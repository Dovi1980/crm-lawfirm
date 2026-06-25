"""
AI endpoints: case summary, case-aware chat, global assistant.

Streaming endpoints use Server-Sent Events. Each text chunk is wrapped as
`data: {"text": "..."}\n\n`; the stream finishes with `data: [DONE]\n\n`.
Errors during streaming arrive as `event: error\ndata: {"detail": "..."}\n\n`.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.security import get_current_active_user
from app.models.user import User
from app.routers.cases import get_scoped_case
from app.schemas.ai import ChatRequest, SummaryResponse
from app.schemas.document import DocumentGenerateRequest, TemplateSchema
from app.services.ai import AIMessage, ProviderError
from app.services.ai_service import (
    stream_case_chat,
    stream_document_draft,
    stream_general_assistant,
    summarize_case,
)
from app.services.template_service import get_template_resolved, list_all_templates

logger = structlog.get_logger()
router = APIRouter(prefix="/ai", tags=["ai"])


def _to_ai_messages(payload: ChatRequest) -> list[AIMessage]:
    return [AIMessage(role=m.role, content=m.content) for m in payload.messages]


async def _wrap_sse(generator: AsyncIterator[str]) -> AsyncIterator[bytes]:
    """Convert a text-chunk generator into a properly-framed SSE stream."""
    try:
        async for chunk in generator:
            if not chunk:
                continue
            payload = json.dumps({"text": chunk}, ensure_ascii=False)
            yield f"data: {payload}\n\n".encode("utf-8")
    except ProviderError as e:
        logger.warning("ai.provider_error", error=str(e))
        err = json.dumps({"detail": str(e)}, ensure_ascii=False)
        yield f"event: error\ndata: {err}\n\n".encode("utf-8")
    except Exception as e:
        logger.exception("ai.unexpected_error")
        err = json.dumps({"detail": "Error interno generando respuesta"}, ensure_ascii=False)
        yield f"event: error\ndata: {err}\n\n".encode("utf-8")
    finally:
        yield b"data: [DONE]\n\n"


@router.post("/cases/{case_id}/summary", response_model=SummaryResponse)
async def case_summary(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate a concise summary of the case. RBAC: scoped to assigned lawyer."""
    # Reuse RBAC check from cases router.
    await get_scoped_case(case_id, db, current_user)
    try:
        text = await summarize_case(db, case_id)
    except ProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return SummaryResponse(summary=text)


@router.post("/cases/{case_id}/chat")
async def case_chat(
    case_id: int,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Streaming chat anchored to a case."""
    await get_scoped_case(case_id, db, current_user)
    history = _to_ai_messages(payload)
    generator = stream_case_chat(db, case_id, history)
    return StreamingResponse(
        _wrap_sse(generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering for SSE
        },
    )


@router.get("/templates", response_model=list[TemplateSchema])
async def list_document_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Catalog of legal document templates (built-in + admin custom)."""
    return [
        TemplateSchema(
            key=t.key,
            name=t.name,
            description=t.description,
            default_title=t.default_title,
            variables=[v.__dict__ for v in t.variables],
        )
        for t in await list_all_templates(db)
    ]


@router.post("/cases/{case_id}/document/generate")
async def generate_document_draft(
    case_id: int,
    payload: DocumentGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream the AI-generated draft of a legal document."""
    await get_scoped_case(case_id, db, current_user)
    template = await get_template_resolved(db, payload.template_key)
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    generator = stream_document_draft(db, case_id, template, payload.variables)
    return StreamingResponse(
        _wrap_sse(generator),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/assistant")
async def assistant(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Streaming global assistant — no case context."""
    history = _to_ai_messages(payload)
    generator = stream_general_assistant(history, current_user)
    return StreamingResponse(
        _wrap_sse(generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
