from typing import Optional

from pydantic import BaseModel

from app.schemas.user import UserResponse


class EnvironmentInformationResponse(BaseModel):
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
