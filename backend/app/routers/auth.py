from datetime import datetime, timedelta
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
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

# Refresh token cookie name + scope. Path is limited to /api/auth so the cookie
# is only attached to the few endpoints that actually need it.
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"

# In-Memory Lockout Trackers (Standard for MVP to avoid DB schema creep)
FAILED_LOGINS = {}  # email -> count
LOCKOUTS = {}       # email -> datetime


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Attach the refresh token as a hardened HttpOnly cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        domain=settings.COOKIE_DOMAIN or None,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minute")  # 5 attempts per 15 mins per IP
async def login(
    request: Request,
    response: Response,
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
        FAILED_LOGINS[email] = FAILED_LOGINS.get(email, 0) + 1

        if FAILED_LOGINS[email] >= 10:
            LOCKOUTS[email] = datetime.utcnow() + timedelta(minutes=15)
            FAILED_LOGINS[email] = 0
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

    _set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        role=user.role,
        user_email=user.email,
        user_name=user.full_name
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """
    Reads refresh token from HttpOnly cookie, rotates it, and returns a fresh
    access token. The new refresh token is set in a new cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no encontrada"
        )

    user = await AuthService.verify_refresh_token(db, refresh_token)
    if not user:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido, revocado o expirado"
        )

    # Token rotation: revoke old, issue new
    await AuthService.revoke_refresh_token(db, refresh_token)
    new_access_token = AuthService.create_access_token(data={"sub": user.email, "role": user.role.value})
    new_refresh_token = await AuthService.create_refresh_token(db, user.id)

    _set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        role=user.role,
        user_email=user.email,
        user_name=user.full_name
    )


@router.post("/logout")
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    """
    Revokes the refresh token (read from cookie) and clears the cookie.
    Idempotent: returns OK even if no cookie/token is present.
    """
    if refresh_token:
        await AuthService.revoke_refresh_token(db, refresh_token)
    _clear_refresh_cookie(response)
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

    user.hashed_password = AuthService.hash_password(payload.new_password)
    db.add(user)
    await db.commit()

    return {"detail": "Contraseña actualizada correctamente"}
