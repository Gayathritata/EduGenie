# File: app/services/prompt_manager.py
# Part of EduGenie SmartBridge Project

class PromptManager:

    # ─────────────────────────────────────────────────────────────────────────
    # QUESTION ANSWERING  (Gemini 2.0 Flash)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_qa_prompt(question: str, context: str = None) -> str:
        """
        Prompt for educational Q&A using Gemini.
        Returns structured JSON with answer, key concepts, and follow-up questions.
        """
        prompt = (
            "You are EduGenie, an expert AI teaching assistant specializing in educational guidance. "
            "A student has asked you a question. Your job is to provide a clear, accurate, and educationally "
            "rich answer that helps the student truly understand the topic.\n\n"
            "IMPORTANT: You MUST respond ONLY with a valid JSON object exactly matching the schema below. "
            "Do NOT include markdown code blocks (```json), extra text, or comments before or after the JSON.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "answer": "A detailed, well-structured answer using Markdown (## headings, **bold**, bullet lists, code blocks). Minimum 3 paragraphs.",\n'
            '  "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],\n'
            '  "follow_up_questions": ["Related question 1 the student should explore?", "Related question 2?"],\n'
            '  "context_used": true\n'
            "}\n\n"
        )
        if context:
            prompt += f"Reference Context (use this to inform your answer):\n---\n{context}\n---\n\n"
        else:
            prompt += '(No reference context provided — answer from your own knowledge. Set "context_used" to false)\n\n'
        prompt += f"Student's Question: {question}"
        return prompt

    # ─────────────────────────────────────────────────────────────────────────
    # CONCEPT EXPLANATION  (LaMini-Flan-T5)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_explain_prompt(concept: str, depth_level: str) -> str:
        """
        Prompt for structured concept explanation using LaMini-Flan-T5.
        LaMini has a smaller context window, so the prompt is directive but concise.
        The Python layer structures the raw output into the required sections.
        """
        level_instruction = {
            "beginner": (
                "Use simple language, everyday analogies, and avoid jargon. "
                "Assume the reader has zero prior knowledge."
            ),
            "intermediate": (
                "Use technical terminology with brief explanations. "
                "Include practical examples and code snippets where relevant."
            ),
            "advanced": (
                "Use expert-level depth. Include internal mechanisms, edge cases, "
                "performance characteristics, and comparative analysis."
            ),
        }.get(depth_level.lower(), "Use clear, educational language.")

        prompt = (
            f"You are an expert educator. Explain the concept of '{concept}' to a student. "
            f"{level_instruction} "
            "Your explanation MUST include all of the following sections in order: "
            "1) Simple Definition — what it is in one or two sentences. "
            "2) How It Works — the core mechanism or logic behind it. "
            "3) Real-World Analogy — relate it to an everyday situation. "
            "4) Example — a concrete code example or practical use case. "
            "5) Applications — where it is actually used in the real world. "
            "6) Advantages — what makes it useful or powerful. "
            "7) Disadvantages or Limitations — when NOT to use it or its weaknesses. "
            "8) One Interview Question — a typical interview question about this concept with a short answer. "
            "Be educational, accurate, and clear."
        )
        return prompt

    # ─────────────────────────────────────────────────────────────────────────
    # TEXT SUMMARIZATION  (Gemini 2.0 Flash)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_summarize_prompt(text: str, target_length: str) -> str:
        """
        Prompt for rich, structured text summarization using Gemini.
        Returns comprehensive JSON with summary, bullets, keywords, concepts, and revision notes.
        """
        length_guide = {
            "short":  "1-2 concise paragraphs",
            "medium": "3-4 paragraphs with moderate detail",
            "long":   "5+ paragraphs covering all major points thoroughly",
        }.get(target_length, "moderate length")

        prompt = (
            "You are EduGenie, an expert AI summarization engine for students and professionals. "
            "Summarize the text provided below into a structured, educational study guide.\n\n"
            "IMPORTANT: You MUST respond ONLY with a valid JSON object exactly matching the schema below. "
            "Do NOT include markdown code blocks, extra text, or comments before or after the JSON.\n\n"
            "JSON Schema:\n"
            "{\n"
            f'  "summary": "A prose summary of {length_guide}. Use clear, educational language.",\n'
            '  "bullet_points": [\n'
            '    "Key point 1 from the text",\n'
            '    "Key point 2 from the text",\n'
            '    "Key point 3 from the text"\n'
            "  ],\n"
            '  "important_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],\n'
            '  "key_concepts": [\n'
            '    {"concept": "Concept Name", "definition": "What it means in context"}\n'
            "  ],\n"
            '  "revision_notes": "A compact revision-ready note a student could use 1 hour before an exam.",\n'
            '  "length": "' + target_length + '"\n'
            "}\n\n"
            f"Target Length Profile: {target_length} ({length_guide})\n\n"
            f"Text to Summarize:\n{text}"
        )
        return prompt

    # ─────────────────────────────────────────────────────────────────────────
    # QUIZ GENERATION  (Gemini 2.0 Flash)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_quiz_prompt(topic: str, num_questions: int, difficulty: str = "Intermediate", context: str = None) -> str:
        """
        Prompt for high-quality multiple-choice quiz generation using Gemini.
        Each question has 4 choices, a correct key (A-D), and an educational explanation.
        """
        difficulty_guide = {
            "Beginner":     "Focus on foundational definitions, basic syntax, and core concepts. Questions should be accessible to someone new to the topic.",
            "Intermediate": "Include questions about practical application, common patterns, and moderate depth. Assume the student knows the basics.",
            "Advanced":     "Include questions about edge cases, internal mechanisms, performance trade-offs, and expert-level nuance.",
        }.get(difficulty, "Include a mix of conceptual and applied questions.")

        prompt = (
            f"You are EduGenie, an expert exam creator. Generate a rigorous multiple-choice quiz about '{topic}' "
            f"at the '{difficulty}' difficulty level with exactly {num_questions} questions.\n\n"
            f"Difficulty Guide: {difficulty_guide}\n\n"
            "Rules:\n"
            "- Each question MUST have exactly 4 choices labeled implicitly as index 0 (A), 1 (B), 2 (C), 3 (D).\n"
            "- correct_key MUST be exactly one of: 'A', 'B', 'C', or 'D'.\n"
            "- All 4 choices must be plausible; avoid obviously wrong distractors.\n"
            "- The explanation must be educational and explain WHY the correct answer is right.\n"
            "- Questions must be diverse and not repeat the same concept.\n\n"
            "IMPORTANT: You MUST respond ONLY with a valid JSON object exactly matching the schema below. "
            "Do NOT include markdown code blocks, extra text, or comments.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "topic": "Topic Name",\n'
            '  "difficulty": "Difficulty Level",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "question": "The full question text ending with a question mark?",\n'
            '      "choices": ["Choice A text", "Choice B text", "Choice C text", "Choice D text"],\n'
            '      "correct_key": "A",\n'
            '      "explanation": "Educational explanation of why Choice A is correct and why others are wrong."\n'
            "    }\n"
            "  ]\n"
            "}\n"
            f"Generate exactly {num_questions} question objects in the 'questions' array.\n\n"
        )
        if context:
            prompt += f"Reference Context (base your questions heavily on this text):\n---\n{context}\n---\n"
        return prompt

    # ─────────────────────────────────────────────────────────────────────────
    # LEARNING ROADMAP / RECOMMENDATION  (Gemini 2.0 Flash)
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def get_roadmap_prompt(topic: str, difficulty: str) -> str:
        """
        Prompt for a comprehensive, personalized learning roadmap using Gemini.
        Returns a full study guide with progression, resources, projects, and weekly plan.
        """
        weeks_guide = {
            "Beginner":     "8-12 weeks (7-10 hours/week)",
            "Intermediate": "6-8 weeks (10-12 hours/week)",
            "Advanced":     "4-6 weeks (12-15 hours/week)",
        }.get(difficulty, "8 weeks (10 hours/week)")

        prompt = (
            f"You are EduGenie, a personalized learning coach. Generate a comprehensive educational roadmap "
            f"for learning '{topic}' starting at the '{difficulty}' level.\n\n"
            "IMPORTANT: You MUST respond ONLY with a valid JSON object exactly matching the schema below. "
            "Do NOT include markdown code blocks, extra text, or comments.\n\n"
            "JSON Schema:\n"
            "{\n"
            '  "topic": "Topic Name",\n'
            '  "difficulty": "Difficulty Level",\n'
            f'  "estimated_time": "e.g., {weeks_guide}",\n'
            '  "overview": "2-3 sentence high-level description of what the learner will achieve.",\n'
            '  "progression": {\n'
            '    "beginner": "What to focus on as a complete beginner. Core foundations.",\n'
            '    "intermediate": "What to build on after foundations. Practical application.",\n'
            '    "advanced": "What to master for expert-level proficiency. Architecture and depth."\n'
            "  },\n"
            '  "resources": {\n'
            '    "books": ["Book Title 1 by Author Name", "Book Title 2 by Author Name"],\n'
            '    "youtube": ["Channel or Video Name 1", "Channel or Video Name 2", "Channel or Video Name 3"],\n'
            '    "courses": ["Course Name (Platform)", "Course Name (Platform)"],\n'
            '    "certifications": ["Certification Name (Issuing Body)", "Certification Name (Issuing Body)"]\n'
            "  },\n"
            '  "suggested_projects": [\n'
            "    {\n"
            '      "title": "Project Title",\n'
            '      "description": "What the project builds, what skills it reinforces, and approximate complexity."\n'
            "    }\n"
            "  ],\n"
            '  "weekly_study_plan": [\n'
            "    {\n"
            '      "week": 1,\n'
            '      "focus": "Theme or goal for this week",\n'
            '      "topics": ["Specific topic A", "Specific topic B", "Specific topic C"],\n'
            '      "checkpoint_quiz_topic": "Topic for self-assessment quiz at end of week"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Requirements:\n"
            "- Include at least 3 books, 3 YouTube channels/videos, 2 courses, and 2 certifications.\n"
            "- Include at least 3 suggested projects ranging from beginner to advanced complexity.\n"
            "- Include a weekly plan for the full estimated duration (at least 4 weeks).\n"
            "- All resource names must be real, accurate, and currently available.\n"
            "- Ensure the output conforms exactly to the JSON schema above."
        )
        return prompt
