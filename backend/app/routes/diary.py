from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

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
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(DiaryEntry)
        .filter(
            DiaryEntry.user_id == current_user.id,
            DiaryEntry.is_deleted == False
        )
        .order_by(desc(DiaryEntry.created_at))
        .all()
    )



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

