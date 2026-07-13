# File: app/api/endpoints/ai_core.py
# Part of EduGenie SmartBridge Project

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.edu_service import EduService
from app.schemas.ai import (
    QARequest, QAResponse,
    ExplainRequest, ExplainResponse,
    SummarizeRequest, SummarizeResponse,
    RoadmapRequest, RoadmapResponse,
    QuizRequest, QuizResponse, QuizSubmitRequest, QuizSubmitResponse
)

router = APIRouter()

@router.post("/qa", response_model=QAResponse)
def ask_question(
    payload: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Answers a learning question using optional context support."""
    try:
        result = EduService.ask_question(db, current_user.id, payload.question, payload.context)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A system failure: {str(e)}"
        )

@router.post("/explain", response_model=ExplainResponse)
def explain_concept(
    payload: ExplainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Explains a target concept customized to specific depth levels."""
    try:
        result = EduService.explain_concept(db, current_user.id, payload.concept, payload.depth_level)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation system failure: {str(e)}"
        )

@router.post("/summarize", response_model=SummarizeResponse)
def summarize_text(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Summarizes text using Google Gemini."""
    try:
        result = EduService.summarize_text(db, current_user.id, payload.text, payload.target_length)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization system failure: {str(e)}"
        )

@router.post("/learn", response_model=RoadmapResponse)
def generate_learning_path(
    payload: RoadmapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates an interactive learning roadmap path."""
    try:
        result = EduService.generate_roadmap(db, current_user.id, payload.topic, payload.difficulty)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Roadmap generation system failure: {str(e)}"
        )

@router.post("/quiz", response_model=QuizResponse)
def generate_quiz(
    payload: QuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a multiple choice quiz on the requested topic."""
    try:
        result = EduService.generate_quiz(db, current_user.id, payload.topic, payload.num_questions, payload.difficulty, payload.context)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation system failure: {str(e)}"
        )

@router.post("/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grades a quiz submission and saves user scores."""
    try:
        result = EduService.grade_quiz(db, current_user.id, payload.quiz_id, payload.answers)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz evaluation system failure: {str(e)}"
        )
