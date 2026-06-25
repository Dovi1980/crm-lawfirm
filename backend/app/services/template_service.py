"""
Template lookup that merges built-in (code-defined) + custom (DB-persisted).

Built-in templates always win on key collision — admins can extend the
catalog but cannot shadow or break a system template.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_template import CustomTemplate
from app.services.document_templates import (
    DocumentTemplate,
    TemplateVariable,
    get_template as get_builtin_template,
    list_templates as list_builtin_templates,
)


def _row_to_template(row: CustomTemplate) -> DocumentTemplate:
    variables = [
        TemplateVariable(
            key=v.get("key", ""),
            label=v.get("label", ""),
            type=v.get("type", "text"),
            required=bool(v.get("required", True)),
            placeholder=v.get("placeholder", ""),
            help=v.get("help", ""),
        )
        for v in (row.variables or [])
    ]
    return DocumentTemplate(
        key=row.key,
        name=row.name,
        description=row.description or "",
        instruction=row.instruction,
        variables=variables,
        default_title=row.default_title or row.name,
    )


async def list_all_templates(db: AsyncSession) -> list[DocumentTemplate]:
    """Built-in catalog + active custom templates (built-in first)."""
    built_in = list_builtin_templates()
    built_in_keys = {t.key for t in built_in}

    stmt = (
        select(CustomTemplate)
        .where(CustomTemplate.is_active == True)  # noqa: E712
        .order_by(CustomTemplate.created_at.desc())
    )
    custom_rows = list((await db.execute(stmt)).scalars().all())
    custom = [_row_to_template(r) for r in custom_rows if r.key not in built_in_keys]
    return built_in + custom


async def get_template_resolved(db: AsyncSession, key: str) -> DocumentTemplate | None:
    """Built-in takes precedence; falls back to DB."""
    built = get_builtin_template(key)
    if built:
        return built
    stmt = select(CustomTemplate).where(
        CustomTemplate.key == key,
        CustomTemplate.is_active == True,  # noqa: E712
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    return _row_to_template(row) if row else None


def is_builtin(key: str) -> bool:
    return get_builtin_template(key) is not None
