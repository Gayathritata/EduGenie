# File: app/services/edu_service.py
# Part of EduGenie SmartBridge Project

import json
import logging
import time
from sqlalchemy.orm import Session
from app.models.query import Query
from app.models.response import AIResponse
from app.models.quiz import Quiz
from app.models.summary import Summary
from app.models.learning_path import LearningPath
from app.models.history import History
from app.services.prompt_manager import PromptManager
from app.services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger("edugenie")
ai_orchestrator = AIOrchestrator()

class EduService:
    @staticmethod
    def ask_question(db: Session, user_id: int, question: str, context: str = None) -> dict:
        """Process Q&A query using Google Gemini, validates JSON response, and log audit details."""
        # 1. Log query input
        query = Query(user_id=user_id, query_text=question, query_type="qa")
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 2. Query Gemini and measure latency
        prompt = PromptManager.get_qa_prompt(question, context)
        start_time = time.time()
        response_raw = ai_orchestrator.query_gemini(prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Parse JSON response safely
        try:
            parsed_json = ai_orchestrator.parse_json_response(response_raw)
            answer_text = parsed_json.get("answer", response_raw)
        except Exception as e:
            logger.warning(f"Failed to parse Q&A response JSON: {e}. Using raw response.")
            answer_text = response_raw
        
        # 4. Save response log
        ai_response = AIResponse(
            query_id=query.id,
            user_id=user_id,
            response_text=answer_text,
            model_used="gemini-1.5-flash",
            latency_ms=latency_ms
        )
        db.add(ai_response)
        
        # 5. Log activity timeline
        history_log = History(
            user_id=user_id,
            action="asked_question",
            entity_id=query.id,
            entity_type="query",
            description=f"Asked: '{question[:45]}...'"
        )
        db.add(history_log)
        db.commit()
        db.refresh(ai_response)
        
        return {"answer": answer_text, "session_id": ai_response.id}

    @staticmethod
    def explain_concept(db: Session, user_id: int, concept: str, depth_level: str) -> dict:
        """Process concept explanation using LaMini-Flan-T5 model and log timeline history."""
        # 1. Log query input
        query = Query(
            user_id=user_id, 
            query_text=f"Concept: '{concept}' depth: '{depth_level}'", 
            query_type="explain"
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 2. Query LaMini model and measure latency
        prompt = PromptManager.get_explain_prompt(concept, depth_level)
        start_time = time.time()
        response_raw = ai_orchestrator.query_lamini(prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Wrap response into a structured format
        explanation_text = response_raw
        
        # 3. Save response log
        ai_response = AIResponse(
            query_id=query.id,
            user_id=user_id,
            response_text=explanation_text,
            model_used="lamini-flan-t5",
            latency_ms=latency_ms
        )
        db.add(ai_response)
        
        # 4. Log timeline activity
        history_log = History(
            user_id=user_id,
            action="requested_explanation",
            entity_id=query.id,
            entity_type="query",
            description=f"Requested explanation for concept: '{concept}' ({depth_level})"
        )
        db.add(history_log)
        db.commit()
        db.refresh(ai_response)
        
        return {"explanation": explanation_text, "session_id": ai_response.id}

    @staticmethod
    def summarize_text(db: Session, user_id: int, text: str, target_length: str) -> dict:
        """Summarize text using Google Gemini, validates JSON response, and save summary log."""
        # 1. Log query input
        query = Query(
            user_id=user_id,
            query_text=f"Summarize text (length: {target_length}): '{text[:100]}...'",
            query_type="summarize"
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 2. Query Gemini and measure latency
        prompt = PromptManager.get_summarize_prompt(text, target_length)
        start_time = time.time()
        response_raw = ai_orchestrator.query_gemini(prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Parse JSON response safely
        try:
            parsed_json = ai_orchestrator.parse_json_response(response_raw)
            summary_text = parsed_json.get("summary", response_raw)
        except Exception as e:
            logger.warning(f"Failed to parse Summarization response JSON: {e}. Using raw response.")
            summary_text = response_raw
            
        # 4. Save response log
        ai_response = AIResponse(
            query_id=query.id,
            user_id=user_id,
            response_text=summary_text,
            model_used="gemini-1.5-flash",
            latency_ms=latency_ms
        )
        db.add(ai_response)
        
        # 5. Save Summary log record
        summary_record = Summary(
            user_id=user_id,
            source_text=text,
            summary_text=summary_text,
            length_type=target_length
        )
        db.add(summary_record)
        
        # 6. Save history timeline log
        db.commit()
        db.refresh(summary_record)
        
        history_log = History(
            user_id=user_id,
            action="summarized_text",
            entity_id=summary_record.id,
            entity_type="summary",
            description=f"Summarized study material ({target_length})"
        )
        db.add(history_log)
        db.commit()
        db.refresh(ai_response)
        
        return {"summary": summary_text, "session_id": ai_response.id}

    @staticmethod
    def generate_roadmap(db: Session, user_id: int, topic: str, difficulty: str) -> dict:
        """Generate interactive roadmap milestone path using Google Gemini and parse response."""
        # 1. Log query input
        query = Query(
            user_id=user_id,
            query_text=f"Learning roadmap topic: '{topic}' difficulty: '{difficulty}'",
            query_type="roadmap_gen"
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 2. Query Gemini
        prompt = PromptManager.get_roadmap_prompt(topic, difficulty)
        start_time = time.time()
        response_raw = ai_orchestrator.query_gemini(prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Parse JSON response safely
        try:
            roadmap_data = ai_orchestrator.parse_json_response(response_raw)
        except Exception as e:
            logger.error(f"Failed to parse generated roadmap JSON: {e}. Raw text: {response_raw}")
            # Fallback structure
            roadmap_data = {
                "topic": topic,
                "difficulty": difficulty,
                "estimated_weeks": 6,
                "prerequisites": ["Basic understanding"],
                "steps": [
                    {
                        "step_number": 1,
                        "title": f"Fundamentals of {topic}",
                        "description": f"Introduction to critical concepts of {topic}.",
                        "topics_covered": ["Core syntax", "Terminology"],
                        "checkpoint_quiz_topic": f"Intro to {topic}"
                    }
                ]
            }

        # 4. Save response log
        ai_response = AIResponse(
            query_id=query.id,
            user_id=user_id,
            response_text=json.dumps(roadmap_data),
            model_used="gemini-1.5-flash",
            latency_ms=latency_ms
        )
        db.add(ai_response)
        
        # 5. Save LearningPath record
        learning_path = LearningPath(
            user_id=user_id,
            topic=topic,
            difficulty=difficulty,
            roadmap_data=roadmap_data
        )
        db.add(learning_path)
        
        # 6. Save history timeline log
        db.commit()
        db.refresh(learning_path)
        
        history_log = History(
            user_id=user_id,
            action="generated_roadmap",
            entity_id=learning_path.id,
            entity_type="learning_path",
            description=f"Generated learning path roadmap for '{topic}' ({difficulty})"
        )
        db.add(history_log)
        db.commit()
        
        return {
            "roadmap_id": learning_path.id,
            "topic": learning_path.topic,
            "difficulty": learning_path.difficulty,
            "roadmap_data": learning_path.roadmap_data
        }

    @staticmethod
    def generate_quiz(db: Session, user_id: int, topic: str, num_questions: int, difficulty: str = "Intermediate") -> dict:
        """Generate multiple choice quizzes using Google Gemini, save record, and strip correct answers."""
        # 1. Log query input
        query = Query(
            user_id=user_id,
            query_text=f"Quiz topic: '{topic}' questions: '{num_questions}' difficulty: '{difficulty}'",
            query_type="quiz_gen"
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        
        # 2. Query Gemini
        prompt = PromptManager.get_quiz_prompt(topic, num_questions, difficulty)
        start_time = time.time()
        response_raw = ai_orchestrator.query_gemini(prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 3. Parse JSON response safely
        try:
            quiz_data = ai_orchestrator.parse_json_response(response_raw)
        except Exception as e:
            logger.error(f"Failed to parse generated quiz JSON: {e}. Raw text: {response_raw}")
            # Fallback basic question
            quiz_data = {
                "topic": topic,
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": f"Which of the following is core to {topic}?",
                        "choices": ["Fundamentals", "Advanced concepts", "Interactive Practice", "All of the above"],
                        "correct_key": "D",
                        "explanation": "Active learning cycles include foundation, progression, and practical application."
                    }
                ]
            }

        # 4. Save response log
        ai_response = AIResponse(
            query_id=query.id,
            user_id=user_id,
            response_text=json.dumps(quiz_data),
            model_used="gemini-1.5-flash",
            latency_ms=latency_ms
        )
        db.add(ai_response)
        
        # 5. Save Quiz record
        quiz = Quiz(
            user_id=user_id,
            topic=topic,
            questions_data=quiz_data,
            total_questions=len(quiz_data.get("questions", []))
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # 6. Save history timeline log
        history_log = History(
            user_id=user_id,
            action="generated_quiz",
            entity_id=quiz.id,
            entity_type="quiz",
            description=f"Generated interactive quiz on topic: '{topic}' ({difficulty})"
        )
        db.add(history_log)
        db.commit()
        
        # Strip correct answers and explanations for quiz integrity
        questions_out = []
        for q in quiz_data.get("questions", []):
            questions_out.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "choices": q.get("choices")
            })
            
        return {
            "quiz_id": quiz.id,
            "topic": quiz.topic,
            "difficulty": quiz_data.get("difficulty", difficulty),
            "questions": questions_out
        }

    @staticmethod
    def grade_quiz(db: Session, user_id: int, quiz_id: int, answers: dict) -> dict:
        """Verify user choices, update score in Quiz record, and log history."""
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == user_id).first()
        if not quiz:
            raise ValueError("Quiz not found or unauthorized access.")
            
        questions = quiz.questions_data.get("questions", [])
        score = 0
        total = len(questions)
        results = []
        
        for q in questions:
            q_id = str(q.get("id"))
            correct_key = q.get("correct_key", "").upper()
            user_key = answers.get(q_id, "").upper()
            is_correct = (correct_key == user_key)
            if is_correct:
                score += 1
                
            results.append({
                "id": q.get("id"),
                "question": q.get("question"),
                "correct_key": correct_key,
                "user_key": user_key,
                "is_correct": is_correct,
                "explanation": q.get("explanation", "")
            })
            
        # Update score in database
        quiz.score = score
        
        # Add to history timeline log
        history_log = History(
            user_id=user_id,
            action="completed_quiz",
            entity_id=quiz.id,
            entity_type="quiz",
            description=f"Scored {score}/{total} on quiz: '{quiz.topic}'"
        )
        db.add(history_log)
        db.commit()
        
        return {
            "score": score,
            "total": total,
            "results": results
        }
