"""
Upload / list / download / delete de documentación escaneada por caso.

RBAC: reutiliza get_scoped_case (lawyer solo sus casos). Assistant no borra.
Validación de tipo MIME y tamaño máximo. Binario en volumen Docker, metadata en DB.
"""
import re
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.security import get_current_active_user
from app.models.attachment import Attachment
from app.models.user import User, UserRole
from app.routers.cases import get_scoped_case
from app.schemas.attachment import AttachmentResponse
from app.services import attachment_storage

router = APIRouter(prefix="/cases/{case_id}/attachments", tags=["attachments"])

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._\- ]+")


def _sanitize_filename(name: str) -> str:
    cleaned = _SAFE_FILENAME_RE.sub("_", (name or "").strip())[:200]
    return cleaned or "documento"


@router.get("/", response_model=List[AttachmentResponse])
async def list_attachments(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)
    stmt = (
        select(Attachment)
        .where(Attachment.case_id == case_id)
        .order_by(Attachment.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


@router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    case_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)

    # 1. Validate MIME type
    mime = (file.content_type or "").lower()
    if mime not in settings.allowed_upload_mime:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo no permitido ({mime or 'desconocido'}). "
                   f"Permitidos: PDF, PNG, JPG, WEBP.",
        )

    # 2. Read + enforce size cap
    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el máximo de {settings.MAX_UPLOAD_MB} MB.",
        )
    if not data:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    # 3. Persist to disk + DB
    stored = attachment_storage.save_bytes(data, mime)
    att = Attachment(
        case_id=case_id,
        filename=_sanitize_filename(file.filename),
        stored_filename=stored,
        mime_type=mime,
        size_bytes=len(data),
        uploaded_by_id=current_user.id,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return att


@router.get("/{attachment_id}/download")
async def download_attachment(
    case_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await get_scoped_case(case_id, db, current_user)
    att = await _get_attachment(db, case_id, attachment_id)
    path = attachment_storage.full_path(att.stored_filename)
    return FileResponse(
        path,
        media_type=att.mime_type,
        filename=att.filename,
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_200_OK)
async def delete_attachment(
    case_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=403,
            detail="Los asistentes no tienen autorización para eliminar adjuntos.",
        )
    await get_scoped_case(case_id, db, current_user)
    att = await _get_attachment(db, case_id, attachment_id)
    attachment_storage.delete_file(att.stored_filename)
    await db.delete(att)
    await db.commit()
    return {"detail": "Adjunto eliminado"}


async def _get_attachment(db: AsyncSession, case_id: int, attachment_id: int) -> Attachment:
    stmt = select(Attachment).where(
        Attachment.id == attachment_id, Attachment.case_id == case_id
    )
    att = (await db.execute(stmt)).scalar_one_or_none()
    if not att:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")
    return att
