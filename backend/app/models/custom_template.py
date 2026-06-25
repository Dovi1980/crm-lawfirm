"""
Admin-defined document templates persisted in DB.

Coexist with the built-in templates declared in `document_templates.py`.
The service layer merges them; built-in always win on key collision so an
admin can't accidentally shadow a system template.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CustomTemplate(Base):
    __tablename__ = "custom_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    instruction: Mapped[str] = mapped_column(String, nullable=False)  # TEXT
    # Stored as JSON: list[{key, label, type, required, placeholder, help}]
    variables: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    default_title: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by = relationship("User")
