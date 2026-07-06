# File: app/api/endpoints/history.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.user import User
from app.models.history import History
from app.models.response import AIResponse
from app.models.saved_response import SavedResponse
from app.services.auth_service import get_current_user
from app.schemas.history import HistoryOut, SavedRequest, SavedResponseOut

router = APIRouter()

@router.get("/history", response_model=List[HistoryOut])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve educational milestone logs representing student timeline history."""
    try:
        logs = db.query(History).filter(
            History.user_id == current_user.id
        ).order_by(History.created_at.desc()).all()
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history logs: {str(e)}"
        )

@router.post("/save", response_model=SavedResponseOut, status_code=status.HTTP_201_CREATED)
def save_response(
    payload: SavedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save an AI response response to the bookmarked list and append history log."""
    if payload.source_response_id:
        response = db.query(AIResponse).filter(
            AIResponse.id == payload.source_response_id,
            AIResponse.user_id == current_user.id
        ).first()
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source AI response log not found or unauthorized access."
            )
            
    try:
        saved_item = SavedResponse(
            user_id=current_user.id,
            source_response_id=payload.source_response_id,
            title=payload.title,
            category=payload.category,
            content=payload.content
        )
        db.add(saved_item)
        db.flush()  # Extract saved_item.id
        
        # Log to student study history
        history_log = History(
            user_id=current_user.id,
            action="saved_response",
            entity_id=saved_item.id,
            entity_type="saved_response",
            description=f"Bookmarked response: '{payload.title}' ({payload.category})"
        )
        db.add(history_log)
        db.commit()
        db.refresh(saved_item)
        return saved_item
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark response: {str(e)}"
        )

@router.get("/save", response_model=List[SavedResponseOut])
def get_saved_responses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all bookmarked responses saved by the student."""
    try:
        saved_items = db.query(SavedResponse).filter(
            SavedResponse.user_id == current_user.id
        ).order_by(SavedResponse.created_at.desc()).all()
        return saved_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bookmarked list: {str(e)}"
        )

@router.delete("/save/{saved_id}", status_code=status.HTTP_200_OK)
def delete_saved_response(
    saved_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a bookmarked response by ID."""
    saved_item = db.query(SavedResponse).filter(
        SavedResponse.id == saved_id,
        SavedResponse.user_id == current_user.id
    ).first()
    
    if not saved_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmarked item not found or unauthorized access."
        )
        
    try:
        db.delete(saved_item)
        
        # Log deletion activity
        history_log = History(
            user_id=current_user.id,
            action="deleted_saved_response",
            entity_id=saved_id,
            entity_type="saved_response",
            description=f"Deleted bookmark with title: '{saved_item.title}'"
        )
        db.add(history_log)
        db.commit()
        return {"status": "success", "message": "Bookmarked item successfully removed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove bookmark: {str(e)}"
        )
