from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
