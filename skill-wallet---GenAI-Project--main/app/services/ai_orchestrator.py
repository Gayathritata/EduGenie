# File: app/services/ai_orchestrator.py
# Part of EduGenie SmartBridge Project

import logging
import requests
import json
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger("edugenie")

class AIOrchestrator:
    def __init__(self):
        self.gemini_enabled = False
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_enabled = True
                logger.info("Google Gemini API successfully configured.")
            except Exception as e:
                logger.error(f"Error configuring Google Gemini: {e}")
        else:
            logger.warning("GEMINI_API_KEY is not set or using default value. Gemini queries will run in offline demo mode.")

    def query_gemini(self, prompt: str) -> str:
        """Queries the Google Gemini 1.5 Flash model."""
        if not self.gemini_enabled:
            return self._get_offline_response(prompt, "gemini")
            
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return self._clean_markdown_fencing(response.text.strip())
        except Exception as e:
            logger.error(f"Gemini Query Failed: {e}", exc_info=True)
            raise RuntimeError(f"Google Gemini model execution failed: {str(e)}")

    def query_lamini(self, prompt: str) -> str:
        """
        Queries the LaMini-Flan-T5 model via Hugging Face Inference API.
        Falls back to offline response generator if credentials are missing or API fails.
        """
        if (not settings.HF_API_KEY or 
            settings.HF_API_KEY == "your-huggingface-api-key-here" or 
            not settings.LAMINI_MODEL_URL):
            logger.info("Hugging Face API key not configured. Running LaMini in offline mock mode.")
            return self._get_offline_response(prompt, "lamini")

        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        payload = {"inputs": prompt, "options": {"wait_for_model": True}}
        
        try:
            response = requests.post(settings.LAMINI_MODEL_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                raw_text = ""
                if isinstance(result, list) and len(result) > 0:
                    raw_text = result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    raw_text = result.get("generated_text", "").strip()
                else:
                    raw_text = str(result)
                return self._clean_markdown_fencing(raw_text)
            else:
                logger.warning(f"LaMini HF API status {response.status_code}. Error: {response.text}")
                return self._get_offline_response(prompt, "lamini")
        except Exception as e:
            logger.warning(f"LaMini HF API query failed: {e}. Running offline mock.")
            return self._get_offline_response(prompt, "lamini")

    def parse_json_response(self, raw_text: str) -> dict:
        """Sanitizes raw AI response text and parses it into a valid JSON dictionary."""
        cleaned_text = self._clean_markdown_fencing(raw_text)
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Robust extraction: find first '{' and last '}'
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed parsing inner JSON block: {e}")
                
        # Robust extraction: find first '[' and last ']'
        start_idx = cleaned_text.find('[')
        end_idx = cleaned_text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx+1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed parsing inner JSON array: {e}")

        raise ValueError("AI response text is not valid parseable JSON.")

    def _clean_markdown_fencing(self, text: str) -> str:
        """Cleans markdown JSON code blocks from response string."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def _get_offline_response(self, prompt: str, provider: str) -> str:
        """Offline mock outputs supporting local credentials-free execution."""
        logger.info(f"Generating offline mock response for provider '{provider}' and prompt: '{prompt[:45]}...'")
        prompt_lower = prompt.lower()
        
        if "quiz" in prompt_lower:
            difficulty = "Intermediate"
            if "beginner" in prompt_lower:
                difficulty = "Beginner"
            elif "advanced" in prompt_lower:
                difficulty = "Advanced"
            return json.dumps({
                "topic": "Python Programming (Offline Mock)",
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the correct way to start a function in Python?",
                        "choices": ["function myFunc():", "def myFunc():", "create myFunc():", "class myFunc():"],
                        "correct_key": "B",
                        "explanation": "In Python, functions are defined using the 'def' keyword."
                    },
                    {
                        "id": 2,
                        "question": "Which of these data types is immutable in Python?",
                        "choices": ["List", "Dictionary", "Tuple", "Set"],
                        "correct_key": "C",
                        "explanation": "Tuples are immutable collections in Python."
                    },
                    {
                        "id": 3,
                        "question": "What is the output of len([1, 2, 3]) in Python?",
                        "choices": ["2", "3", "4", "Error"],
                        "correct_key": "B",
                        "explanation": "The len() function returns the number of items in a list, which is 3."
                    }
                ]
            })
            
        elif "roadmap" in prompt_lower or "roadmap_gen" in prompt_lower:
            return json.dumps({
                "topic": "FastAPI (Offline Mock)",
                "difficulty": "Beginner",
                "estimated_time": "4 Weeks (8 hours/week)",
                "overview": "A foundational study track mapping local development to API integrations.",
                "progression": {
                    "beginner": "Learn routing, parameters, and query schemas.",
                    "intermediate": "Learn SQLite ORM models, migrations, and session contexts.",
                    "advanced": "Implement CORS, async tasks, and secure cookie credentials."
                },
                "resources": {
                    "books": ["FastAPI Web Development (Author A)", "Web APIs with Python"],
                    "youtube": ["Tiangolo Tutorials", "FastAPI Crash Courses"],
                    "courses": ["Intro to FastAPI (Udemy)", "Advanced Python APIs (Coursera)"],
                    "certifications": ["Python Backend Engineer Certificate", "Hugging Face ML Ops Path"]
                },
                "suggested_projects": [
                    {
                        "title": "Task Organizer API",
                        "description": "Build a CRUD task manager exposing REST endpoints with SQLite storage."
                    },
                    {
                        "title": "Educational Dashboard Hub",
                        "description": "Construct an SPA workspace utilizing Fetch API and JWT authentication."
                    }
                ],
                "weekly_study_plan": [
                    {
                        "week": 1,
                        "focus": "FastAPI Installation and Setup",
                        "topics": ["pip install fastapi uvicorn", "first router file", "uvicorn run"],
                        "checkpoint_quiz_topic": "FastAPI Basics"
                    },
                    {
                        "week": 2,
                        "focus": "Pydantic Schema Validation",
                        "topics": ["Pydantic BaseModel", "field validation", "response serialization"],
                        "checkpoint_quiz_topic": "Pydantic Validation"
                    }
                ]
            })
            
        elif "summarize" in prompt_lower:
            return json.dumps({
                "summary": "This is a clean, structured offline summary. (Please set your GEMINI_API_KEY in the .env file to run live). The text discussed modular design, SQLite database constraints, and scalable FastAPI architecture configurations.",
                "length": "medium"
            })
            
        elif "explain" in prompt_lower or provider == "lamini":
            # Extract concept from prompt text if available
            concept = "the requested concept"
            if "explain the concept of '" in prompt_lower:
                start = prompt_lower.find("explain the concept of '") + len("explain the concept of '")
                end = prompt_lower.find("'", start)
                if start != -1 and end != -1:
                    concept = prompt[start:end]
            
            return f"### Concept Explanation: {concept} (Offline Mock)\n\n" \
                   f"**Definition**: A simulated educational explanation running in offline mode.\n\n" \
                   f"**Analogy**: Using draft layouts and drawings before building the final stone house.\n\n" \
                   f"**Key Summary**: Configure the API keys in your .env template to connect to the active LaMini model."
            
        else:
            # Q&A default fallback
            return json.dumps({
                "answer": "### EduGenie Offline Response (Demo Mode)\n\nHello! I am your AI learning co-pilot. I am currently running offline because the GEMINI_API_KEY is not configured.\n\n* **To fix this**: Copy `.env.example` to `.env` and fill in your keys.",
                "context_used": False
            })
