from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.middleware.security import RoleChecker, get_current_active_user
from app.services.auth_service import AuthService

# Router config: globally allow authenticated staff
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all studio users. Accessible to all active staff.
    """
    stmt = select(User).order_by(User.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_guard: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Create a new studio user (Admin only). Hashes the password securely.
    """
    # Check if email is already taken
    stmt = select(User).where(User.email == payload.email.lower())
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La dirección de correo electrónico ya está registrada."
        )

    # Secure Hash
    hashed_pwd = AuthService.hash_password(payload.password)

    new_user = User(
        email=payload.email.lower(),
        hashed_password=hashed_pwd,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        is_active=payload.is_active
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific user.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_guard: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Update user information (Admin only). Hashes password if updated.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        user.hashed_password = AuthService.hash_password(update_data["password"])
        update_data.pop("password")

    for key, value in update_data.items():
        setattr(user, key, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Delete a user or mark them inactive if they have assigned cases.
    Prevent admins from deleting themselves.
    """
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta de administrador"
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    try:
        # Check if we can safely hard-delete. Otherwise, soft-delete.
        await db.delete(user)
        await db.commit()
        return {"detail": "Usuario eliminado correctamente"}
    except Exception:
        # Fallback to Soft-Deactivation to maintain database integrity (RESTRICT FK checks)
        await db.rollback()
        user.is_active = False
        db.add(user)
        await db.commit()
        return {"detail": "El usuario posee expedientes o actividades. Se procedió a desactivar su cuenta."}
