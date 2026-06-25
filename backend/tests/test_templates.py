"""
Templates CRUD: admin-only writes, catalog is readable by everyone,
built-in keys cannot be shadowed.
"""
import pytest
from tests.conftest import login, auth_headers


VALID_PAYLOAD = {
    "key": "demanda_laboral",
    "name": "Demanda laboral",
    "description": "Demanda por despido sin causa",
    "instruction": "Redactá una demanda laboral contra el empleador. Estructura clásica: SUMA, hechos, derecho, petitorio.",
    "variables": [
        {"key": "monto", "label": "Monto reclamado", "type": "money", "required": True, "placeholder": "1000000", "help": ""},
        {"key": "trabajador", "label": "Nombre del trabajador", "type": "text", "required": True, "placeholder": "", "help": ""},
    ],
    "default_title": "Demanda laboral",
    "is_active": True,
}


@pytest.mark.asyncio
async def test_admin_can_create_custom_template(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    resp = await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["key"] == "demanda_laboral"
    assert len(body["variables"]) == 2


@pytest.mark.asyncio
async def test_lawyer_cannot_create_template(client, lawyer_user):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_shadow_builtin_key(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    shadow = {**VALID_PAYLOAD, "key": "carta_documento"}
    resp = await client.post("/api/templates/", json=shadow, headers=auth_headers(token))
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_duplicate_custom_key_rejected(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    first = await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))
    assert first.status_code == 201
    again = await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_catalog_lists_builtin_and_custom_with_origin(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))

    resp = await client.get("/api/templates/catalog", headers=auth_headers(token))
    assert resp.status_code == 200
    items = resp.json()
    keys_origin = {(i["key"], i["is_builtin"]) for i in items}
    assert ("carta_documento", True) in keys_origin
    assert ("demanda_laboral", False) in keys_origin


@pytest.mark.asyncio
async def test_lawyer_can_read_catalog(client, lawyer_user, admin_user):
    # Admin seeds one
    admin_token = await login(client, "admin@test.com", "AdminPass123!")
    await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(admin_token))

    # Lawyer reads (no cookie issue: log in fresh)
    await client.post("/api/auth/logout")
    lawyer_token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.get("/api/templates/catalog", headers=auth_headers(lawyer_token))
    assert resp.status_code == 200
    assert any(i["key"] == "demanda_laboral" for i in resp.json())


@pytest.mark.asyncio
async def test_admin_can_update_and_delete(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    create_resp = await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))
    tid = create_resp.json()["id"]

    upd = await client.put(
        f"/api/templates/{tid}",
        json={"name": "Demanda laboral v2"},
        headers=auth_headers(token),
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Demanda laboral v2"

    deleted = await client.delete(f"/api/templates/{tid}", headers=auth_headers(token))
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_ai_templates_endpoint_includes_custom(client, admin_user):
    token = await login(client, "admin@test.com", "AdminPass123!")
    await client.post("/api/templates/", json=VALID_PAYLOAD, headers=auth_headers(token))

    resp = await client.get("/api/ai/templates", headers=auth_headers(token))
    assert resp.status_code == 200
    keys = {t["key"] for t in resp.json()}
    assert "carta_documento" in keys
    assert "demanda_laboral" in keys
