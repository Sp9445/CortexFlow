import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.utils.timestamps import now_ist


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)

    raw_text = Column(Text, nullable=False)
    improved_text = Column(Text, nullable=True)

    is_improved = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=now_ist, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_ist, onupdate=now_ist, nullable=False)

    user = relationship("User", back_populates="diary_entries")
