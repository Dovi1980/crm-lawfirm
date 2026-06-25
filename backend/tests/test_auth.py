"""
Auth flow tests:
- Login OK / bad password / inactive user
- Refresh token via HttpOnly cookie (no body)
- Token rotation: old refresh token invalid after refresh
- Logout revokes the token
- Refresh body NEVER contains refresh_token (must live in cookie)
"""
import pytest
from tests.conftest import login, auth_headers


@pytest.mark.asyncio
async def test_login_success_sets_httponly_cookie(client, lawyer_user):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "lawyer@test.com", "password": "LawyerPass123!"},
    )
    assert resp.status_code == 200
    body = resp.json()

    # Body must NOT carry the refresh token
    assert "refresh_token" not in body
    assert "access_token" in body
    assert body["role"] == "lawyer"

    # Cookie must be set, HttpOnly
    set_cookie = resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/api/auth" in set_cookie


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client, lawyer_user):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "lawyer@test.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client):
    resp = await client.post(
        "/api/auth/login",
        json={"email": "nobody@test.com", "password": "whatever"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_invalidates_old_one(client, lawyer_user):
    # Initial login → cookie #1
    await login(client, "lawyer@test.com", "LawyerPass123!")
    old_cookie = client.cookies.get("refresh_token")
    assert old_cookie is not None

    # Refresh → cookie #2 (must differ, body must not echo it)
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "refresh_token" not in refresh_resp.json()

    new_cookie = client.cookies.get("refresh_token")
    assert new_cookie is not None
    assert new_cookie != old_cookie

    # Trying to use the OLD (rotated-out) cookie must now fail. Force-override
    # the client jar so we send the old value instead of the rotated one.
    client.cookies.clear()
    client.cookies.set("refresh_token", old_cookie)
    resp_old = await client.post("/api/auth/refresh")
    assert resp_old.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(client, lawyer_user):
    resp = await client.post("/api/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client, lawyer_user):
    await login(client, "lawyer@test.com", "LawyerPass123!")
    cookie_value = client.cookies.get("refresh_token")

    logout_resp = await client.post("/api/auth/logout")
    assert logout_resp.status_code == 200

    # Re-attach the revoked cookie manually; it should no longer refresh.
    client.cookies.set("refresh_token", cookie_value)
    refresh_after = await client.post("/api/auth/refresh")
    assert refresh_after.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_requires_access_token(client, lawyer_user):
    # Without bearer header → 401
    resp = await client.get("/api/cases/")
    assert resp.status_code == 401

    # With valid token → 200
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp_ok = await client.get("/api/cases/", headers=auth_headers(token))
    assert resp_ok.status_code == 200
