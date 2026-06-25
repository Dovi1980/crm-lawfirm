import re
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


class CustomTemplateVariable(BaseModel):
    key: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=120)
    type: Literal["text", "textarea", "money", "date"] = "text"
    required: bool = True
    placeholder: str = Field("", max_length=200)
    help: str = Field("", max_length=300)

    @field_validator("key")
    @classmethod
    def normalize_key(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z][a-z0-9_]*$", cleaned):
            raise ValueError("La clave debe empezar con letra y solo contener letras, números o guión bajo.")
        return cleaned


class CustomTemplateCreate(BaseModel):
    key: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=500)
    instruction: str = Field(..., min_length=20, max_length=8000)
    variables: list[CustomTemplateVariable] = Field(default_factory=list, max_length=20)
    default_title: str = Field("", max_length=200)
    is_active: bool = True

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not _KEY_RE.match(cleaned):
            raise ValueError(
                "Clave inválida: 3-64 caracteres, letras minúsculas, números o guión bajo."
            )
        return cleaned

    @field_validator("variables")
    @classmethod
    def unique_variable_keys(cls, v: list[CustomTemplateVariable]) -> list[CustomTemplateVariable]:
        keys = [item.key for item in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Las claves de variables deben ser únicas.")
        return v


class CustomTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    instruction: Optional[str] = Field(None, min_length=20, max_length=8000)
    variables: Optional[list[CustomTemplateVariable]] = Field(None, max_length=20)
    default_title: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None


class CustomTemplateResponse(BaseModel):
    id: int
    key: str
    name: str
    description: str
    instruction: str
    variables: list[CustomTemplateVariable]
    default_title: str
    is_active: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateCatalogItem(BaseModel):
    """For listing built-in + custom in admin UI with their origin."""
    key: str
    name: str
    description: str
    default_title: str
    variable_count: int
    is_builtin: bool
    is_active: bool = True
    custom_id: Optional[int] = None
