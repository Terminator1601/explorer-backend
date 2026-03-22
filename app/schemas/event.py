import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

from app.schemas.user import UserOut


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    start_time: datetime
    end_time: datetime
    max_participants: int = 50
    is_private: bool = False
    interest_tag: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class EventOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    start_time: datetime
    end_time: datetime
    max_participants: int
    is_private: bool
    interest_tag: Optional[str] = None
    created_by: uuid.UUID
    created_at: datetime
    creator: Optional[UserOut] = None
    participant_count: int = 0
    distance_meters: Optional[float] = None
    is_user_participant: bool = False

    model_config = {"from_attributes": True}


class EventNearbyQuery(BaseModel):
    lat: float
    lng: float
    radius: float = 5000.0
    interest_tag: Optional[str] = None


class JoinResponse(BaseModel):
    message: str
    event_id: uuid.UUID
    user_id: uuid.UUID
    status: str
