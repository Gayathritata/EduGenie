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
                    model="gemini-2.0-flash-lite",
                    contents=prompt
                )
                self.gemini_available = True
                self.gemini_disabled_until = None

                return self._clean_markdown_fencing(response.text.strip())

            except Exception as e:
                error_str = str(e)
                if "400" in error_str and ("API_KEY_INVALID" in error_str or "API key not valid" in error_str):
                    logger.warning("Invalid API Key detected. Falling back to offline mode.")
                    self.gemini_enabled = False
                    return self._get_offline_response(prompt, "gemini")
                
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
        Topic: Data Structures — hardcoded for all features.
        """
        logger.info(
            f"Generating offline mock response for provider='{provider}' "
            f"prompt_preview='{prompt[:60]}...'"
        )
        prompt_lower = prompt.lower()

        # ── Q&A ──────────────────────────────────────────────────────────────
        if "student" in prompt_lower or ("edugenie, an expert" in prompt_lower and "quiz" not in prompt_lower and "roadmap" not in prompt_lower and "summarize" not in prompt_lower):
            return json.dumps({
                "answer": (
                    "## What are Data Structures?\n\n"
                    "A **Data Structure** is a specialized format for organizing, processing, retrieving, "
                    "and storing data so that it can be accessed and modified efficiently. "
                    "Data structures are one of the foundational pillars of computer science — "
                    "every algorithm you write depends on how well you choose and use them.\n\n"

                    "## Types of Data Structures\n\n"
                    "Data structures are broadly classified into two categories:\n\n"
                    "**1. Linear Data Structures** — Elements are arranged sequentially:\n"
                    "- **Array**: Fixed-size collection of elements of the same type, accessed by index. O(1) access.\n"
                    "- **Linked List**: Nodes connected via pointers. Efficient insertions/deletions (O(1)) but O(n) access.\n"
                    "- **Stack**: Last-In First-Out (LIFO). Used in undo operations, recursion, expression parsing.\n"
                    "- **Queue**: First-In First-Out (FIFO). Used in scheduling, BFS, print spoolers.\n\n"

                    "**2. Non-Linear Data Structures** — Elements arranged hierarchically or as networks:\n"
                    "- **Tree**: Hierarchical structure. Binary Search Tree gives O(log n) search.\n"
                    "- **Graph**: Nodes and edges. Used in maps, social networks, shortest-path algorithms.\n"
                    "- **Heap**: A complete binary tree satisfying the heap property. Used in priority queues.\n"
                    "- **Hash Table**: Key-value pairs with O(1) average-case lookup using hashing.\n\n"

                    "## Why Data Structures Matter\n\n"
                    "Choosing the right data structure can make the difference between an O(n\u00b2) "
                    "and an O(log n) solution. For example:\n\n"
                    "```python\n"
                    "# Using a list (O(n) lookup) vs set (O(1) lookup)\n"
                    "nums = [1, 2, 3, 4, 5]\n"
                    "print(3 in nums)        # O(n) — scans entire list\n\n"
                    "nums_set = {1, 2, 3, 4, 5}\n"
                    "print(3 in nums_set)    # O(1) — direct hash lookup\n"
                    "```\n\n"

                    "## Real-World Applications\n\n"
                    "| Data Structure | Real-World Use |\n"
                    "|----------------|----------------|\n"
                    "| Stack          | Browser back/forward, undo in editors |\n"
                    "| Queue          | OS process scheduling, message queues |\n"
                    "| Hash Table     | Python dictionaries, database indexing |\n"
                    "| Tree           | File systems, XML/JSON parsing, databases |\n"
                    "| Graph          | Google Maps, social networks, recommendation systems |"
                ),
                "key_concepts": [
                    "Array",
                    "Linked List",
                    "Stack (LIFO)",
                    "Queue (FIFO)",
                    "Binary Search Tree",
                    "Hash Table",
                    "Graph",
                    "Heap"
                ],
                "follow_up_questions": [
                    "What is the difference between a Stack and a Queue?",
                    "When would you use a Hash Table over a Binary Search Tree?",
                    "Explain how a Graph differs from a Tree.",
                    "What is the time complexity of common operations on a Linked List?",
                    "How does hashing work in a Hash Table?"
                ],
                "context_used": False
            })

        # ── Roadmap ──────────────────────────────────────────────────────────
        elif "roadmap" in prompt_lower or "learning path" in prompt_lower or "learning coach" in prompt_lower:
            return json.dumps({
                "topic": "Data Structures & Algorithms",
                "difficulty": "Beginner to Advanced",
                "estimated_time": "12 Weeks (10-12 hours/week)",
                "overview": (
                    "This roadmap is designed to take you from zero to mastery in Data Structures and Algorithms (DSA). "
                    "You will learn how to organize data efficiently using arrays, linked lists, stacks, queues, trees, "
                    "graphs, and hash tables, and apply algorithmic techniques like sorting, searching, recursion, "
                    "dynamic programming, and greedy methods to solve real-world and interview-level problems."
                ),
                "progression": {
                    "beginner": "Learn Python basics, arrays, strings, and Big-O time/space complexity. Solve simple problems using loops and conditionals.",
                    "intermediate": "Master linked lists, stacks, queues, recursion, binary search, sorting algorithms (merge sort, quick sort), and binary search trees.",
                    "advanced": "Study heaps, graphs (BFS, DFS, Dijkstra), dynamic programming, backtracking, tries, and segment trees."
                },
                "resources": {
                    "books": [
                        "Introduction to Algorithms (CLRS) by Cormen, Leiserson, Rivest & Stein",
                        "Data Structures and Algorithms in Python by Goodrich, Tamassia & Goldwasser",
                        "Cracking the Coding Interview by Gayle Laakmann McDowell",
                        "Grokking Algorithms by Aditya Bhargava",
                        "The Algorithm Design Manual by Steven Skiena"
                    ],
                    "youtube": [
                        "Abdul Bari — Algorithms (YouTube)",
                        "CodeWithHarry — Data Structures in Python",
                        "William Fiset — Graph Theory Algorithms",
                        "NeetCode — LeetCode Problem Walkthroughs",
                        "CS Dojo — Data Structures and Algorithms"
                    ],
                    "courses": [
                        "Data Structures and Algorithms Specialization (Coursera — UC San Diego)",
                        "Algorithms, Part I & II (Coursera — Princeton University)",
                        "Master the Coding Interview: Data Structures + Algorithms (Udemy)",
                        "The Last Algorithms Course You'll Need (Frontend Masters)",
                        "LeetCode DSA Study Plan (leetcode.com)"
                    ],
                    "certifications": [
                        "Google Technical Interview Certification (Grow with Google)",
                        "Python Institute — PCAP (includes data structures)",
                        "Meta Coding Interview Prep (Meta Careers)",
                        "AWS Developer Associate (uses DSA concepts)",
                        "HackerRank Problem Solving Certificate"
                    ]
                },
                "suggested_projects": [
                    {
                        "title": "Custom Linked List Library",
                        "description": "Implement a fully-featured singly and doubly linked list in Python with insert, delete, reverse, and cycle-detection methods."
                    },
                    {
                        "title": "Expression Evaluator using Stack",
                        "description": "Build a calculator that parses and evaluates infix/postfix mathematical expressions using a stack data structure."
                    },
                    {
                        "title": "Graph Pathfinder",
                        "description": "Implement BFS, DFS, and Dijkstra's shortest path on a weighted graph and visualize paths in the terminal."
                    },
                    {
                        "title": "LRU Cache Implementation",
                        "description": "Build a Least Recently Used (LRU) cache using a doubly linked list and hash map with O(1) get and put operations."
                    }
                ],
                "weekly_study_plan": [
                    {"week": 1, "focus": "Python Foundations & Big-O Notation",
                     "topics": ["Python Lists", "Tuples", "Dictionaries", "Big-O Time Complexity", "Space Complexity"],
                     "checkpoint_quiz_topic": "Big-O Notation"},
                    {"week": 2, "focus": "Arrays & Strings",
                     "topics": ["Static vs Dynamic Arrays", "Two-Pointer Technique", "Sliding Window", "String Manipulation"],
                     "checkpoint_quiz_topic": "Arrays"},
                    {"week": 3, "focus": "Linked Lists",
                     "topics": ["Singly Linked List", "Doubly Linked List", "Cycle Detection (Floyd)", "Reverse a Linked List"],
                     "checkpoint_quiz_topic": "Linked Lists"},
                    {"week": 4, "focus": "Stacks & Queues",
                     "topics": ["Stack (LIFO)", "Queue (FIFO)", "Deque", "Monotonic Stack", "BFS using Queue"],
                     "checkpoint_quiz_topic": "Stacks & Queues"},
                    {"week": 5, "focus": "Recursion & Backtracking",
                     "topics": ["Base Cases", "Recursive Tree", "Memoization", "N-Queens", "Maze Solver"],
                     "checkpoint_quiz_topic": "Recursion"},
                    {"week": 6, "focus": "Sorting & Searching",
                     "topics": ["Bubble Sort", "Merge Sort", "Quick Sort", "Binary Search", "Search in Rotated Array"],
                     "checkpoint_quiz_topic": "Sorting Algorithms"},
                    {"week": 7, "focus": "Hash Tables & Sets",
                     "topics": ["Hash Functions", "Collision Resolution", "Python dict internals", "Anagram Detection", "Two Sum"],
                     "checkpoint_quiz_topic": "Hash Tables"},
                    {"week": 8, "focus": "Trees",
                     "topics": ["Binary Tree", "Binary Search Tree", "Tree Traversals (In/Pre/Post)", "Height & Depth", "Balanced Trees"],
                     "checkpoint_quiz_topic": "Binary Trees"},
                    {"week": 9, "focus": "Heaps & Priority Queues",
                     "topics": ["Min-Heap", "Max-Heap", "Heapify", "Python heapq", "K Largest Elements"],
                     "checkpoint_quiz_topic": "Heaps"},
                    {"week": 10, "focus": "Graphs",
                     "topics": ["Graph Representations", "BFS", "DFS", "Topological Sort", "Cycle Detection"],
                     "checkpoint_quiz_topic": "Graph Traversal"},
                    {"week": 11, "focus": "Dynamic Programming",
                     "topics": ["Memoization", "Tabulation", "0/1 Knapsack", "Fibonacci", "Longest Common Subsequence"],
                     "checkpoint_quiz_topic": "Dynamic Programming"},
                    {"week": 12, "focus": "Advanced Topics & Mock Interviews",
                     "topics": ["Trie", "Segment Tree", "Dijkstra", "Greedy Algorithms", "Mock Interview Problems"],
                     "checkpoint_quiz_topic": "Final DSA Assessment"}
                ]
            })

        # ── Quiz ─────────────────────────────────────────────────────────────
        elif "quiz" in prompt_lower or "multiple-choice" in prompt_lower:
            difficulty = "Intermediate"
            if "beginner" in prompt_lower:
                difficulty = "Beginner"
            elif "advanced" in prompt_lower:
                difficulty = "Advanced"

            return json.dumps({
                "topic": "Data Structures",
                "difficulty": difficulty,
                "questions": [
                    {
                        "id": 1,
                        "question": "Which data structure follows the Last-In First-Out (LIFO) principle?",
                        "choices": ["Queue", "Stack", "Linked List", "Array"],
                        "correct_key": "B",
                        "explanation": "A Stack follows LIFO — the last element added is the first one removed. Common uses include undo operations, function call stacks, and expression parsing."
                    },
                    {
                        "id": 2,
                        "question": "What is the average-case time complexity for searching in a Hash Table?",
                        "choices": ["O(n)", "O(log n)", "O(1)", "O(n log n)"],
                        "correct_key": "C",
                        "explanation": "Hash Tables provide O(1) average-case lookup because the key is hashed directly to a bucket index. Worst case is O(n) due to collisions."
                    },
                    {
                        "id": 3,
                        "question": "Which traversal of a Binary Search Tree produces elements in sorted (ascending) order?",
                        "choices": ["Pre-order", "Post-order", "In-order", "Level-order"],
                        "correct_key": "C",
                        "explanation": "In-order traversal (Left \u2192 Root \u2192 Right) of a BST always produces elements in ascending sorted order."
                    },
                    {
                        "id": 4,
                        "question": "What is the time complexity of inserting an element at the beginning of a Singly Linked List?",
                        "choices": ["O(n)", "O(log n)", "O(n\u00b2)", "O(1)"],
                        "correct_key": "D",
                        "explanation": "Inserting at the head of a linked list is O(1) because you only need to update the head pointer — no shifting of elements is required."
                    },
                    {
                        "id": 5,
                        "question": "Which data structure is used internally by a recursive function call mechanism?",
                        "choices": ["Queue", "Heap", "Stack", "Graph"],
                        "correct_key": "C",
                        "explanation": "The call stack is used to keep track of function calls. Each function invocation pushes a frame; when it returns, the frame is popped."
                    },
                    {
                        "id": 6,
                        "question": "What is the space complexity of a graph represented as an Adjacency Matrix for V vertices?",
                        "choices": ["O(V)", "O(E)", "O(V\u00b2)", "O(V + E)"],
                        "correct_key": "C",
                        "explanation": "An adjacency matrix uses a V\u00d7V 2D array, resulting in O(V\u00b2) space. Adjacency lists are more space-efficient at O(V + E)."
                    },
                    {
                        "id": 7,
                        "question": "Which algorithm uses a Queue to traverse a graph level by level?",
                        "choices": ["Depth-First Search (DFS)", "Dijkstra's Algorithm", "Breadth-First Search (BFS)", "Prim's Algorithm"],
                        "correct_key": "C",
                        "explanation": "BFS uses a Queue (FIFO) to explore all neighbors before moving to the next level, making it ideal for shortest-path in unweighted graphs."
                    },
                    {
                        "id": 8,
                        "question": "In a Min-Heap, which element is always at the root?",
                        "choices": ["The maximum element", "The median element", "The minimum element", "A random element"],
                        "correct_key": "C",
                        "explanation": "In a Min-Heap, the root always holds the smallest element. Every parent node is smaller than or equal to its children."
                    },
                    {
                        "id": 9,
                        "question": "What is the worst-case time complexity of Quick Sort?",
                        "choices": ["O(n log n)", "O(n)", "O(n\u00b2)", "O(log n)"],
                        "correct_key": "C",
                        "explanation": "Quick Sort degrades to O(n\u00b2) when the pivot is always the smallest or largest element, e.g., on an already-sorted array with naive pivot selection."
                    },
                    {
                        "id": 10,
                        "question": "Which data structure is best suited for implementing a priority queue efficiently?",
                        "choices": ["Array", "Linked List", "Binary Heap", "Stack"],
                        "correct_key": "C",
                        "explanation": "A Binary Heap supports insert and extract-min/max in O(log n) time, making it the ideal underlying structure for a priority queue."
                    }
                ]
            })

        # ── Summarize ────────────────────────────────────────────────────────
        elif "summarize" in prompt_lower or "summarization engine" in prompt_lower:
            return json.dumps({
                "summary": (
                    "Data Structures are specialized formats for organizing, storing, and managing data in a computer "
                    "so that it can be accessed and modified efficiently. They form the backbone of every software "
                    "system and algorithm. The two primary categories are linear structures — such as arrays, linked "
                    "lists, stacks, and queues — and non-linear structures, which include trees, graphs, and hash tables.\n\n"
                    "Linear data structures store elements sequentially. Arrays offer O(1) random access but fixed size. "
                    "Linked lists allow dynamic memory allocation with efficient insertions and deletions. Stacks enforce "
                    "LIFO ordering critical for recursion and expression evaluation. Queues follow FIFO and underpin "
                    "scheduling and BFS algorithms.\n\n"
                    "Non-linear data structures model complex relationships. Binary Search Trees enable O(log n) operations. "
                    "Graphs represent networks and power applications like navigation and social networks. "
                    "Hash Tables provide O(1) average-case key-value lookup. Heaps are complete binary trees used in "
                    "priority queues and Dijkstra's algorithm."
                ),
                "bullet_points": [
                    "Data Structures organize and store data to enable efficient access, insertion, deletion, and modification.",
                    "Linear structures (Array, Linked List, Stack, Queue) store elements sequentially with different trade-offs.",
                    "Arrays give O(1) access by index; Linked Lists give O(1) insert/delete at the head.",
                    "Non-linear structures (Tree, Graph, Heap, Hash Table) model hierarchical or networked relationships.",
                    "Hash Tables provide O(1) average-case lookup; Binary Search Trees give O(log n) operations.",
                    "Choosing the correct data structure determines the time and space complexity of your algorithm.",
                    "Graphs power real-world applications like GPS navigation, social media, and web search.",
                    "Heaps are the backbone of priority queues, used in Dijkstra's shortest-path and heap sort algorithms."
                ],
                "important_keywords": [
                    "Array",
                    "Linked List",
                    "Stack",
                    "Queue",
                    "Binary Search Tree",
                    "Hash Table",
                    "Graph",
                    "Heap",
                    "Big-O Complexity",
                    "Dynamic Programming"
                ],
                "key_concepts": [
                    {
                        "concept": "Array",
                        "definition": "A fixed-size, contiguous block of memory storing elements of the same type, accessible in O(1) time by index."
                    },
                    {
                        "concept": "Linked List",
                        "definition": "A dynamic collection of nodes where each node stores data and a pointer to the next node, enabling O(1) insertion at the head."
                    },
                    {
                        "concept": "Stack",
                        "definition": "A linear data structure following Last-In First-Out (LIFO) order, used in recursion, undo features, and expression parsing."
                    },
                    {
                        "concept": "Hash Table",
                        "definition": "A data structure that maps keys to values using a hash function, providing O(1) average-case lookup, insert, and delete."
                    },
                    {
                        "concept": "Binary Search Tree (BST)",
                        "definition": "A tree where each node's left subtree has smaller values and right subtree has larger values, enabling O(log n) search."
                    },
                    {
                        "concept": "Graph",
                        "definition": "A collection of vertices and edges used to model networks, maps, social connections, and dependency systems."
                    }
                ],
                "revision_notes": (
                    "KEY COMPLEXITIES: "
                    "Array: Access O(1) | Insert/Delete O(n). "
                    "Linked List: Access O(n) | Insert/Delete at head O(1). "
                    "Stack/Queue: All operations O(1). "
                    "Hash Table: O(1) avg, O(n) worst. "
                    "BST: O(log n) avg, O(n) worst (unbalanced). "
                    "Heap: Insert O(log n) | Extract O(log n) | Build O(n). "
                    "CHOOSE BY USE: Fast lookup \u2192 Hash Table. Sorted data \u2192 BST. Priority \u2192 Heap. LIFO \u2192 Stack. FIFO \u2192 Queue."
                ),
                "length": "medium"
            })

        # ── Concept Explanation (LaMini / default fallback) ──────────────────
        else:
            return json.dumps({
                "explanation": (
                    "## Data Structures \u2014 Concept Explanation\n\n"
                    "**1. Simple Definition**\n"
                    "A Data Structure is a specialized way of organizing, storing, and managing data in a computer "
                    "so that it can be accessed, modified, and processed efficiently. It defines both the data itself, "
                    "the relationships between the data, and the operations that can be applied to it.\n\n"

                    "**2. How It Works**\n"
                    "A data structure defines rules for how data is laid out in memory and what operations are allowed. "
                    "For example, a Stack only allows add/remove from the top (LIFO), while an Array lets you access "
                    "any element directly by index in O(1) time.\n\n"

                    "**3. Real-World Analogy**\n"
                    "Think of a library:\n"
                    "\u2022 Books = data\n"
                    "\u2022 Shelves organized alphabetically = Array (direct access by position)\n"
                    "\u2022 A stack of books on a desk = Stack (last placed, first picked)\n"
                    "\u2022 A waiting list for a reserved book = Queue (first requested, first served)\n"
                    "\u2022 The library catalog network = Graph (books connected by references)\n\n"

                    "**4. Example**\n"
                    "```python\n"
                    "# Stack using Python list\n"
                    "stack = []\n"
                    "stack.append(10)    # Push\n"
                    "stack.append(20)\n"
                    "stack.append(30)\n"
                    "print(stack.pop())  # Pop \u2192 30 (LIFO)\n\n"
                    "# Hash Table using Python dict\n"
                    "phonebook = {'Alice': '9876543210', 'Bob': '9123456789'}\n"
                    "print(phonebook['Alice'])  # O(1) lookup\n"
                    "```\n\n"

                    "**5. Applications**\n"
                    "\u2022 Arrays & Hash Tables \u2192 Database indexing, caching (Redis)\n"
                    "\u2022 Stacks \u2192 Browser history, undo/redo, compiler parsing\n"
                    "\u2022 Queues \u2192 OS process scheduling, message brokers (Kafka, RabbitMQ)\n"
                    "\u2022 Trees \u2192 File systems, XML/JSON parsers, decision trees in ML\n"
                    "\u2022 Graphs \u2192 Google Maps, Facebook social graph, recommendation engines\n"
                    "\u2022 Heaps \u2192 Task schedulers, Dijkstra's algorithm, real-time leaderboards\n\n"

                    "**6. Advantages**\n"
                    "\u2022 Enables efficient data access and manipulation\n"
                    "\u2022 Reduces time and space complexity of algorithms\n"
                    "\u2022 Provides reusable, well-understood abstractions\n"
                    "\u2022 Essential for writing scalable, high-performance software\n\n"

                    "**7. Disadvantages / Limitations**\n"
                    "\u2022 Choosing the wrong structure causes poor performance\n"
                    "\u2022 Complex structures (B-Trees, Tries) have steep learning curves\n"
                    "\u2022 Dynamic structures use more memory per element due to pointers\n"
                    "\u2022 Hash Tables can degrade to O(n) with many collisions\n\n"

                    "**8. Interview Question**\n"
                    "Q: What is the difference between an Array and a Linked List?\n\n"
                    "A: An Array stores elements in contiguous memory with O(1) random access by index, "
                    "but insertion/deletion is O(n) due to shifting. A Linked List stores elements as nodes "
                    "with pointers \u2014 insertion/deletion at the head is O(1), but random access is O(n). "
                    "Use Arrays when you need fast access; use Linked Lists when you need frequent insertions/deletions."
                ),
                "key_concepts": [
                    "Array",
                    "Linked List",
                    "Stack (LIFO)",
                    "Queue (FIFO)",
                    "Binary Search Tree",
                    "Hash Table",
                    "Graph",
                    "Heap"
                ],
                "follow_up_questions": [
                    "What is the difference between a Stack and a Queue?",
                    "When would you use a Hash Table over a Binary Search Tree?",
                    "What are Linear vs Non-Linear Data Structures?",
                    "Explain how a Min-Heap works with an example.",
                    "What is the time complexity of BFS and DFS on a graph?"
                ],
                "context_used": False
            })