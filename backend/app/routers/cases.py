from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.case import Case, CaseStatus, CaseType
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.middleware.security import get_current_active_user

router = APIRouter(prefix="/cases", tags=["cases"])

async def get_scoped_case(case_id: int, db: AsyncSession, user: User) -> Case:
    """
    Helper function to query a case and enforce role-based access.
    Lawyers can only view/modify their assigned cases.
    """
    stmt = select(Case).where(Case.id == case_id)
    
    # Eager load relationships for frontend detail representation
    stmt = stmt.options(
        selectinload(Case.client),
        selectinload(Case.assigned_lawyer)
    )
    
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expediente no encontrado"
        )
        
    # Enforce Lawyer security isolation
    if user.role == UserRole.LAWYER and case.assigned_lawyer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No posees autorización para ver o modificar este expediente."
        )
        
    return case


@router.get("/", response_model=List[CaseResponse])
async def list_cases(
    status: Optional[CaseStatus] = None,
    case_type: Optional[CaseType] = None,
    assigned_lawyer_id: Optional[int] = None,
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List cases with optional filters.
    Lawyers are automatically limited to their assigned cases.
    """
    stmt = select(Case).options(
        selectinload(Case.client),
        selectinload(Case.assigned_lawyer)
    )

    # 1. Enforce Lawyer isolation
    if current_user.role == UserRole.LAWYER:
        stmt = stmt.where(Case.assigned_lawyer_id == current_user.id)
    elif assigned_lawyer_id:
        # Admins or assistants can filter by lawyer
        stmt = stmt.where(Case.assigned_lawyer_id == assigned_lawyer_id)

    # 2. Apply general filters
    if status:
        stmt = stmt.where(Case.status == status)
    if case_type:
        stmt = stmt.where(Case.case_type == case_type)
    if client_id:
        stmt = stmt.where(Case.client_id == client_id)

    stmt = stmt.order_by(Case.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new Case (Expediente).
    Auto-generates case_number: EXP-YYYY-NNNN.
    """
    year = datetime.now().year

    # Auto-number sequence generator: count cases in current calendar year
    stmt_count = (
        select(func.count(Case.id))
        .where(func.extract('year', Case.created_at) == year)
    )
    result_count = await db.execute(stmt_count)
    year_cases_count = result_count.scalar() or 0
    
    # Generate number: e.g. EXP-2026-0001
    sequence = year_cases_count + 1
    case_number = f"EXP-{year}-{sequence:04d}"

    # Verify that the generated number is unique (safety fallback)
    stmt_check = select(Case).where(Case.case_number == case_number)
    res_check = await db.execute(stmt_check)
    if res_check.scalar_one_or_none():
        # Incremental backup in case of collision
        sequence += 1
        case_number = f"EXP-{year}-{sequence:04d}"

    new_case = Case(
        case_number=case_number,
        created_by_id=current_user.id,
        **payload.model_dump()
    )

    db.add(new_case)
    await db.commit()
    
    # Reload with relationships
    return await get_scoped_case(new_case.id, db, current_user)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case_details(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed case metrics. Enforces lawyer visibility scopes.
    """
    return await get_scoped_case(case_id, db, current_user)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    payload: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Modify an existing case. Enforces lawyer ownership bounds.
    """
    case = await get_scoped_case(case_id, db, current_user)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)

    db.add(case)
    await db.commit()
    await db.refresh(case)
    return await get_scoped_case(case_id, db, current_user)


@router.delete("/{case_id}", status_code=status.HTTP_200_OK)
async def delete_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Archive a case (soft delete). Assistants are barred; lawyers only their own.

    We do NOT hard-delete: a hard delete would cascade-remove the case's
    interactions, which are append-only by legal requirement. Instead the case
    is moved to ARCHIVADO, preserving the full history.
    """
    if current_user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los asistentes no tienen autorización para archivar expedientes."
        )

    case = await get_scoped_case(case_id, db, current_user)
    case.status = CaseStatus.ARCHIVADO
    db.add(case)
    await db.commit()
    return {"detail": "Expediente archivado correctamente. El historial se conserva."}
