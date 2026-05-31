from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.interaction import InteractionType
from app.schemas.user import UserResponse

class InteractionBase(BaseModel):
    interaction_type: InteractionType = InteractionType.OTRO
    description: str
    duration_minutes: int = Field(default=0, ge=0)
    case_id: Optional[int] = None
    client_id: Optional[int] = None

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

class InteractionCreate(InteractionBase):
    pass

class InteractionResponse(InteractionBase):
    id: int
    interaction_date: datetime
    user_id: int
    created_at: datetime
    
    # Expand user for React timeline representation
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
