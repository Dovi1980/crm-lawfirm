import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"
    ASSISTANT = "assistant"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.LAWYER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    assigned_cases: Mapped[List["Case"]] = relationship(
        "Case", 
        back_populates="assigned_lawyer", 
        foreign_keys="[Case.assigned_lawyer_id]"
    )
    created_cases: Mapped[List["Case"]] = relationship(
        "Case", 
        back_populates="creator", 
        foreign_keys="[Case.created_by_id]"
    )
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="user")
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task", 
        back_populates="assigned_to", 
        foreign_keys="[Task.assigned_to_id]"
    )
    created_tasks: Mapped[List["Task"]] = relationship(
        "Task", 
        back_populates="creator", 
        foreign_keys="[Task.created_by_id]"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens: Mapped[List["PasswordResetToken"]] = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
