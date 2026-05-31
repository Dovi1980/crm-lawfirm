from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.case import CaseType, CaseStatus
from app.schemas.client import ClientResponse
from app.schemas.user import UserResponse

class CaseBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    case_type: CaseType = CaseType.OTRO
    status: CaseStatus = CaseStatus.NUEVO
    client_id: int
    assigned_lawyer_id: int
    start_date: date = Field(default_factory=date.today)
    estimated_close_date: Optional[date] = None
    agreed_fees: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    internal_notes: Optional[str] = None

    @field_validator("title", "description", "internal_notes", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    case_type: Optional[CaseType] = None
    status: Optional[CaseStatus] = None
    client_id: Optional[int] = None
    assigned_lawyer_id: Optional[int] = None
    start_date: Optional[date] = None
    estimated_close_date: Optional[date] = None
    agreed_fees: Optional[Decimal] = Field(None, max_digits=12, decimal_places=2)
    internal_notes: Optional[str] = None

    @field_validator("title", "description", "internal_notes", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class CaseResponse(CaseBase):
    id: int
    case_number: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested helpers for React UI
    client: Optional[ClientResponse] = None
    assigned_lawyer: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
