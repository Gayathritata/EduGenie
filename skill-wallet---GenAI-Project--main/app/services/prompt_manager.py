# File: app/services/prompt_manager.py
# Part of EduGenie SmartBridge Project

class PromptManager:
    @staticmethod
    def get_qa_prompt(question: str, context: str = None) -> str:
        """Create a prompt for Q&A requesting JSON responses."""
        prompt = (
            "You are an expert AI teaching assistant. Provide a detailed, easy-to-understand response "
            "to the student's question.\n"
            "You MUST respond ONLY with a valid JSON object matching the following schema. "
            "Do not include markdown code block syntax (like ```json) or any pre/post text.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "answer": "Detailed answer formatted with Markdown (headings, bold, lists)",\n'
            '  "context_used": true\n'
            "}\n\n"
        )
        if context:
            prompt += f"Reference Context:\n---\n{context}\n---\n"
        prompt += f"Student's Question: {question}"
        return prompt

    @staticmethod
    def get_explain_prompt(concept: str, depth_level: str) -> str:
        """Create a prompt for concept explanation. Suitable for LaMini-Flan-T5."""
        # Since LaMini is smaller, we keep the prompt clear, simple, and direct.
        # We will wrap its text response into a structured JSON dictionary in Python.
        prompt = (
            f"Explain the concept of '{concept}' for a student at the '{depth_level}' level. "
            "Include a simple definition, a clear analogy, and a brief summary. "
            "Be educational and clear."
        )
        return prompt

    @staticmethod
    def get_summarize_prompt(text: str, target_length: str) -> str:
        """Create a prompt for text summarization requesting JSON responses."""
        prompt = (
            "You are an AI summarization tool. Summarize the text provided below.\n"
            "You MUST respond ONLY with a valid JSON object matching the following schema. "
            "Do not include markdown code blocks or extra text.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "summary": "Summary text matching the requested length profile",\n'
            '  "length": "short/medium/long"\n'
            "}\n\n"
            f"Target Length Profile: {target_length}\n"
            f"Text to Summarize:\n{text}"
        )
        return prompt

    @staticmethod
    def get_quiz_prompt(topic: str, num_questions: int, difficulty: str = "Intermediate") -> str:
        """Create a prompt to generate a multiple-choice quiz in JSON format with difficulty level."""
        prompt = (
            f"Generate a multiple-choice quiz about '{topic}' at the '{difficulty}' difficulty level with exactly {num_questions} questions.\n"
            "You MUST respond ONLY with a valid JSON object matching the following schema. "
            "Do not include markdown code blocks or surrounding text, just the raw JSON.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "topic": "Topic Name",\n'
            '  "difficulty": "Difficulty Level",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "question": "The question text?",\n'
            '      "choices": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "correct_key": "A",\n'
            '      "explanation": "Why Option A is correct."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Note: choices must be exactly 4 strings. correct_key must be 'A', 'B', 'C', or 'D', corresponding to the choices indexes."
        )
        return prompt

    @staticmethod
    def get_roadmap_prompt(topic: str, difficulty: str) -> str:
        """Create a prompt to generate a comprehensive learning recommendation path in JSON format."""
        prompt = (
            f"Generate a comprehensive educational learning path and recommendation guide for learning '{topic}' at a '{difficulty}' starting level.\n"
            "You MUST respond ONLY with a valid JSON object matching the following schema. "
            "Do not include markdown code blocks or surrounding text, just the raw JSON.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "topic": "Topic Name",\n'
            '  "difficulty": "Difficulty Level",\n'
            '  "estimated_time": "e.g., 8 Weeks (10 hours/week)",\n'
            '  "overview": "High-level summary of recommendations",\n'
            '  "progression": {\n'
            '    "beginner": "Core focus for beginner phase",\n'
            '    "intermediate": "Core focus for intermediate phase",\n'
            '    "advanced": "Core focus for advanced phase"\n'
            '  },\n'
            '  "resources": {\n'
            '    "books": ["Book Title 1 (Author)", "Book Title 2"],\n'
            '    "youtube": ["Channel/Video Name 1", "Channel/Video Name 2"],\n'
            '    "courses": ["Course Name 1 (Provider)", "Course Name 2"],\n'
            '    "certifications": ["Certification Name 1 (Issuer)", "Certification Name 2"]\n'
            '  },\n'
            '  "suggested_projects": [\n'
            '    {\n'
            '      "title": "Project Name",\n'
            '      "description": "What to build and how it reinforces learning"\n'
            '    }\n'
            '  ],\n'
            '  "weekly_study_plan": [\n'
            '    {\n'
            '      "week": 1,\n'
            '      "focus": "Week theme/goal",\n'
            '      "topics": ["Topic A", "Topic B"],\n'
            '      "checkpoint_quiz_topic": "Quiz Topic for Week 1"\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "Ensure the output conforms exactly to this JSON schema."
        )
        return prompt
