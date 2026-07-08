# File: app/schemas/ai.py
# Part of EduGenie SmartBridge Project

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Q&A Schema
class QARequest(BaseModel):
    question: str = Field(..., min_length=5, description="The educational question to ask")
    context: Optional[str] = Field(None, description="Optional textbook context or code snippet")

class QAResponse(BaseModel):
    answer: str
    session_id: int
    key_concepts: Optional[List[str]] = Field(default_factory=list, description="Key concepts covered in the answer")
    follow_up_questions: Optional[List[str]] = Field(default_factory=list, description="Suggested follow-up questions for deeper learning")

# Concept Explanation Schema
class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=2, description="The concept to be explained")
    depth_level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$", description="Target audience level")

class ExplainResponse(BaseModel):
    explanation: str
    session_id: int

# Summarize Schema
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The text body to summarize")
    target_length: str = Field("medium", pattern="^(short|medium|long)$", description="Target summary length")

class SummarizeResponse(BaseModel):
    summary: str
    session_id: int
    bullet_points: Optional[List[str]] = Field(default_factory=list, description="Key bullet points from the text")
    important_keywords: Optional[List[str]] = Field(default_factory=list, description="Important keywords extracted from the text")
    key_concepts: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Key concepts with definitions")
    revision_notes: Optional[str] = Field(default="", description="Compact revision notes for exam preparation")

# Roadmap Schema
class RoadmapRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The topic to generate a learning path for")
    difficulty: str = Field("Beginner", pattern="^(Beginner|Intermediate|Advanced)$", description="Difficulty tier")

class RoadmapResponse(BaseModel):
    roadmap_id: int
    topic: str
    difficulty: str
    roadmap_data: Any

# Quiz Schema
class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The subject topic for the quiz")
    num_questions: int = Field(5, ge=1, le=10, description="Number of questions to generate (1 to 10)")
    difficulty: str = Field("Intermediate", pattern="^(Beginner|Intermediate|Advanced)$", description="Difficulty level")

class QuizQuestionOut(BaseModel):
    id: int
    question: str
    choices: List[str]

class QuizResponse(BaseModel):
    quiz_id: int
    topic: str
    difficulty: str
    questions: List[QuizQuestionOut]

class QuizSubmitRequest(BaseModel):
    quiz_id: int
    answers: Dict[str, str]  # e.g., {"1": "A", "2": "C"}

class QuizQuestionGrade(BaseModel):
    id: int
    question: str
    correct_key: str
    user_key: str
    is_correct: bool
    explanation: str

class QuizSubmitResponse(BaseModel):
    score: int
    total: int
    results: List[QuizQuestionGrade]
