from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserLogin, TokenResponse, PasswordResetRequest, PasswordResetConfirm
)
from app.config import settings
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

# Import SlowAPI rate limiter
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, enabled=settings.ENABLE_RATE_LIMITER)
router = APIRouter(prefix="/auth", tags=["auth"])

# In-Memory Lockout Trackers (Standard for MVP to avoid DB schema creep)
# Per-Email failure counts and lockout timestamps
FAILED_LOGINS = {}  # email -> count
LOCKOUTS = {}       # email -> datetime

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minute") # 5 attempts per 15 mins per IP
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    email = credentials.email.lower()
    
    # 1. Check if account is locked out
    lockout_time = LOCKOUTS.get(email)
    if lockout_time and lockout_time > datetime.utcnow():
        remaining = int((lockout_time - datetime.utcnow()).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cuenta bloqueada temporalmente por excesivos intentos fallidos. Intente nuevamente en {remaining} segundos."
        )

    # 2. Query user from DB
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 3. Handle login failures
    if not user or not AuthService.verify_password(credentials.password, user.hashed_password):
        # Increment failures
        FAILED_LOGINS[email] = FAILED_LOGINS.get(email, 0) + 1
        
        # Lockout check (10 attempts consecutive)
        if FAILED_LOGINS[email] >= 10:
            LOCKOUTS[email] = datetime.utcnow() + timedelta(minutes=15)
            FAILED_LOGINS[email] = 0 # reset count
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Su cuenta ha sido bloqueada por 15 minutos debido a 10 intentos fallidos consecutivos."
            )
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos"
        )

    # 4. Handle inactive accounts
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario inactiva o deshabilitada"
        )

    # 5. Success! Reset failure counts and lockout
    FAILED_LOGINS[email] = 0
    LOCKOUTS.pop(email, None)

    # 6. Generate Tokens
    access_token = AuthService.create_access_token(data={"sub": user.email, "role": user.role.value})
    refresh_token = await AuthService.create_refresh_token(db=db, user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
        user_email=user.email,
        user_name=user.full_name
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts a raw refresh token, validates it against active/non-expired ones in DB,
    and returns a fresh access token and a brand-new rotated refresh token.
    """
    user = await AuthService.verify_refresh_token(db, refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido, revocado o expirado"
        )

    # Revoke old refresh token (Token rotation for security)
    await AuthService.revoke_refresh_token(db, refresh_token)

    # Generate new tokens
    new_access_token = AuthService.create_access_token(data={"sub": user.email, "role": user.role.value})
    new_refresh_token = await AuthService.create_refresh_token(db, user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        role=user.role,
        user_email=user.email,
        user_name=user.full_name
    )


@router.post("/logout")
async def logout(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Revokes the provided refresh token to securely terminate the session.
    """
    revoked = await AuthService.revoke_refresh_token(db, refresh_token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token no válido o ya revocado"
        )
    return {"detail": "Sesión cerrada correctamente"}


@router.post("/reset-password-request")
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives email, creates a 15-minute reset token, and sends a recovery email.
    """
    stmt = select(User).where(User.email == payload.email.lower()).where(User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Safe UX: Do not disclose whether email exists. Always return success.
    if user:
        reset_token = await AuthService.create_password_reset_token(db, user.id)
        await EmailService.send_password_reset_email(user.email, reset_token)

    return {"detail": "Si la dirección de correo electrónico es válida, se ha enviado un enlace de recuperación."}


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies reset token and updates the user's password.
    """
    user = await AuthService.use_password_reset_token(db, payload.token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de recuperación es inválido, ya fue usado o ha expirado"
        )

    # Hash new password and save
    user.hashed_password = AuthService.hash_password(payload.new_password)
    db.add(user)
    await db.commit()

    return {"detail": "Contraseña actualizada correctamente"}
