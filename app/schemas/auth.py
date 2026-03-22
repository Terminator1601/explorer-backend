from pydantic import BaseModel, EmailStr

from app.models.user import GenderEnum


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: GenderEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
