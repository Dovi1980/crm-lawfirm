"""
Admin CRUD for custom document templates.

Only ADMINs can create / edit / delete. The catalog endpoint is readable by
any active user so the documents UI in the case page can preview the full
list with origin labels.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.security import RoleChecker, get_current_active_user
from app.models.custom_template import CustomTemplate
from app.models.user import User, UserRole
from app.schemas.custom_template import (
    CustomTemplateCreate,
    CustomTemplateResponse,
    CustomTemplateUpdate,
    TemplateCatalogItem,
)
from app.services.document_templates import list_templates as list_builtin_templates

router = APIRouter(prefix="/templates", tags=["templates"])
require_admin = RoleChecker([UserRole.ADMIN])


@router.get("/catalog", response_model=List[TemplateCatalogItem])
async def catalog(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Unified listing for the admin panel: built-in + custom, with origin."""
    built_in = list_builtin_templates()
    built_in_keys = {t.key for t in built_in}
    items: list[TemplateCatalogItem] = []
    for t in built_in:
        items.append(TemplateCatalogItem(
            key=t.key,
            name=t.name,
            description=t.description,
            default_title=t.default_title,
            variable_count=len(t.variables),
            is_builtin=True,
            is_active=True,
        ))

    stmt = select(CustomTemplate).order_by(CustomTemplate.created_at.desc())
    rows = list((await db.execute(stmt)).scalars().all())
    for row in rows:
        if row.key in built_in_keys:
            continue  # built-in always wins; hide shadow
        items.append(TemplateCatalogItem(
            key=row.key,
            name=row.name,
            description=row.description or "",
            default_title=row.default_title or row.name,
            variable_count=len(row.variables or []),
            is_builtin=False,
            is_active=row.is_active,
            custom_id=row.id,
        ))
    return items


@router.post(
    "/",
    response_model=CustomTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_custom_template(
    payload: CustomTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Disallow keys that already exist either built-in or custom.
    if any(t.key == payload.key for t in list_builtin_templates()):
        raise HTTPException(
            status_code=409,
            detail="La clave coincide con un template de sistema. Usá otra.",
        )
    stmt = select(CustomTemplate).where(CustomTemplate.key == payload.key)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un template con esa clave.")

    row = CustomTemplate(
        key=payload.key,
        name=payload.name.strip(),
        description=payload.description.strip(),
        instruction=payload.instruction.strip(),
        variables=[v.model_dump() for v in payload.variables],
        default_title=(payload.default_title or payload.name).strip(),
        is_active=payload.is_active,
        created_by_id=current_user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.get(
    "/{template_id}",
    response_model=CustomTemplateResponse,
    dependencies=[Depends(require_admin)],
)
async def get_custom_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomTemplate).where(CustomTemplate.id == template_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    return row


@router.put(
    "/{template_id}",
    response_model=CustomTemplateResponse,
    dependencies=[Depends(require_admin)],
)
async def update_custom_template(
    template_id: int,
    payload: CustomTemplateUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomTemplate).where(CustomTemplate.id == template_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Template no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "variables" in data and data["variables"] is not None:
        data["variables"] = [v if isinstance(v, dict) else v.model_dump() for v in data["variables"]]
    for k, v in data.items():
        setattr(row, k, v.strip() if isinstance(v, str) else v)

    await db.commit()
    await db.refresh(row)
    return row


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin)],
)
async def delete_custom_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CustomTemplate).where(CustomTemplate.id == template_id)
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    await db.delete(row)
    await db.commit()
    return {"detail": "Template eliminado"}
