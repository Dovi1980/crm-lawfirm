"""
Archivos subidos por el usuario (documentación escaneada) adjuntos a un caso.

El binario vive en disco (volumen Docker, `settings.UPLOAD_DIR`); en la base solo
se guarda la metadata + el nombre con que está guardado físicamente (UUID). El
nombre original se preserva solo para mostrar y para la descarga.
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)        # original
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False) # uuid en disco
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case = relationship("Case", backref="attachments")
    uploaded_by = relationship("User")
