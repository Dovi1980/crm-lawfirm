from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.models.task import TaskPriority, TaskStatus
from app.schemas.user import UserResponse

class TaskBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIA
    status: TaskStatus = TaskStatus.PENDIENTE
    assigned_to_id: int
    due_date: date
    case_id: Optional[int] = None
    client_id: Optional[int] = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assigned_to_id: Optional[int] = None
    due_date: Optional[date] = None
    case_id: Optional[int] = None
    client_id: Optional[int] = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else None
        return v

class TaskResponse(TaskBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested response for premium UX
    assigned_to: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
