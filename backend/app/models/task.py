import enum
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base

class TaskPriority(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"

class TaskStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True) # TEXT
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIA)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDIENTE)
    
    # Foreign Keys
    assigned_to_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    assigned_to: Mapped["User"] = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to_id])
    creator: Mapped["User"] = relationship("User", back_populates="created_tasks", foreign_keys=[created_by_id])
    case: Mapped[Optional["Case"]] = relationship("Case", back_populates="tasks")
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="tasks")
