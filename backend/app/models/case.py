import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Enum, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from app.database import Base

class CaseType(str, enum.Enum):
    CIVIL = "civil"
    PENAL = "penal"
    LABORAL = "laboral"
    COMERCIAL = "comercial"
    FAMILIA = "familia"
    OTRO = "otro"

class CaseStatus(str, enum.Enum):
    NUEVO = "nuevo"
    EN_PROCESO = "en_proceso"
    EN_ESPERA = "en_espera"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False) # e.g. EXP-2026-0001
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True) # TEXT
    case_type: Mapped[CaseType] = mapped_column(Enum(CaseType), nullable=False, default=CaseType.OTRO)
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), nullable=False, default=CaseStatus.NUEVO)
    
    # Foreign Keys
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_lawyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    estimated_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    agreed_fees: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True) # TEXT
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="cases")
    assigned_lawyer: Mapped["User"] = relationship("User", back_populates="assigned_cases", foreign_keys=[assigned_lawyer_id])
    creator: Mapped["User"] = relationship("User", back_populates="created_cases", foreign_keys=[created_by_id])
    
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="case", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="case", cascade="all, delete-orphan")
