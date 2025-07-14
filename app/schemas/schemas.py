#backend\app\schemas\schemas.py
#auth_router to schemas /register

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True  # Required for ORM models in Pydantic v2

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class UserProfileResponse(BaseModel):
    email: str
    name: str
    phone: str
    location: str

    