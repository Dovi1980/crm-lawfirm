from typing import List, Literal
from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    messages: List[ChatMessageIn] = Field(..., min_length=1, max_length=40)


class SummaryResponse(BaseModel):
    summary: str
