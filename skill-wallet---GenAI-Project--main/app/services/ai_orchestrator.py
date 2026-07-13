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

        # ── Roadmap ──────────────────────────────────────────────────────────
        if "roadmap" in prompt_lower or "learning path" in prompt_lower or "learning coach" in prompt_lower:
            return json.dumps({
                "topic": "Python Full Stack Development",
                "difficulty": "Beginner to Advanced",
                "estimated_time": "16 Weeks (12-15 hours/week)",
                "overview": (
                    "This roadmap is designed to help learners become industry-ready "
                    "Python Full Stack Developers. It covers frontend development, "
                    "backend development with Python and FastAPI, database management, "
                    "authentication, REST APIs, deployment, version control, and "
                    "real-world project development."
                ),

                "progression": {
                    "beginner": "Learn Python fundamentals, HTML5, CSS3, JavaScript, Git, and basic SQL.",
                    "intermediate": "Build REST APIs using FastAPI, work with SQLite/MySQL, SQLAlchemy ORM, authentication using JWT, and consume APIs using JavaScript.",
                    "advanced": "Develop complete full-stack applications, integrate AI APIs, deploy applications on cloud platforms, implement Docker, CI/CD pipelines, testing, and optimize application performance."
                },

                "resources": {
                    "books": [
                        "Python Crash Course by Eric Matthes",
                        "Automate the Boring Stuff with Python by Al Sweigart",
                        "HTML & CSS: Design and Build Websites by Jon Duckett",
                        "JavaScript: The Definitive Guide by David Flanagan",
                        "FastAPI Official Documentation"
                    ],
                    "youtube": [
                        "CodeWithHarry - Python Full Course",
                        "Apna College - Full Stack Development",
                        "Bro Code - Python Programming",
                        "Traversy Media - HTML CSS JavaScript",
                        "Tech With Tim - FastAPI Tutorial"
                    ],
                    "courses": [
                        "Python for Everybody (Coursera)",
                        "Complete Python Bootcamp (Udemy)",
                        "Full Stack Web Development (Udemy)",
                        "FastAPI Complete Guide",
                        "Meta Backend Developer Professional Certificate"
                    ],
                    "certifications": [
                        "Python Institute - PCEP",
                        "Meta Backend Developer",
                        "AWS Cloud Practitioner",
                        "Google Associate Cloud Engineer",
                        "Microsoft Azure Fundamentals"
                    ]
                },

                "suggested_projects": [
                    {
                        "title": "Student Management System",
                        "description": "Build a CRUD application using FastAPI, SQLite, HTML, CSS and JavaScript."
                    },
                    {
                        "title": "AI Learning Assistant",
                        "description": "Develop an AI-powered educational assistant using FastAPI, Gemini API, SQLite and JavaScript."
                    },
                    {
                        "title": "E-Commerce Website",
                        "description": "Create a complete shopping website with authentication, product catalog, cart, payment workflow and admin dashboard."
                    },
                    {
                        "title": "Job Portal",
                        "description": "Build a recruitment platform with authentication, resume upload, job posting and application tracking."
                    }
                ],

                "weekly_study_plan": [
                    {"week": 1, "focus": "Python Programming Fundamentals",
                     "topics": ["Variables", "Data Types", "Operators", "Loops", "Functions", "Modules"],
                     "checkpoint_quiz_topic": "Python Basics"},
                    {"week": 2, "focus": "Object-Oriented Programming",
                     "topics": ["Classes", "Objects", "Inheritance", "Polymorphism", "Exception Handling"],
                     "checkpoint_quiz_topic": "OOP Concepts"},
                    {"week": 3, "focus": "Frontend Development",
                     "topics": ["HTML5", "CSS3", "Responsive Design", "JavaScript ES6"],
                     "checkpoint_quiz_topic": "Frontend Fundamentals"},
                    {"week": 4, "focus": "Advanced JavaScript",
                     "topics": ["DOM Manipulation", "Fetch API", "Async/Await", "JSON"],
                     "checkpoint_quiz_topic": "JavaScript"},
                    {"week": 5, "focus": "Database Fundamentals",
                     "topics": ["SQLite", "SQL Queries", "Relationships", "Normalization"],
                     "checkpoint_quiz_topic": "Database Basics"},
                    {"week": 6, "focus": "FastAPI Framework",
                     "topics": ["Routing", "Pydantic", "Request Validation", "Response Models"],
                     "checkpoint_quiz_topic": "FastAPI"},
                    {"week": 7, "focus": "SQLAlchemy ORM",
                     "topics": ["Models", "Relationships", "CRUD Operations", "Database Sessions"],
                     "checkpoint_quiz_topic": "SQLAlchemy"},
                    {"week": 8, "focus": "Authentication",
                     "topics": ["JWT", "Password Hashing", "Protected Routes", "Role-Based Access"],
                     "checkpoint_quiz_topic": "Authentication"},
                    {"week": 9, "focus": "REST API Development",
                     "topics": ["CRUD APIs", "Status Codes", "Exception Handling", "API Testing"],
                     "checkpoint_quiz_topic": "REST APIs"},
                    {"week": 10, "focus": "AI Integration",
                     "topics": ["Gemini API", "Prompt Engineering", "JSON Responses", "Error Handling"],
                     "checkpoint_quiz_topic": "Generative AI"},
                    {"week": 11, "focus": "Git & GitHub",
                     "topics": ["Git Basics", "Branches", "Pull Requests", "Version Control"],
                     "checkpoint_quiz_topic": "Git"},
                    {"week": 12, "focus": "Deployment",
                     "topics": ["Render", "Railway", "Vercel", "Environment Variables"],
                     "checkpoint_quiz_topic": "Deployment"},
                    {"week": 13, "focus": "Mini Project",
                     "topics": ["Student Management System"],
                     "checkpoint_quiz_topic": "Mini Project"},
                    {"week": 14, "focus": "Intermediate Project",
                     "topics": ["AI Learning Assistant"],
                     "checkpoint_quiz_topic": "AI Project"},
                    {"week": 15, "focus": "Major Project",
                     "topics": ["Full Stack Web Application"],
                     "checkpoint_quiz_topic": "Major Project"},
                    {"week": 16, "focus": "Interview Preparation",
                     "topics": ["DSA", "SQL", "Python", "System Design", "Mock Interviews"],
                     "checkpoint_quiz_topic": "Final Assessment"}
                ]
            })

        # ── Quiz ─────────────────────────────────────────────────────────────
        elif "quiz" in prompt_lower or "multiple-choice" in prompt_lower:
            difficulty = "Intermediate"

            if "beginner" in prompt_lower:
                difficulty = "Beginner"
            elif "advanced" in prompt_lower:
                difficulty = "Advanced"

            # FIX: this return was previously dedented out of the elif block,
            # which broke the if/elif/elif chain below with a SyntaxError.
            return json.dumps({
                "topic": "Python Programming",
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": "Which keyword is used to define a function in Python?",
                        "choices": ["function", "define", "def", "func"],
                        "correct_key": "C",
                        "explanation": "The 'def' keyword is used to define a function in Python."
                    },
                    {
                        "id": 2,
                        "question": "Which of the following is a mutable data type in Python?",
                        "choices": ["Tuple", "String", "List", "Integer"],
                        "correct_key": "C",
                        "explanation": "Lists are mutable, meaning their elements can be modified after creation."
                    },
                    {
                        "id": 3,
                        "question": "What is the output of print(len([10, 20, 30, 40]))?",
                        "choices": ["3", "4", "5", "Error"],
                        "correct_key": "B",
                        "explanation": "The list contains four elements, so len() returns 4."
                    },
                    {
                        "id": 4,
                        "question": "Which loop is used to iterate over a sequence in Python?",
                        "choices": ["repeat loop", "foreach loop", "for loop", "until loop"],
                        "correct_key": "C",
                        "explanation": "The 'for' loop is commonly used to iterate over lists, tuples, strings, and other sequences."
                    },
                    {
                        "id": 5,
                        "question": "Which symbol is used to write comments in Python?",
                        "choices": ["//", "/* */", "#", "--"],
                        "correct_key": "C",
                        "explanation": "Single-line comments in Python begin with the '#' symbol."
                    }
                ]
            })

        # ── Summarize ────────────────────────────────────────────────────────
        elif "summarize" in prompt_lower or "summarization engine" in prompt_lower:
            return json.dumps({
                "summary": (
                    "Robotics in Artificial Intelligence and Machine Learning combines intelligent algorithms "
                    "with robotic systems to enable machines to perceive their environment, learn from data, "
                    "make decisions, and perform tasks autonomously. AI provides reasoning, planning, and "
                    "decision-making capabilities, while Machine Learning enables robots to improve their "
                    "performance through experience. Robotics powered by AI and ML is widely used in "
                    "manufacturing, healthcare, agriculture, autonomous vehicles, space exploration, "
                    "and smart warehouses to improve efficiency, accuracy, and safety."
                ),
                "bullet_points": [
                    "Robotics integrates Artificial Intelligence and Machine Learning to build intelligent autonomous systems.",
                    "AI enables robots to make decisions, recognize objects, and solve complex problems.",
                    "Machine Learning allows robots to learn from data and continuously improve their performance.",
                    "Computer Vision helps robots identify objects, people, and surroundings using cameras and sensors.",
                    "Applications include healthcare, manufacturing, agriculture, autonomous vehicles, logistics, and space exploration."
                ],
                "important_keywords": [
                    "Robotics",
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Computer Vision",
                    "Automation",
                    "Sensors",
                    "Autonomous Systems",
                    "Deep Learning"
                ],
                "key_concepts": [
                    {
                        "concept": "Robotics",
                        "definition": "The branch of engineering that designs, develops, and operates intelligent machines capable of performing tasks automatically."
                    },
                    {
                        "concept": "Artificial Intelligence",
                        "definition": "The capability of machines to simulate human intelligence such as learning, reasoning, and decision making."
                    },
                    {
                        "concept": "Machine Learning",
                        "definition": "A subset of AI that enables systems to learn patterns from data without being explicitly programmed."
                    },
                    {
                        "concept": "Computer Vision",
                        "definition": "A field of AI that enables robots to interpret and understand visual information from images and videos."
                    }
                ],
                "revision_notes": (
                    "Robotics + AI + Machine Learning = Intelligent Autonomous Systems. "
                    "AI enables decision making, ML enables learning from experience, and Computer Vision enables "
                    "robots to understand their surroundings. Major applications include healthcare, manufacturing, "
                    "agriculture, autonomous vehicles, and space exploration."
                ),
                "length": "medium"
            })

        # ── Concept Explanation (default / LaMini fallback) ────────────────────
        # NOTE: In the pasted source, this branch's opening (the condition,
        # `return json.dumps({`, the "explanation" key, and the "**Definition**"
        # / start of "**Types**" text) was missing — the fragment picked up
        # mid-list at "Linked List". I've reconstructed a plausible opening
        # below so the file parses; verify this against your actual source,
        # since I inferred the missing lines rather than recovering them.
        else:
            return json.dumps({
                "explanation": (
                    "**Definition**\n"
                    "A Data Structure is a specialized format for organizing, processing, "
                    "retrieving, and storing data so that it can be used efficiently.\n\n"
                    "**Types**\n"
                    "• Array\n"
                    "• Linked List\n"
                    "• Stack (LIFO)\n"
                    "• Queue (FIFO)\n"
                    "• Tree\n"
                    "• Graph\n"
                    "• Hash Table\n\n"

                    "**Advantages**\n"
                    "• Fast data access\n"
                    "• Efficient memory usage\n"
                    "• Better program performance\n"
                    "• Easier implementation of algorithms\n"
                    "• Supports scalable applications\n\n"

                    "**Disadvantages**\n"
                    "• Some structures are complex to implement.\n"
                    "• Choosing the wrong data structure can reduce performance.\n"
                    "• Dynamic structures may consume additional memory.\n\n"

                    "**Applications**\n"
                    "• Database Management Systems\n"
                    "• Operating Systems\n"
                    "• Artificial Intelligence\n"
                    "• Search Engines\n"
                    "• Web Browsers\n"
                    "• Compiler Design\n"
                    "• Networking\n\n"

                    "**Interview Question**\n"
                    "Q: What is a Data Structure and why is it important?\n\n"
                    "Answer: A Data Structure is a method of organizing and storing data "
                    "efficiently so that operations like searching, insertion, deletion, "
                    "and sorting can be performed quickly. Choosing the appropriate data "
                    "structure improves application performance and memory utilization."
                ),
                "key_concepts": [
                    "Data Structure",
                    "Array",
                    "Linked List",
                    "Stack",
                    "Queue",
                    "Tree",
                    "Graph",
                    "Hash Table"
                ],
                "follow_up_questions": [
                    "What are Linear and Non-Linear Data Structures?",
                    "Explain Stack with a real-world example.",
                    "Explain Queue with a real-world example.",
                    "Difference between Array and Linked List?"
                ],
                "context_used": False
            })