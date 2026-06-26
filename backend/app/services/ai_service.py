"""
Domain-level AI orchestration.

Builds case-aware system prompts from ORM data and delegates the actual
LLM call to whatever provider is configured (see app.services.ai.factory).
The router layer wraps the streaming generators in Server-Sent Events.
"""
from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.case import Case
from app.models.interaction import Interaction
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.ai import AIMessage, ProviderError, get_ai_provider
from app.services.ai.base import AIAttachment
from app.services.document_templates import (
    DocumentTemplate,
    render_user_inputs_block,
)


_BASE_SYSTEM_PROMPT = (
    "Eres un asistente jurídico para un estudio de abogados en Argentina. "
    "Respondes en español rioplatense, con tono profesional y conciso. "
    "Te basas únicamente en la información del expediente provista; cuando "
    "no tengas datos suficientes, lo decís explícitamente en lugar de inventar. "
    "No inventás citas legales, jurisprudencia ni nombres de partes. "
    "Cuando sugieras pasos procesales, aclará que son sugerencias y que el "
    "criterio final es del abogado responsable."
)


def _ensure_ai_enabled() -> None:
    if not settings.AI_ENABLED:
        raise ProviderError("La funcionalidad de IA está deshabilitada en este despliegue.")


async def _load_case_context(db: AsyncSession, case_id: int, max_interactions: int = 30) -> str:
    """Return a markdown-ish dossier the model can read."""
    stmt_case = (
        select(Case)
        .options(selectinload(Case.client), selectinload(Case.assigned_lawyer))
        .where(Case.id == case_id)
    )
    case = (await db.execute(stmt_case)).scalar_one_or_none()
    if not case:
        raise ProviderError(f"Expediente {case_id} no encontrado")

    lines: list[str] = []
    lines.append(f"# Expediente {case.case_number}: {case.title}")
    lines.append(f"- Tipo: {case.case_type.value}")
    lines.append(f"- Estado: {case.status.value}")
    lines.append(f"- Inicio: {case.start_date.isoformat()}")
    if case.estimated_close_date:
        lines.append(f"- Cierre estimado: {case.estimated_close_date.isoformat()}")
    if case.client:
        lines.append(f"- Cliente: {case.client.full_name} ({case.client.client_type.value})")
    if case.assigned_lawyer:
        lines.append(f"- Abogado asignado: {case.assigned_lawyer.full_name}")
    if case.agreed_fees:
        lines.append(f"- Honorarios pactados: {case.agreed_fees}")
    if case.description:
        lines.append("")
        lines.append("## Descripción")
        lines.append(case.description.strip())
    if case.internal_notes:
        lines.append("")
        lines.append("## Notas internas")
        lines.append(case.internal_notes.strip())

    # Recent interactions (chronological, oldest first for narrative flow)
    stmt_inter = (
        select(Interaction)
        .where(Interaction.case_id == case_id)
        .order_by(Interaction.interaction_date.desc())
        .limit(max_interactions)
    )
    interactions = list((await db.execute(stmt_inter)).scalars().all())
    interactions.reverse()  # oldest first

    if interactions:
        lines.append("")
        lines.append(f"## Últimas {len(interactions)} interacciones (cronológico)")
        for it in interactions:
            date_str = it.interaction_date.strftime("%Y-%m-%d %H:%M")
            duration = f" ({it.duration_minutes}m)" if it.duration_minutes else ""
            desc = it.description.strip().replace("\n", " ")
            lines.append(f"- [{date_str}] {it.interaction_type.value}{duration}: {desc}")

    # Open tasks
    stmt_tasks = (
        select(Task)
        .where(Task.case_id == case_id)
        .where(Task.status.in_([TaskStatus.PENDIENTE, TaskStatus.EN_PROGRESO]))
        .order_by(Task.due_date.asc())
    )
    tasks = list((await db.execute(stmt_tasks)).scalars().all())
    if tasks:
        lines.append("")
        lines.append("## Tareas abiertas")
        for t in tasks:
            lines.append(
                f"- [{t.priority.value}] {t.title} — vence {t.due_date.isoformat()} "
                f"({t.status.value})"
            )

    return "\n".join(lines)


async def summarize_case(db: AsyncSession, case_id: int) -> str:
    """Produce a brief summary of the case state. Used by the 'Resumir' button."""
    _ensure_ai_enabled()
    dossier = await _load_case_context(db, case_id)
    provider = get_ai_provider()

    system = (
        _BASE_SYSTEM_PROMPT
        + "\n\nTu tarea: generar un resumen ejecutivo del expediente que sigue, "
        "en no más de 8 viñetas. Estructura: situación actual, hechos clave, "
        "próximos pasos sugeridos. No repitas literalmente el dossier."
    )
    return await provider.complete(
        messages=[AIMessage(role="user", content=dossier)],
        system=system,
        max_tokens=1024,
        temperature=0.3,
    )


async def stream_case_chat(
    db: AsyncSession,
    case_id: int,
    history: list[AIMessage],
) -> AsyncIterator[str]:
    """Chat tied to a specific case — case data injected as system context."""
    _ensure_ai_enabled()
    dossier = await _load_case_context(db, case_id)
    provider = get_ai_provider()

    system = (
        _BASE_SYSTEM_PROMPT
        + "\n\nEstás conversando con el abogado a cargo del siguiente expediente. "
        "Responde basándote en este dossier:\n\n"
        + dossier
    )
    async for chunk in provider.stream(
        messages=history,
        system=system,
        max_tokens=4096,
        temperature=0.5,
    ):
        yield chunk


async def stream_document_draft(
    db: AsyncSession,
    case_id: int,
    template: DocumentTemplate,
    variables: dict[str, str],
) -> AsyncIterator[str]:
    """
    Stream the AI-generated draft of a legal document.

    The model receives: case dossier + template instruction + user-filled variables.
    The deep model (settings.AI_MODEL_DEEP) is used when configured — drafting is
    where the cost/quality tradeoff favours a stronger model.
    """
    _ensure_ai_enabled()
    dossier = await _load_case_context(db, case_id)
    provider = get_ai_provider()
    user_block = render_user_inputs_block(template, variables)

    system = (
        _BASE_SYSTEM_PROMPT
        + "\n\nTAREA: redactar el documento solicitado en formato Markdown plano. "
        "Sin preámbulos del tipo 'Aquí está...'; comenzá directamente con el "
        "encabezado del documento. No incluyas el dossier en la respuesta — "
        "es solo contexto para vos.\n\n"
        + template.instruction
        + "\n\n"
        + "---\n\n"
        + dossier
        + "\n\n---\n\n"
        + user_block
    )

    model = settings.AI_MODEL_DEEP or None  # None → provider default
    async for chunk in provider.stream(
        messages=[AIMessage(role="user", content="Generá el documento ahora.")],
        system=system,
        model=model,
        max_tokens=4096,
        temperature=0.4,
    ):
        yield chunk


async def stream_analyze_attachment(
    case_id: int,
    file_bytes: bytes,
    mime_type: str,
    filename: str,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """
    Lee un documento escaneado (PDF/imagen) con un modelo multimodal y produce:
    un análisis breve + una redacción lista para cargar como gestión.

    Requiere un proveedor con soporte multimodal (Gemini). Otros lanzan ProviderError.
    """
    _ensure_ai_enabled()
    dossier = await _load_case_context(db, case_id)
    provider = get_ai_provider()

    system = (
        _BASE_SYSTEM_PROMPT
        + "\n\nTAREA: analizar el documento adjunto (puede ser una notificación, "
        "demanda, cédula, oficio, contrato, comprobante u otro). Devolvé la respuesta "
        "en Markdown con exactamente estas dos secciones:\n\n"
        "## Resumen\n"
        "Qué tipo de documento es, partes involucradas, fechas y plazos relevantes, "
        "y qué acción procesal sugiere (marcada como sugerencia).\n\n"
        "## Texto para gestión\n"
        "Una redacción breve (2-4 oraciones), en tercera persona y tono de registro "
        "de expediente, lista para cargarse como gestión en el historial. Ejemplo: "
        "'Se recibió cédula de notificación de... con fecha... que otorga plazo de... "
        "para...'.\n\n"
        "Si el documento es ilegible o no podés leerlo, decilo explícitamente en lugar "
        "de inventar contenido.\n\n"
        "Contexto del expediente al que pertenece:\n\n"
        + dossier
    )

    user_msg = AIMessage(
        role="user",
        content="Analizá este documento del expediente.",
        attachments=[AIAttachment(mime_type=mime_type, data=file_bytes, filename=filename)],
    )

    async for chunk in provider.stream(
        messages=[user_msg],
        system=system,
        max_tokens=4096,
        temperature=0.3,
    ):
        yield chunk


async def stream_general_assistant(
    history: list[AIMessage],
    user: User,
) -> AsyncIterator[str]:
    """Global floating assistant — no specific case context."""
    _ensure_ai_enabled()
    provider = get_ai_provider()

    system = (
        _BASE_SYSTEM_PROMPT
        + f"\n\nEstás hablando con {user.full_name} (rol: {user.role.value}). "
        "Como no hay un expediente en contexto, ayudás con tareas generales del estudio: "
        "redacción de mensajes, dudas procesales generales, organización de agenda, "
        "explicaciones de instituciones jurídicas argentinas."
    )
    async for chunk in provider.stream(
        messages=history,
        system=system,
        max_tokens=4096,
        temperature=0.6,
    ):
        yield chunk
