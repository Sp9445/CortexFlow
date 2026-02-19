# backend/app/routes/mcp_server.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.routes.diary import search_diary_entries

router = APIRouter(prefix="/tools", tags=["MCP Tools"])

class MCPRequest(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Free-text search query (optional, leave empty to include all entries)"
    )
    from_date: Optional[datetime] = Field(
        None, description="Inclusive start of the date range (ISO format)"
    )
    to_date: Optional[datetime] = Field(
        None, description="Inclusive end of the date range (ISO format)"
    )
    user_id: Optional[str] = Field(
        None, description="User ID for filtering entries (will be set by the API)"
    )

@router.post("/searchDiaryEntryTool")
def search_diary_tool(payload: MCPRequest) -> List[dict]:
    """
    This endpoint searches diary entries for a user.
    The model calls this tool when the user asks questions about their diary.
    
    Returns a **pure JSON‑serialisable list** of diary entries matching the criteria.
    """
    if not payload.user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id is required in tool parameters"
        )
    
    try:
        user_uuid = UUID(payload.user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid user_id format"
        )
    
    # Convert string dates to datetime if provided
    from_dt = None
    to_dt = None
    if payload.from_date:
        from_dt = payload.from_date
    if payload.to_date:
        to_dt = payload.to_date
    
    # Call the service function
    entries = search_diary_entries(
        user_id=user_uuid,
        query=payload.query,
        from_date=from_dt,
        to_date=to_dt,
    )
    
    return entries
