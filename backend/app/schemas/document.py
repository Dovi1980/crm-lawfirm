from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TemplateVariableSchema(BaseModel):
    key: str
    label: str
    type: Literal["text", "textarea", "money", "date"] = "text"
    required: bool = True
    placeholder: str = ""
    help: str = ""


class TemplateSchema(BaseModel):
    key: str
    name: str
    description: str
    default_title: str = ""
    variables: list[TemplateVariableSchema]


class DocumentGenerateRequest(BaseModel):
    template_key: str
    variables: dict[str, str] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    template_key: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    template_key: str
    title: str
    content: str
    generated_by_id: int
    is_archived: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListItem(BaseModel):
    """Lightweight payload for the listing — `content` excluded for bandwidth."""
    id: int
    case_id: int
    template_key: str
    title: str
    generated_by_id: int
    is_archived: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
