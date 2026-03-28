import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserOut


class CommentCreate(BaseModel):
    text: str


class CommentOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user: UserOut
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
