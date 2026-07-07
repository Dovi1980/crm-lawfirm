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


@pytest.mark.asyncio
async def test_deleting_case_archives_and_preserves_interactions(client, db_session, admin_user):
    """
    Borrar un caso NO debe destruir sus interacciones (append-only por ley).
    El endpoint DELETE hace soft-delete (archiva) y el historial se conserva.
    """
    from sqlalchemy import select, func
    from app.models.client import Client, ClientType
    from app.models.case import Case, CaseStatus, CaseType
    from app.models.interaction import Interaction, InteractionType
    from tests.conftest import login, auth_headers

    cli = Client(first_name="C", last_name="D", client_type=ClientType.NATURAL, tax_id="20-9-9", is_active=True)
    db_session.add(cli)
    await db_session.commit(); await db_session.refresh(cli)

    case = Case(
        case_number="EXP-DEL-1", title="Para archivar", case_type=CaseType.CIVIL,
        status=CaseStatus.NUEVO, client_id=cli.id, assigned_lawyer_id=admin_user.id,
        created_by_id=admin_user.id,
    )
    db_session.add(case)
    await db_session.commit(); await db_session.refresh(case)

    inter = Interaction(
        interaction_type=InteractionType.ESCRITO, description="gestión importante",
        user_id=admin_user.id, case_id=case.id, client_id=cli.id, duration_minutes=10,
    )
    db_session.add(inter)
    await db_session.commit()

    token = await login(client, "admin@test.com", "AdminPass123!")
    resp = await client.delete(f"/api/cases/{case.id}", headers=auth_headers(token))
    assert resp.status_code == 200

    # El caso sigue existiendo, archivado (refresh awaitea la IO async correctamente)
    await db_session.refresh(case)
    assert case.status == CaseStatus.ARCHIVADO
    # La interacción NO fue borrada
    count = (await db_session.execute(
        select(func.count(Interaction.id)).where(Interaction.case_id == case.id)
    )).scalar()
    assert count == 1
