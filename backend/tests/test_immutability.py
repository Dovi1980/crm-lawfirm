"""
Immutability tests: the /interactions resource is append-only by contract.

Verifies that NO route exists in the application for:
- PUT /api/interactions/{id}
- PATCH /api/interactions/{id}
- DELETE /api/interactions/{id}

Stronger than a 405 check at runtime — we read the FastAPI route table directly.
"""
import pytest
from app.main import app


def _interaction_routes_by_method(method: str) -> list[str]:
    """
    Return paths under /interactions that expose the given HTTP method.

    Reads the OpenAPI schema instead of walking `app.routes` directly: newer
    FastAPI (>=0.138) no longer flattens included routers into `app.routes`
    (they become opaque `_IncludedRouter` objects), so the schema is the
    version-stable source of truth for the declared route table.
    """
    method = method.lower()
    schema = app.openapi()
    matches = []
    for path, operations in schema.get("paths", {}).items():
        if "/interactions" in path and method in operations:
            matches.append(path)
    return matches


def test_no_put_route_on_interactions():
    assert _interaction_routes_by_method("PUT") == [], (
        "Interactions must be append-only; PUT endpoint was registered."
    )


def test_no_patch_route_on_interactions():
    assert _interaction_routes_by_method("PATCH") == [], (
        "Interactions must be append-only; PATCH endpoint was registered."
    )


def test_no_delete_route_on_interactions():
    assert _interaction_routes_by_method("DELETE") == [], (
        "Interactions must be append-only; DELETE endpoint was registered."
    )


def test_get_and_post_routes_do_exist():
    """Sanity: ensure the append/list routes ARE present."""
    assert _interaction_routes_by_method("GET"), "Missing GET /api/interactions"
    assert _interaction_routes_by_method("POST"), "Missing POST /api/interactions"


@pytest.mark.asyncio
async def test_put_request_returns_405(client, lawyer_user):
    """Belt-and-suspenders runtime check: an actual PUT must be rejected by FastAPI."""
    from tests.conftest import login, auth_headers
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.put(
        "/api/interactions/1",
        headers=auth_headers(token),
        json={"description": "no debería poder editarse"},
    )
    assert resp.status_code in (404, 405)


@pytest.mark.asyncio
async def test_delete_request_returns_405(client, lawyer_user):
    from tests.conftest import login, auth_headers
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.delete("/api/interactions/1", headers=auth_headers(token))
    assert resp.status_code in (404, 405)
