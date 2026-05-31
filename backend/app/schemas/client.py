from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.models.client import ClientType

class ClientBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    client_type: ClientType = ClientType.NATURAL
    tax_id: Optional[str] = Field(None, max_length=50) # DNI/CUIT/CUIL
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("first_name", "last_name", "tax_id", "phone", "address", "city", "province", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    client_type: Optional[ClientType] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("first_name", "last_name", "tax_id", "phone", "address", "city", "province", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class ClientResponse(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
