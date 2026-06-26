"""
Adjuntos: upload con validación de tipo, RBAC, descarga, delete (no assistant),
y el guard multimodal de los providers que no lo soportan.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case, CaseStatus, CaseType
from app.models.client import Client, ClientType
from tests.conftest import login, auth_headers

# PDF mínimo válido (header + EOF). Suficiente para los tests de upload.
MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


@pytest_asyncio.fixture
async def case_for_lawyer(db_session: AsyncSession, lawyer_user, admin_user):
    client = Client(
        first_name="Cliente", last_name="Adjuntos",
        client_type=ClientType.NATURAL, tax_id="20-11111111-1", is_active=True,
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)

    case = Case(
        case_number="EXP-ATT-0001", title="Caso con adjuntos",
        case_type=CaseType.CIVIL, status=CaseStatus.NUEVO,
        client_id=client.id, assigned_lawyer_id=lawyer_user.id, created_by_id=admin_user.id,
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case


@pytest.mark.asyncio
async def test_upload_and_list_pdf(client, lawyer_user, case_for_lawyer):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.post(
        f"/api/cases/{case_for_lawyer.id}/attachments/",
        headers=auth_headers(token),
        files={"file": ("cedula.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "cedula.pdf"
    assert body["mime_type"] == "application/pdf"
    assert body["size_bytes"] == len(MINIMAL_PDF)

    lst = await client.get(
        f"/api/cases/{case_for_lawyer.id}/attachments/", headers=auth_headers(token)
    )
    assert lst.status_code == 200
    assert len(lst.json()) == 1


@pytest.mark.asyncio
async def test_upload_rejects_invalid_type(client, lawyer_user, case_for_lawyer):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    resp = await client.post(
        f"/api/cases/{case_for_lawyer.id}/attachments/",
        headers=auth_headers(token),
        files={"file": ("malicioso.exe", b"MZ\x90\x00", "application/x-msdownload")},
    )
    assert resp.status_code == 415


@pytest.mark.asyncio
async def test_lawyer_cannot_upload_to_other_case(client, other_lawyer_user, case_for_lawyer):
    # case_for_lawyer pertenece a lawyer_user; lawyer2 no debe poder subir
    token = await login(client, "lawyer2@test.com", "LawyerPass123!")
    resp = await client.post(
        f"/api/cases/{case_for_lawyer.id}/attachments/",
        headers=auth_headers(token),
        files={"file": ("x.pdf", MINIMAL_PDF, "application/pdf")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_download_returns_bytes(client, lawyer_user, case_for_lawyer):
    token = await login(client, "lawyer@test.com", "LawyerPass123!")
    up = await client.post(
        f"/api/cases/{case_for_lawyer.id}/attachments/",
        headers=auth_headers(token),
        files={"file": ("doc.pdf", MINIMAL_PDF, "application/pdf")},
    )
    aid = up.json()["id"]
    dl = await client.get(
        f"/api/cases/{case_for_lawyer.id}/attachments/{aid}/download",
        headers=auth_headers(token),
    )
    assert dl.status_code == 200
    assert dl.content == MINIMAL_PDF


@pytest.mark.asyncio
async def test_assistant_cannot_delete_attachment(client, lawyer_user, assistant_user, case_for_lawyer):
    # Lawyer sube
    ltoken = await login(client, "lawyer@test.com", "LawyerPass123!")
    up = await client.post(
        f"/api/cases/{case_for_lawyer.id}/attachments/",
        headers=auth_headers(ltoken),
        files={"file": ("doc.pdf", MINIMAL_PDF, "application/pdf")},
    )
    aid = up.json()["id"]

    # Assistant intenta borrar
    await client.post("/api/auth/logout")
    atoken = await login(client, "assistant@test.com", "AssistPass123!")
    resp = await client.delete(
        f"/api/cases/{case_for_lawyer.id}/attachments/{aid}",
        headers=auth_headers(atoken),
    )
    assert resp.status_code == 403


# ---- Multimodal layer ----

def test_gemini_builds_inline_data_for_attachment():
    from app.services.ai.gemini_provider import GeminiProvider
    from app.services.ai.base import AIMessage, AIAttachment

    provider = GeminiProvider(api_key="dummy", default_model="gemini-2.5-flash")
    msg = AIMessage(
        role="user",
        content="analizá",
        attachments=[AIAttachment(mime_type="application/pdf", data=MINIMAL_PDF, filename="x.pdf")],
    )
    body = provider._build_body(
        [msg], system=None, max_tokens=100, temperature=0.3, model="gemini-2.5-flash"
    )
    parts = body["contents"][0]["parts"]
    # Debe haber un part de texto y uno inline_data
    assert any("text" in p for p in parts)
    inline = [p for p in parts if "inline_data" in p]
    assert len(inline) == 1
    assert inline[0]["inline_data"]["mime_type"] == "application/pdf"
    assert inline[0]["inline_data"]["data"]  # base64 no vacío
    # flash → thinking deshabilitado, y el texto recibe su presupuesto completo
    assert body["generationConfig"]["thinkingConfig"]["thinkingBudget"] == 0
    assert body["generationConfig"]["maxOutputTokens"] == 100


def test_thinking_budget_disabled_on_flash_bounded_on_pro():
    from app.services.ai.gemini_provider import _thinking_budget
    assert _thinking_budget("gemini-2.5-flash") == 0
    assert _thinking_budget("gemini-2.5-flash-lite") == 0
    assert _thinking_budget("gemini-3-flash-preview") == 0
    assert _thinking_budget("gemini-2.5-pro") > 0  # pro no permite deshabilitar


def test_text_only_providers_reject_attachments():
    from app.services.ai.base import (
        AIMessage, AIAttachment, ProviderError, reject_attachments_if_present,
    )
    msgs = [AIMessage(role="user", content="x", attachments=[
        AIAttachment(mime_type="application/pdf", data=b"x", filename="x.pdf")
    ])]
    with pytest.raises(ProviderError):
        reject_attachments_if_present(msgs, "openai")
