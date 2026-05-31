import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base

class InteractionType(str, enum.Enum):
    LLAMADA = "llamada"
    EMAIL = "email"
    REUNION = "reunion"
    ESCRITO = "escrito"
    AUDIENCIA = "audiencia"
    OTRO = "otro"

class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType), nullable=False, default=InteractionType.OTRO)
    description: Mapped[str] = mapped_column(String, nullable=False) # TEXT
    interaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Foreign Keys
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # This is an append-only table, no updated_at is specified in prompt
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interactions")
    case: Mapped[Optional["Case"]] = relationship("Case", back_populates="interactions")
    client: Mapped[Optional["Client"]] = relationship("Client", back_populates="interactions")
