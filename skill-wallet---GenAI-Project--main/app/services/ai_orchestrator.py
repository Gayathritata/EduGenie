# File: app/services/ai_orchestrator.py
# Part of EduGenie SmartBridge Project

from app.services import prompt_manager
from app.models import response
import logging
import time
import json
import requests
from google import genai
from app.config import settings
from datetime import datetime, timedelta
logger = logging.getLogger("edugenie")

# Retry configuration constants
_GEMINI_MAX_RETRIES = 2     # Maximum retry attempts for Gemini API calls
_LAMINI_MAX_RETRIES = 2     # Maximum retry attempts for LaMini HF API calls
_RETRY_BASE_DELAY = 1.5     # Base delay in seconds (doubles per retry)


class AIOrchestrator:

    def __init__(self):
        self.gemini_enabled = False
        self._client = None
        # Circuit Breaker
        self.gemini_available = True
        self.gemini_disabled_until = None
        gemini_key = settings.GEMINI_API_KEY
        if (
            gemini_key 
            and gemini_key != "your-gemini-api-key-here"
            and gemini_key != "YOUR_GOOGLE_API_KEY"
        ):
            try:
                self._client = genai.Client(api_key=gemini_key)
                self.gemini_enabled = True
                logger.info("Google Gemini API successfully configured.")
            except Exception as e:
                logger.error(f"Error configuring Google Gemini: {e}")
        else:
            logger.warning(
                "GEMINI_API_KEY is not set or using default value. "
                "Gemini queries will run in offline demo mode."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # GEMINI — Q&A, Quiz, Summary, Roadmap
    # ─────────────────────────────────────────────────────────────────────────
    def query_gemini(self, prompt: str) -> str:
        """
        Queries Google Gemini with intelligent retry logic.
        Retries only for temporary failures.
        Falls back to LaMini when quota is exhausted.
        """
        if (
            not self.gemini_available
            and self.gemini_disabled_until
            and datetime.now() < self.gemini_disabled_until
        ):
            logger.info("Gemini temporarily disabled. Using LaMini.")
            return self.query_lamini(prompt)

    # Re-enable Gemini after cooldown
        if (
            self.gemini_disabled_until
            and datetime.now() >= self.gemini_disabled_until
        ):
            self.gemini_available = True
            self.gemini_disabled_until = None
        if not self.gemini_enabled:
            return self._get_offline_response(prompt, "gemini")

        last_error = None

        for attempt in range(1, _GEMINI_MAX_RETRIES + 2):

            try:
                response = self._client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                self.gemini_available = True
                self.gemini_disabled_until = None

                return self._clean_markdown_fencing(response.text.strip())

            except Exception as e:

                last_error = e
                error_message = str(e)

            # ---------------------------------------------------------
            # CASE 1 : Daily Quota Exhausted (DO NOT RETRY)
            # ---------------------------------------------------------
            if any(keyword in error_message for keyword in [
                "RESOURCE_EXHAUSTED",
                "quota exceeded",
                "429",
                "GenerateRequestsPerDay",
                "GenerateRequestsPerMinute",
                "GenerateContentInputTokens",
                "QuotaFailure"
            ]):

                logger.warning(
                    "Gemini quota exhausted. Disabling Gemini for 15 minutes."
                )

                self.gemini_available = False
                self.gemini_disabled_until = datetime.now() + timedelta(minutes=15)

                logger.info("Using LaMini fallback.")
                return self.query_lamini(prompt)

            # ---------------------------------------------------------
            # CASE 2 : Invalid API Key (DO NOT RETRY)
            # ---------------------------------------------------------
            if (
                "401" in error_message
                or "UNAUTHENTICATED" in error_message
            ):

                logger.error("Invalid Gemini API Key.")

                return self.query_lamini(prompt)

            # ---------------------------------------------------------
            # CASE 3 : Permission Denied (DO NOT RETRY)
            # ---------------------------------------------------------
            if (
                "403" in error_message
                or "PERMISSION_DENIED" in error_message
            ):

                logger.error("Gemini permission denied.")

                return self.query_lamini(prompt)

            # ---------------------------------------------------------
            # CASE 4 : Retry only temporary failures
            # ---------------------------------------------------------
            if attempt <= _GEMINI_MAX_RETRIES:

                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))

                logger.warning(
                    f"[Gemini Retry] "
                    f"Attempt {attempt}/{_GEMINI_MAX_RETRIES + 1} | "
                    f"Delay={delay:.1f}s | "
                    f"Error={error_message}"
                )

                time.sleep(delay)

            else:

                logger.error(
                    "Gemini retries exhausted. Using LaMini.",
                    exc_info=True
                )

                return self.query_lamini(prompt)

        return self.query_lamini(prompt)

    # ─────────────────────────────────────────────────────────────────────────
    # LAMINI — Concept Explanation ONLY
    # ─────────────────────────────────────────────────────────────────────────
    def query_lamini(self, prompt: str) -> str:
        """
        Queries the LaMini-Flan-T5 model via the Hugging Face Inference API.
        Implements exponential-backoff retry on timeout or connection errors.
        Falls back to structured offline response if credentials are missing or all retries fail.
        """
        if (
            not settings.HF_API_KEY
            or settings.HF_API_KEY == "your-huggingface-api-key-here"
            or settings.HF_API_KEY == "YOUR_HUGGINGFACE_TOKEN"
            or not settings.LAMINI_MODEL_URL
        ):
            logger.info("Hugging Face API key not configured. Running LaMini in offline mock mode.")
            return self._get_offline_response(prompt, "lamini")

        headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "do_sample": True,
            },
            "options": {"wait_for_model": True},
        }

        last_error = None
        for attempt in range(1, _LAMINI_MAX_RETRIES + 2):  # attempts: 1, 2, 3
            try:
                response = requests.post(
                    settings.LAMINI_MODEL_URL,
                    headers=headers,
                    json=payload,
                    timeout=45,  # Increased to 45s — cold start can be slow
                )
                if response.status_code == 200:
                    result = response.json()
                    raw_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        raw_text = result[0].get("generated_text", "").strip()
                    elif isinstance(result, dict):
                        raw_text = result.get("generated_text", "").strip()
                    else:
                        raw_text = str(result)

                    # Strip the input prompt from the output if the model echoes it
                    if raw_text.startswith(prompt.strip()):
                        raw_text = raw_text[len(prompt.strip()):].strip()

                    return self._clean_markdown_fencing(raw_text) if raw_text else self._get_offline_response(prompt, "lamini")

                elif response.status_code in (503, 429):
                    # 503 = model loading, 429 = rate limit — both are retryable
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    if attempt <= _LAMINI_MAX_RETRIES:
                        delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        logger.warning(
                            f"LaMini attempt {attempt}/{_LAMINI_MAX_RETRIES + 1} got {response.status_code}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(f"LaMini all retries exhausted (status {response.status_code}). Falling back to offline.")
                        return self._get_offline_response(prompt, "lamini")
                else:
                    logger.warning(
                        f"LaMini HF API non-retryable status {response.status_code}. "
                        f"Error: {response.text[:200]}. Falling back to offline."
                    )
                    return self._get_offline_response(prompt, "lamini")

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt <= _LAMINI_MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"LaMini attempt {attempt}/{_LAMINI_MAX_RETRIES + 1} network error: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.warning(f"LaMini all retries exhausted after network error: {e}. Falling back to offline.")
                    return self._get_offline_response(prompt, "lamini")
            except Exception as e:
                logger.warning(f"LaMini unexpected error: {e}. Falling back to offline.")
                return self._get_offline_response(prompt, "lamini")

        return self._get_offline_response(prompt, "lamini")

    # ─────────────────────────────────────────────────────────────────────────
    # JSON PARSER
    # ─────────────────────────────────────────────────────────────────────────
    def parse_json_response(self, raw_text: str) -> dict:
        """
        Sanitizes raw AI response text and parses it into a valid JSON dictionary.
        Implements 3-level fallback extraction strategy.
        """
        cleaned_text = self._clean_markdown_fencing(raw_text)

        # Level 1: Direct parse
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass

        # Level 2: Extract first JSON object block
        start_idx = cleaned_text.find('{')
        end_idx = cleaned_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed parsing inner JSON block: {e}")

        # Level 3: Extract first JSON array block
        start_idx = cleaned_text.find('[')
        end_idx = cleaned_text.rfind(']')
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned_text[start_idx:end_idx + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed parsing inner JSON array: {e}")

        raise ValueError("AI response text is not valid parseable JSON.")

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────────────────────────────────────
    def _clean_markdown_fencing(self, text: str) -> str:
        """Strips markdown JSON/code fencing from AI response strings."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def _get_offline_response(self, prompt: str, provider: str) -> str:
        """
        Structured offline mock responses for credential-free local development.
        Matches the exact JSON schema expected by each endpoint's response model.
        """
        logger.info(
            f"Generating offline mock response for provider='{provider}' "
            f"prompt_preview='{prompt[:60]}...'"
        )
        prompt_lower = prompt.lower()

        # ── Roadmap ────────────────────────────────────────────────────────────
        if "roadmap" in prompt_lower or "learning path" in prompt_lower or "learning coach" in prompt_lower:
            return json.dumps({
                "topic": "FastAPI Web Development",
                "difficulty": "Beginner",
                "estimated_time": "8 Weeks (10 hours/week)",
                "overview": "A structured foundational track covering FastAPI routing, Pydantic validation, SQLite ORM, JWT authentication, and AI API integration. By the end you will be able to build and deploy a full-stack API backend.",
                "progression": {
                    "beginner": "Learn routing, path/query parameters, and Pydantic schemas. Build your first REST API.",
                    "intermediate": "Add SQLAlchemy ORM models, database sessions, and JWT authentication middleware.",
                    "advanced": "Implement async background tasks, CORS policies, file uploads, and WebSocket endpoints."
                },
                "resources": {
                    "books": [
                        "FastAPI by Sebastián Ramírez (Official Docs as a book)",
                        "Python Web Development with FastAPI by Bill Lubanovic",
                        "Building Data Science Applications with FastAPI by François Voron"
                    ],
                    "youtube": [
                        "FastAPI Full Course — Amigoscode",
                        "Build APIs with FastAPI — Tech with Tim",
                        "FastAPI Crash Course — Traversy Media"
                    ],
                    "courses": [
                        "REST APIs with FastAPI and Python (Udemy)",
                        "FastAPI — The Complete Course (Udemy)"
                    ],
                    "certifications": [
                        "Python Backend Engineer Certificate (LinkedIn Learning)",
                        "AWS Developer Associate (AWS)"
                    ]
                },
                "suggested_projects": [
                    {
                        "title": "Task Manager REST API",
                        "description": "Build a CRUD task management API with SQLite, Pydantic schemas, and JWT auth. Beginner-level complexity."
                    },
                    {
                        "title": "AI Study Assistant Backend",
                        "description": "Create a FastAPI backend that integrates Gemini API for Q&A, quiz generation, and summarization. Intermediate complexity."
                    },
                    {
                        "title": "Real-Time Chat API",
                        "description": "Implement a WebSocket-based chat system with user authentication and message history. Advanced complexity."
                    }
                ],
                "weekly_study_plan": [
                    {
                        "week": 1,
                        "focus": "FastAPI Fundamentals",
                        "topics": ["Installing FastAPI and Uvicorn", "Path and query parameters", "First router file"],
                        "checkpoint_quiz_topic": "FastAPI Basics"
                    },
                    {
                        "week": 2,
                        "focus": "Pydantic Data Validation",
                        "topics": ["Pydantic BaseModel", "Request and response schemas", "Field validation"],
                        "checkpoint_quiz_topic": "Pydantic and Schemas"
                    },
                    {
                        "week": 3,
                        "focus": "SQLAlchemy ORM",
                        "topics": ["SQLite engine setup", "ORM models and relationships", "Session dependency"],
                        "checkpoint_quiz_topic": "SQLAlchemy Basics"
                    },
                    {
                        "week": 4,
                        "focus": "Authentication and Security",
                        "topics": ["JWT token generation", "Password hashing with bcrypt", "Protected route dependencies"],
                        "checkpoint_quiz_topic": "JWT and Auth"
                    }
                ]
            })

        # ── Quiz ──────────────────────────────────────────────────────────────
        elif "quiz" in prompt_lower or "multiple-choice" in prompt_lower:
            difficulty = "Intermediate"
            if "beginner" in prompt_lower:
                difficulty = "Beginner"
            elif "advanced" in prompt_lower:
                difficulty = "Advanced"
            return json.dumps({
                "topic": "Python Programming",
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": "What keyword is used to define a function in Python?",
                        "choices": ["function", "def", "define", "lambda"],
                        "correct_key": "B",
                        "explanation": "In Python, the 'def' keyword is used to declare a function. 'lambda' creates anonymous functions but is not used for named function definitions."
                    },
                    {
                        "id": 2,
                        "question": "Which data type is immutable in Python?",
                        "choices": ["list", "dict", "set", "tuple"],
                        "correct_key": "D",
                        "explanation": "Tuples are immutable — their elements cannot be changed after creation. Lists, dicts, and sets are all mutable."
                    },
                    {
                        "id": 3,
                        "question": "What does the 'len()' function return for len([1, 2, 3])?",
                        "choices": ["2", "3", "4", "TypeError"],
                        "correct_key": "B",
                        "explanation": "len() returns the number of elements. The list [1, 2, 3] has 3 elements, so len() returns 3."
                    }
                ]
            })

        # ── Summarize ─────────────────────────────────────────────────────────
        elif "summarize" in prompt_lower or "summarization engine" in prompt_lower:
            return json.dumps({
                "summary": "This is a demonstration summary. The provided text covers key concepts in software architecture and API design. To generate a real summary, configure your GEMINI_API_KEY in the .env file.",
                "bullet_points": [
                    "The text introduces foundational software engineering principles.",
                    "Key architectural patterns are discussed with practical examples.",
                    "API design best practices including RESTful conventions are highlighted.",
                    "Database integration and ORM usage are covered in detail.",
                    "Security considerations including authentication and input validation are addressed."
                ],
                "important_keywords": ["API", "architecture", "database", "authentication", "validation"],
                "key_concepts": [
                    {"concept": "RESTful API", "definition": "An API architectural style that uses HTTP methods and stateless communication."},
                    {"concept": "ORM", "definition": "Object-Relational Mapping — a technique to query and manipulate databases using an object-oriented paradigm."}
                ],
                "revision_notes": "RESTful APIs use HTTP verbs (GET, POST, PUT, DELETE). ORMs map database tables to Python classes. JWT tokens authenticate users without server-side sessions. Pydantic validates request/response data.",
                "length": "medium"
            })

        # ── Concept Explanation (LaMini offline) ─────────────────────────────
        elif "explain" in prompt_lower or "educator" in prompt_lower or provider == "lamini":
            concept = "the requested concept"
            for marker in ["explain the concept of '", "explain '", "explaining '"]:
                if marker in prompt_lower:
                    start = prompt_lower.find(marker) + len(marker)
                    end = prompt_lower.find("'", start)
                    if start != -1 and end != -1:
                        concept = prompt[start:end]
                        break

            return (
                f"## {concept.title()} — Concept Explanation\n\n"
                f"**1. Simple Definition**\n"
                f"{concept.title()} is a fundamental concept in computer science and software engineering.\n\n "
                f"**2. How It Works**\n"
                f"It operates by combining structured inputs, defined rules, and logical processing to produce predictable outputs.\n\n"
                f"**3. Real-World Analogy**\n"
                f"Think of it like a recipe: you provide ingredients (inputs), follow steps (logic), and get a dish (output).\n\n"
                f"**4. Example**\n"
                f"```python\n# Example demonstrating {concept}\nresult = process({concept.lower().replace(' ', '_')}_input)\nprint(result)\n```\n\n"
                f"**5. Applications**\n"
                f"Used widely in web development, data processing, and system design patterns.\n\n"
                f"**6. Advantages**\n"
                f"- Improves code readability and maintainability\n"
                f"- Reduces duplication and promotes reuse\n"
                f"- Enables scalable and testable architectures\n\n"
                f"**7. Disadvantages / Limitations**\n"
                f"- Can add abstraction overhead if overused\n"
                f"- May have a learning curve for beginners\n\n"
                f"**8. Interview Question**\n"
                f"*Q: What is {concept} and when would you use it?*\n"
                f"A: {concept.title()} is used to [purpose]. You would choose it when [conditions]."
            )

        # ── Q&A default fallback ──────────────────────────────────────────────
        else:
            return json.dumps({
                "answer": (
                    "## EduGenie — Offline Demo Mode\n\n"
                    "Hello! I am your AI learning assistant, currently running in **offline demo mode** "
                    "because the `GEMINI_API_KEY` is not configured.\n\n"
                    "### How to Enable Live AI\n"
                    "1. Copy `.env.example` to `.env`\n"
                    "2. Add your Gemini API key: `GEMINI_API_KEY=your-actual-key`\n"
                    "3. Restart the server: `uvicorn app.main:app --reload`\n\n"
                    "Get your free Gemini API key at [aistudio.google.com](https://aistudio.google.com/)"
                ),
                "key_concepts": ["API Configuration", "Environment Variables", "Offline Mode"],
                "follow_up_questions": [
                    "How do I get a Gemini API key?",
                    "What can EduGenie do with a live API key?"
                ],
                "context_used": False
            })
