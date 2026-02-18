from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class DiaryEntryBase(BaseModel):
    raw_text: str


class DiaryEntryCreate(DiaryEntryBase):
    pass


class DiaryEntryUpdate(BaseModel):
    raw_text: Optional[str] = None
    improved_text: Optional[str] = None
    is_improved: Optional[bool] = None


class DiaryEntryResponse(BaseModel):
    id: UUID
    raw_text: str
    improved_text: Optional[str]
    is_improved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
