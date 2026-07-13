# File: app/services/ai_orchestrator.py
# Part of EduGenie SmartBridge Project

import logging
import time
import json
import requests
from google import genai
from app.config import settings

logger = logging.getLogger("edugenie")

# Retry configuration constants
_GEMINI_MAX_RETRIES = 2     # Maximum retry attempts for Gemini API calls
_LAMINI_MAX_RETRIES = 2     # Maximum retry attempts for LaMini HF API calls
_RETRY_BASE_DELAY = 1.5     # Base delay in seconds (doubles per retry)


class AIOrchestrator:
    def __init__(self):
        self.gemini_enabled = False
        self._client = None
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
        Queries Google Gemini 2.0 Flash with exponential-backoff retry.
        Max 2 retries on transient failures before raising RuntimeError.
        """
        if not self.gemini_enabled:
            return self._get_offline_response(prompt, "gemini")

        last_error = None
        for attempt in range(1, _GEMINI_MAX_RETRIES + 2):  # attempts: 1, 2, 3
            try:
                response = self._client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=prompt
                )
                return self._clean_markdown_fencing(response.text.strip())
            except Exception as e:
                error_str = str(e)
                if "400" in error_str and ("API_KEY_INVALID" in error_str or "API key not valid" in error_str):
                    logger.warning("Invalid API Key detected. Falling back to offline mode.")
                    self.gemini_enabled = False
                    return self._get_offline_response(prompt, "gemini")
                
                last_error = e
                if attempt <= _GEMINI_MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 1.5s, 3.0s
                    logger.warning(
                        f"Gemini attempt {attempt}/{_GEMINI_MAX_RETRIES + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Gemini all {_GEMINI_MAX_RETRIES + 1} attempts exhausted: {e}", exc_info=True)

        raise RuntimeError(f"Google Gemini model execution failed after retries: {str(last_error)}")

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
            topic = "FastAPI Web Development"
            topics_list = ["Installing FastAPI", "Pydantic", "SQLAlchemy", "JWT"]
            if "machine learning" in prompt_lower:
                topic = "Machine Learning"
                topics_list = ["Linear Regression", "Scikit-Learn", "Model Evaluation", "Neural Networks"]
            elif "deep learning" in prompt_lower:
                topic = "Deep Learning"
                topics_list = ["Backpropagation", "CNNs", "RNNs", "Transformers"]
            elif "knn" in prompt_lower:
                topic = "K-Nearest Neighbors (KNN)"
                topics_list = ["Distance Metrics", "Choosing K", "Curse of Dimensionality", "KD-Trees"]
            elif "kubernetes" in prompt_lower:
                topic = "Kubernetes"
                topics_list = ["Pods and Nodes", "Deployments", "Services", "Ingress"]
            elif "python" in prompt_lower and "fastapi" not in prompt_lower and "fast api" not in prompt_lower:
                topic = "Python Programming"
                topics_list = ["Syntax Basics", "Data Structures", "OOP", "Decorators"]

            return json.dumps({
                "topic": f"{topic} (Offline Demo)",
                "difficulty": "Beginner",
                "estimated_time": "8 Weeks (10 hours/week)",
                "overview": f"A structured foundational track covering {topic}. By the end you will be able to build and deploy applications.",
                "progression": {
                    "beginner": f"Learn basic concepts of {topic}.",
                    "intermediate": f"Build your first projects in {topic}.",
                    "advanced": f"Master advanced patterns in {topic}."
                },
                "resources": {
                    "books": [f"Intro to {topic}", f"Advanced {topic}"],
                    "youtube": [f"{topic} Crash Course"],
                    "courses": [f"{topic} Masterclass (Udemy)"],
                    "certifications": [f"Certified {topic} Specialist"]
                },
                "suggested_projects": [
                    {
                        "title": f"{topic} Basics Project",
                        "description": f"A beginner project to understand {topic}."
                    },
                    {
                        "title": f"Advanced {topic} Implementation",
                        "description": f"Complex project leveraging {topic}."
                    }
                ],
                "weekly_study_plan": [
                    {
                        "week": i + 1,
                        "focus": f"{topic} Phase {i + 1}",
                        "topics": [t],
                        "checkpoint_quiz_topic": t
                    } for i, t in enumerate(topics_list)
                ]
            })

        # ── Quiz ──────────────────────────────────────────────────────────────
        elif "quiz" in prompt_lower or "multiple-choice" in prompt_lower:
            difficulty = "Intermediate"
            if "beginner" in prompt_lower:
                difficulty = "Beginner"
            elif "advanced" in prompt_lower:
                difficulty = "Advanced"

            topic = "FastAPI"
            q1 = "What is FastAPI?"
            a1 = "A Python web framework"
            if "machine learning" in prompt_lower:
                topic = "Machine Learning"
                q1 = "What is Overfitting?"
                a1 = "When a model learns training data too well"
            elif "deep learning" in prompt_lower:
                topic = "Deep Learning"
                q1 = "What is a CNN?"
                a1 = "Convolutional Neural Network"
            elif "knn" in prompt_lower:
                topic = "KNN"
                q1 = "What does K represent in KNN?"
                a1 = "Number of nearest neighbors"
            elif "kubernetes" in prompt_lower:
                topic = "Kubernetes"
                q1 = "What is a Pod?"
                a1 = "The smallest deployable unit in Kubernetes"
            elif "python" in prompt_lower and "fastapi" not in prompt_lower and "fast api" not in prompt_lower:
                topic = "Python"
                q1 = "What keyword defines a function?"
                a1 = "def"

            return json.dumps({
                "topic": f"{topic} (Offline Demo)",
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": q1,
                        "choices": [a1, "Incorrect A", "Incorrect B", "Incorrect C"],
                        "correct_key": "A",
                        "explanation": f"The correct answer is {a1}."
                    },
                    {
                        "id": 2,
                        "question": f"Which is a key concept of {topic}?",
                        "choices": ["Wrong", "Correct Concept", "False", "None"],
                        "correct_key": "B",
                        "explanation": f"Correct Concept is essential in {topic}."
                    }
                ]
            })

        # ── Summarize ─────────────────────────────────────────────────────────
        elif "summarize" in prompt_lower or "summarization engine" in prompt_lower:
            # Extract the original text if possible
            original_text = ""
            if "Text to Summarize:\n" in prompt:
                original_text = prompt.split("Text to Summarize:\n")[-1].strip()
            
            # Split the text into bullet points using dot
            if original_text:
                bullet_points = [p.strip() + "." for p in original_text.split(".") if p.strip()]
            else:
                bullet_points = [
                    "The text introduces foundational software engineering principles.",
                    "Key architectural patterns are discussed with practical examples."
                ]
                
            return json.dumps({
                "summary": "This is an offline demonstration summary. To generate a real AI summary, configure your GEMINI_API_KEY in the .env file.",
                "bullet_points": bullet_points,
                "important_keywords": ["offline", "demo", "summarizer"],
                "key_concepts": [
                    {"concept": "Offline Mode", "definition": "Fallback mode when API key is missing."}
                ],
                "revision_notes": "Generated from splitting your input text by dots.",
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
                f"## {concept.title()} — Concept Explanation (Offline Demo)\n\n"
                f"**1. Simple Definition**\n"
                f"{concept.title()} is a fundamental concept in computer science and software engineering. "
                f"(Configure your HF_API_KEY in .env to get a live AI-generated explanation.)\n\n"
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
