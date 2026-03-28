import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas.user import UserOut


class ReviewCreate(BaseModel):
    rating: int
    text: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user: UserOut
    rating: int
    text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
