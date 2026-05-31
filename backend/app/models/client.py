import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.database import Base

class ClientType(str, enum.Enum):
    NATURAL = "natural"  # Persona Física
    LEGAL = "legal"      # Persona Jurídica

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_type: Mapped[ClientType] = mapped_column(Enum(ClientType), nullable=False, default=ClientType.NATURAL)
    tax_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True) # CUIT/CUIL/DNI
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    province: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(String, nullable=True) # TEXT
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="client", cascade="all, delete-orphan")
    interactions: Mapped[List["Interaction"]] = relationship("Interaction", back_populates="client", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="client", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
