from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.interaction import Interaction
from app.models.case import Case
from app.models.user import User, UserRole
from app.schemas.interaction import InteractionCreate, InteractionResponse
from app.middleware.security import get_current_active_user

router = APIRouter(prefix="/interactions", tags=["interactions"])

@router.get("/", response_model=List[InteractionResponse])
async def list_interactions(
    case_id: Optional[int] = None,
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List chronological interactions. Append-only history list.
    Enforces that lawyers can only fetch interactions for cases they own.
    """
    # Verify Lawyer boundaries
    if current_user.role == UserRole.LAWYER and case_id:
        stmt_case = select(Case).where(Case.id == case_id)
        result_case = await db.execute(stmt_case)
        case = result_case.scalar_one_or_none()
        if not case or case.assigned_lawyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes acceso a los registros de este expediente."
            )

    stmt = select(Interaction).options(selectinload(Interaction.user))

    # Apply filters
    if case_id:
        stmt = stmt.where(Interaction.case_id == case_id)
    if client_id:
        stmt = stmt.where(Interaction.client_id == client_id)
        
    # If lawyer fetches general, restrict to their cases/actions
    if current_user.role == UserRole.LAWYER and not case_id:
        # Fetch cases assigned to the lawyer
        stmt_cases_ids = select(Case.id).where(Case.assigned_lawyer_id == current_user.id)
        cases_ids_res = await db.execute(stmt_cases_ids)
        cases_ids = cases_ids_res.scalars().all()
        stmt = stmt.where(
            (Interaction.case_id.in_(cases_ids)) | (Interaction.user_id == current_user.id)
        )

    stmt = stmt.order_by(Interaction.interaction_date.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    payload: InteractionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Record a new append-only interaction.
    No updates or deletes are provided for compliance.
    """
    # Enforce case assignment for Lawyers
    if payload.case_id:
        stmt_case = select(Case).where(Case.id == payload.case_id)
        result_case = await db.execute(stmt_case)
        case = result_case.scalar_one_or_none()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expediente asociado no encontrado"
            )
        if current_user.role == UserRole.LAWYER and case.assigned_lawyer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No posees autorización para agregar interacciones en este expediente."
            )

    new_interaction = Interaction(
        user_id=current_user.id,
        **payload.model_dump()
    )
    db.add(new_interaction)
    await db.commit()
    
    # Reload with user relationship loaded
    stmt_reload = (
        select(Interaction)
        .options(selectinload(Interaction.user))
        .where(Interaction.id == new_interaction.id)
    )
    res_reload = await db.execute(stmt_reload)
    return res_reload.scalar_one()
