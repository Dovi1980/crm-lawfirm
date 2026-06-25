"""
CRUD for AI-generated documents saved against a case.

RBAC: re-uses `get_scoped_case` so a lawyer only sees / writes / deletes
documents on cases they own. Assistant is read-only (no delete).
"""
import re
from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.security import get_current_active_user
from app.models.document import Document
from app.models.user import User, UserRole
from app.routers.cases import get_scoped_case
from app.schemas.document import (
    DocumentCreate,
    DocumentListItem,
    DocumentResponse,
)
from app.services.document_export import to_docx, to_pdf

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


@router.get("/", response_model=List[DocumentListItem])
async def list_case_documents(
    case_id: int,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)
    stmt = select(Document).where(Document.case_id == case_id)
    if not include_archived:
        stmt = stmt.where(Document.is_archived == False)  # noqa: E712
    stmt = stmt.order_by(Document.created_at.desc())
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def save_case_document(
    case_id: int,
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)
    doc = Document(
        case_id=case_id,
        template_key=payload.template_key,
        title=payload.title,
        content=payload.content,
        generated_by_id=current_user.id,
        is_archived=False,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_case_document(
    case_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)
    stmt = select(Document).where(Document.id == document_id, Document.case_id == case_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc


_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_\-]+")


def _safe_filename_stem(text: str) -> str:
    stem = _SAFE_FILENAME_RE.sub("_", text.strip())[:80].strip("_")
    return stem or "documento"


@router.get("/{document_id}/export")
async def export_case_document(
    case_id: int,
    document_id: int,
    format: Literal["docx", "pdf"] = "docx",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Render the document as DOCX or PDF and return it as a download."""
    await get_scoped_case(case_id, db, current_user)
    stmt = select(Document).where(Document.id == document_id, Document.case_id == case_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if format == "docx":
        payload = to_docx(doc.content, doc.title)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        payload = to_pdf(doc.content, doc.title)
        media_type = "application/pdf"

    filename = f"{_safe_filename_stem(doc.title)}.{format}"
    return Response(
        content=payload,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def archive_case_document(
    case_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Soft delete — the row stays for audit trail."""
    if current_user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=403,
            detail="Los asistentes no tienen autorización para eliminar documentos.",
        )
    await get_scoped_case(case_id, db, current_user)
    stmt = select(Document).where(Document.id == document_id, Document.case_id == case_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    doc.is_archived = True
    await db.commit()
    return {"detail": "Documento archivado"}
