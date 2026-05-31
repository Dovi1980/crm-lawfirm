import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Configure simple seed logging
structlog.configure()
logger = structlog.get_logger()

from app.config import settings
from app.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

async def seed_admin():
    """
    Asynchronously seeds the first administrator account if it doesn't exist.
    Uses FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD configured in environment variables.
    """
    logger.info("Initializing database admin seeder...")

    async with SessionLocal() as db:
        # Check if first admin email already exists
        email = settings.FIRST_ADMIN_EMAIL.lower()
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info("Admin user already seeded in database.", email=email)
            return

        # Secure password hashing
        hashed_password = AuthService.hash_password(settings.FIRST_ADMIN_PASSWORD)

        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            first_name="Admin",
            last_name="Principal",
            role=UserRole.ADMIN,
            is_active=True
        )

        db.add(admin_user)
        await db.commit()
        logger.info(
            "Administrator user created successfully!", 
            email=email, 
            role=UserRole.ADMIN.value
        )

async def main():
    try:
        await seed_admin()
    finally:
        # Close connection engine pool
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
