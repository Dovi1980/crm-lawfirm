"""
RBAC tests on cases:
- LAWYER only sees cases assigned to them in the list endpoint
- LAWYER cannot fetch another lawyer's case by ID
- ASSISTANT cannot delete a case
- ADMIN can delete any case
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case, CaseStatus, CaseType
from app.models.client import Client, ClientType
from tests.conftest import login, auth_headers


@pytest_asyncio.fixture
async def seed_client(db_session: AsyncSession):
    client_obj = Client(
        first_name="Cliente",
        last_name="Demo",
        client_type=ClientType.NATURAL,
        tax_id="20-12345678-9",
        is_active=True,
    )
    db_session.add(client_obj)
    await db_session.commit()
    await db_session.refresh(client_obj)
    return client_obj


@pytest_asyncio.fixture
async def lawyer1_case(db_session, lawyer_user, seed_client, admin_user):
    case = Case(
        case_number="EXP-2026-0001",
        title="Caso de lawyer1",
        case_type=CaseType.CIVIL,
        status=CaseStatus.NUEVO,
        client_id=seed_client.id,
        assigned_lawyer_id=lawyer_user.id,
        created_by_id=admin_user.id,
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case


@pytest_asyncio.fixture
async def lawyer2_case(db_session, other_lawyer_user, seed_client, admin_user):
    case = Case(
        case_number="EXP-2026-0002",
        title="Caso de lawyer2",
        case_type=CaseType.LABORAL,
        status=CaseStatus.NUEVO,
        client_id=seed_client.id,
        assigned_lawyer_id=other_lawyer_user.id,
        created_by_id=admin_user.id,
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case


@pytest.mark.asyncio
async def test_lawyer_sees_only_assigned_cases(client, lawyer_user, other_lawyer_user, lawyer1_case, lawyer2_case):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.get("/api/cases/", headers=auth_headers(token))
    assert resp.status_code == 200
    cases = resp.json()
    case_numbers = {c["case_number"] for c in cases}
    assert "EXP-2026-0001" in case_numbers
    assert "EXP-2026-0002" not in case_numbers


@pytest.mark.asyncio
async def test_lawyer_cannot_read_other_lawyer_case_by_id(client, lawyer_user, lawyer2_case):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.get(f"/api/cases/{lawyer2_case.id}", headers=auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_sees_all_cases(client, admin_user, lawyer1_case, lawyer2_case):
    token = await login(client, "admin@test.com", "AdminPass123!")
    resp = await client.get("/api/cases/", headers=auth_headers(token))
    assert resp.status_code == 200
    case_numbers = {c["case_number"] for c in resp.json()}
    assert "EXP-2026-0001" in case_numbers
    assert "EXP-2026-0002" in case_numbers


@pytest.mark.asyncio
async def test_assistant_cannot_delete_case(client, assistant_user, lawyer1_case):
    token = await login(client, "assistant@test.com", "AssistPass123!")
    resp = await client.delete(f"/api/cases/{lawyer1_case.id}", headers=auth_headers(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_delete_case(client, admin_user, lawyer1_case):
    token = await login(client, "admin@test.com", "AdminPass123!")
    resp = await client.delete(f"/api/cases/{lawyer1_case.id}", headers=auth_headers(token))
    assert resp.status_code == 200
