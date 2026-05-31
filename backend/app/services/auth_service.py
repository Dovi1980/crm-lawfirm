import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.token import RefreshToken, PasswordResetToken
from app.models.user import User

# Using bcrypt with rounds=12 by default for passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token with SHA-256 for secure DB storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    async def create_refresh_token(cls, db: AsyncSession, user_id: int) -> str:
        """Create a cryptographically secure refresh token and store its hash in the database."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        db_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revoked=False
        )
        db.add(db_token)
        await db.commit()
        return raw_token

    @classmethod
    async def verify_refresh_token(cls, db: AsyncSession, raw_token: str) -> Optional[User]:
        """Verify the refresh token, clean up revoked/expired ones, and return the User if valid."""
        token_hash = cls.hash_token(raw_token)
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.revoked == False)
            .where(RefreshToken.expires_at > datetime.utcnow())
        )
        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            return None

        # Fetch associated user
        stmt_user = select(User).where(User.id == db_token.user_id).where(User.is_active == True)
        result_user = await db.execute(stmt_user)
        return result_user.scalar_one_or_none()

    @classmethod
    async def revoke_refresh_token(cls, db: AsyncSession, raw_token: str) -> bool:
        """Revoke a specific refresh token (used during logout)."""
        token_hash = cls.hash_token(raw_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if db_token:
            db_token.revoked = True
            await db.commit()
            return True
        return False

    @classmethod
    async def create_password_reset_token(cls, db: AsyncSession, user_id: int) -> str:
        """Create a secure one-time password reset token valid for 15 minutes."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        db_token = PasswordResetToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            used=False
        )
        db.add(db_token)
        await db.commit()
        return raw_token

    @classmethod
    async def use_password_reset_token(cls, db: AsyncSession, raw_token: str) -> Optional[User]:
        """Verify a password reset token, mark it as used, and return the associated active user."""
        token_hash = cls.hash_token(raw_token)
        stmt = (
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .where(PasswordResetToken.used == False)
            .where(PasswordResetToken.expires_at > datetime.utcnow())
        )
        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            return None

        # Mark token as used
        db_token.used = True
        await db.commit()

        # Fetch associated active user
        stmt_user = select(User).where(User.id == db_token.user_id).where(User.is_active == True)
        result_user = await db.execute(stmt_user)
        return result_user.scalar_one_or_none()

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """Decode a JWT access token and return its payload if valid."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != "access":
                return None
            return payload
        except JWTError:
            return None
