from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.database import get_db
from app.schemas.diary_entry import (
    DiaryEntryCreate,
    DiaryEntryResponse,
    DiaryEntryUpdate,
)
from app.models.diary_entry import DiaryEntry
from app.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/diary",
    tags=["Diary"]
)

# ----------------------------------------
# CREATE ENTRY
# ----------------------------------------
@router.post(
    "/",
    response_model=DiaryEntryResponse,
    status_code=201
)
def create_entry(
    entry_data: DiaryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_entry = DiaryEntry(
        raw_text=entry_data.raw_text,
        user_id=current_user.id,
        is_improved=False
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry



# ----------------------------------------
# LIST ENTRIES
# ----------------------------------------
@router.get(
    "/",
    response_model=List[DiaryEntryResponse]
)
def list_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    from_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    to_date: Optional[datetime] = Query(None, description="End date for filtering"),
    search: Optional[str] = Query(None, description="Search text in raw_text or improved_text")
):
    query = db.query(DiaryEntry).filter(
        DiaryEntry.user_id == current_user.id,
        DiaryEntry.is_deleted == False
    )
    
    # Apply date filters
    if from_date:
        query = query.filter(DiaryEntry.created_at >= from_date)
    if to_date:
        query = query.filter(DiaryEntry.created_at <= to_date)
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (DiaryEntry.raw_text.ilike(search_pattern)) |
            (DiaryEntry.improved_text.ilike(search_pattern))
        )
    
    return query.order_by(desc(DiaryEntry.created_at)).all()



# ----------------------------------------
# GET ENTRY BY ID
# ----------------------------------------
@router.get(
    "/{entry_id}",
    response_model=DiaryEntryResponse
)
def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.is_deleted == False
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return entry



# ----------------------------------------
# UPDATE ENTRY
# ----------------------------------------
@router.patch(
    "/{entry_id}",
    response_model=DiaryEntryResponse
)
def update_entry(
    entry_id: UUID,
    update_data: DiaryEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.is_deleted == False
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    update_fields = update_data.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)

    return entry



# ----------------------------------------
# SOFT DELETE ENTRY
# ----------------------------------------
@router.delete(
    "/{entry_id}",
    status_code=204
)
def delete_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.is_deleted == False
        )
        .first()
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.is_deleted = True
    db.commit()

    return None

