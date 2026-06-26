from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    case_id: int
    filename: str
    mime_type: str
    size_bytes: int
    uploaded_by_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
