import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator

from app.models.user import GenderEnum


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: GenderEnum
    profile_picture: Optional[str] = None

    @field_validator("profile_picture")
    @classmethod
    def validate_picture_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            HttpUrl(v)
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    profile_picture: Optional[str] = None

    @field_validator("profile_picture")
    @classmethod
    def validate_picture_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            HttpUrl(v)
        return v


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    profile_picture: Optional[str] = None
    gender: GenderEnum
    created_at: datetime

    model_config = {"from_attributes": True}


class UserStats(BaseModel):
    events_created: int
    events_attended: int
