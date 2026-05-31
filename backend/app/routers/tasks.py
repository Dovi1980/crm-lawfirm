from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User, UserRole
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.middleware.security import get_current_active_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

async def get_scoped_task(task_id: int, db: AsyncSession, user: User) -> Task:
    """Helper to query task and assert role scopes."""
    stmt = select(Task).options(selectinload(Task.assigned_to)).where(Task.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )

    # Lawyers are scoped to their assigned tasks
    if user.role == UserRole.LAWYER and task.assigned_to_id != user.id and task.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No posees privilegios para interactuar con esta tarea."
        )
        
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assigned_to_id: Optional[int] = None,
    case_id: Optional[int] = None,
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List tasks.
    Lawyers default to tasks assigned to them.
    Admins/Assistants can view all or filter by assignee.
    """
    stmt = select(Task).options(selectinload(Task.assigned_to))

    # Scope filtering
    if current_user.role == UserRole.LAWYER:
        stmt = stmt.where(
            or_(
                Task.assigned_to_id == current_user.id,
                Task.created_by_id == current_user.id
            )
        )
    elif assigned_to_id:
        stmt = stmt.where(Task.assigned_to_id == assigned_to_id)

    # General Filters
    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if case_id:
        stmt = stmt.where(Task.case_id == case_id)
    if client_id:
        stmt = stmt.where(Task.client_id == client_id)

    stmt = stmt.order_by(Task.due_date.asc(), Task.priority.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new Task.
    """
    new_task = Task(
        created_by_id=current_user.id,
        **payload.model_dump()
    )
    db.add(new_task)
    await db.commit()
    
    # Return with relations
    return await get_scoped_task(new_task.id, db, current_user)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_details(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch a single task. Enforces lawyer ownership bounds.
    """
    return await get_scoped_task(task_id, db, current_user)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Modify an existing task.
    """
    task = await get_scoped_task(task_id, db, current_user)
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.add(task)
    await db.commit()
    await db.refresh(task)
    return await get_scoped_task(task_id, db, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a task. Assistants are blocked.
    """
    if current_user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los asistentes no tienen autorización para eliminar tareas."
        )

    task = await get_scoped_task(task_id, db, current_user)
    await db.delete(task)
    await db.commit()
    return {"detail": "Tarea eliminada correctamente"}
