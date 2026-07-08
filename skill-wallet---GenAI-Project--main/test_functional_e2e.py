# File: test_functional_e2e.py
# Comprehensive functional testing suite for EduGenie

import sys
import os
import json
import unittest
from fastapi.testclient import TestClient

# Add workspace directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.models.query import Query
from app.models.response import AIResponse
from app.models.quiz import Quiz
from app.models.summary import Summary
from app.models.learning_path import LearningPath
from app.models.history import History
from app.models.saved_response import SavedResponse
from app.models.activity_log import ActivityLog

class TestEduGenieE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()
        
        # Prepare clean state for testing
        cls.username = "test_qa_student"
        cls.email = "qa_student@edugenie.com"
        cls.password = "SecuredPass123"
        
        # Cleanup if previously left over
        user = cls.db.query(User).filter(User.username == cls.username).first()
        if user:
            cls.db.delete(user)
            cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Cleanup
        user = cls.db.query(User).filter(User.username == cls.username).first()
        if user:
            cls.db.delete(user)
            cls.db.commit()
        cls.db.close()

    def test_01_health_check(self):
        print("Testing system health check endpoint...")
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("gemini_api_configured", data)
        self.assertIn("lamini_api_configured", data)

    def test_02_registration_validation(self):
        print("Testing registration validation rules...")
        # Invalid email
        response = self.client.post("/auth/register", json={
            "username": "bad",
            "email": "invalid-email-format",
            "password": "123"
        })
        self.assertEqual(response.status_code, 422)

        # Password too short (less than 6 characters)
        response = self.client.post("/auth/register", json={
            "username": "student",
            "email": "student@test.com",
            "password": "123"
        })
        self.assertEqual(response.status_code, 422)

        # Successful registration
        response = self.client.post("/auth/register", json={
            "username": self.username,
            "email": self.email,
            "password": self.password
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], self.username)
        self.assertEqual(data["email"], self.email)
        self.assertNotIn("password_hash", data)

        # Duplicate Registration
        response = self.client.post("/auth/register", json={
            "username": self.username,
            "email": "another@test.com",
            "password": self.password
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("already registered", response.json()["detail"])

    def test_03_login_and_session(self):
        print("Testing authentication credentials, cookie flow, and JWT...")
        # Invalid login password
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": "WrongPassword123"
        })
        self.assertEqual(response.status_code, 401)
        
        # Valid login
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        
        # Set token for subsequently protected requests
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Check that Cookie is set
        self.assertIn("access_token", response.cookies)
        cookie_val = response.cookies["access_token"]
        if cookie_val.startswith('"') and cookie_val.endswith('"'):
            cookie_val = cookie_val[1:-1]
        self.assertTrue(cookie_val.startswith("Bearer "))

        # Test cookie access (views redirection check)
        # Directly call with cookie session
        client_with_cookie = TestClient(app)
        client_with_cookie.cookies.set("access_token", f"Bearer {self.token}")
        
        profile_res = client_with_cookie.get("/profile")
        self.assertEqual(profile_res.status_code, 200)
        self.assertEqual(profile_res.json()["username"], self.username)

    def test_04_route_protection(self):
        print("Testing route protection policies...")
        # Access profile without auth
        clean_client = TestClient(app)
        response = clean_client.get("/profile")
        self.assertEqual(response.status_code, 401)

        # Access profile with wrong token
        response = clean_client.get("/profile", headers={"Authorization": "Bearer badtoken"})
        self.assertEqual(response.status_code, 401)

    def test_05_question_answering(self):
        print("Testing AI Question & Answering...")
        # Log in again to get session headers
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Empty question
        response = self.client.post("/qa", json={"question": ""}, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Valid question
        response = self.client.post("/qa", json={
            "question": "What is Python function nesting?",
            "context": "Context paragraph."
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("session_id", data)
        self.assertIn("key_concepts", data)
        self.assertIn("follow_up_questions", data)

    def test_06_concept_explanation(self):
        print("Testing Concept Explainer (LaMini/fallback)...")
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Topic Validation - too short
        response = self.client.post("/explain", json={"concept": "", "depth_level": "beginner"}, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Invalid depth
        response = self.client.post("/explain", json={"concept": "Recursion", "depth_level": "invalid-level"}, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Beginner explanation
        response = self.client.post("/explain", json={"concept": "Recursion", "depth_level": "beginner"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("explanation", response.json())
        self.assertIn("session_id", response.json())

    def test_07_quiz_arena(self):
        print("Testing Quiz Arena generation and grading...")
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate Quiz
        response = self.client.post("/quiz", json={
            "topic": "HTML Semantics",
            "num_questions": 3,
            "difficulty": "Intermediate"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        quiz_data = response.json()
        self.assertIn("quiz_id", quiz_data)
        self.assertEqual(len(quiz_data["questions"]), 3)
        
        # Verify correct answer key is stripped in the public output schema
        first_q = quiz_data["questions"][0]
        self.assertNotIn("correct_key", first_q)
        self.assertNotIn("explanation", first_q)

        # Grade Quiz
        submit_payload = {
            "quiz_id": quiz_data["quiz_id"],
            "answers": {
                "1": "B",
                "2": "A",
                "3": "D"
            }
        }
        grade_response = self.client.post("/quiz/submit", json=submit_payload, headers=headers)
        self.assertEqual(grade_response.status_code, 200)
        grade_data = grade_response.json()
        self.assertIn("score", grade_data)
        self.assertEqual(grade_data["total"], 3)
        self.assertEqual(len(grade_data["results"]), 3)
        self.assertIn("correct_key", grade_data["results"][0])
        self.assertIn("is_correct", grade_data["results"][0])
        self.assertIn("explanation", grade_data["results"][0])

    def test_08_summarize(self):
        print("Testing Summarizer module...")
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Text too short
        response = self.client.post("/summarize", json={"text": "short", "target_length": "medium"}, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Successful summary
        long_paragraph = (
            "FastAPI is a modern, fast (high-performance), web framework for building APIs "
            "with Python 3.8+ based on standard Python type hints. The key features are: "
            "Fast: Very high performance, on par with NodeJS and Go. "
            "Fast to code: Increase the speed to develop features by about 200% to 300%. "
            "Fewer bugs: Reduce about 40% of human induced errors. "
            "Intuitive: Great editor support. Completion everywhere. Less time debugging."
        )
        response = self.client.post("/summarize", json={
            "text": long_paragraph,
            "target_length": "medium"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("bullet_points", data)
        self.assertIn("important_keywords", data)
        self.assertIn("key_concepts", data)
        self.assertIn("revision_notes", data)

    def test_09_learning_recommendation(self):
        print("Testing Learning Path (learn) recommendation...")
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.post("/learn", json={
            "topic": "Machine Learning",
            "difficulty": "Beginner"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("roadmap_id", data)
        self.assertEqual(data["topic"], "Machine Learning")
        self.assertEqual(data["difficulty"], "Beginner")
        self.assertIn("weekly_study_plan", data["roadmap_data"])
        self.assertIn("progression", data["roadmap_data"])

    def test_10_bookmarks_and_history(self):
        print("Testing history timeline logs and bookmark save/delete...")
        response = self.client.post("/auth/login", json={
            "username": self.username,
            "password": self.password
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check history contains generated items from prior tests
        history_response = self.client.get("/history", headers=headers)
        self.assertEqual(history_response.status_code, 200)
        history_list = history_response.json()
        self.assertGreater(len(history_list), 0)
        
        # Test bookmarks save
        save_response = self.client.post("/save", json={
            "title": "My custom study bookmark",
            "category": "qa",
            "content": "This is sample bookmarked content details."
        }, headers=headers)
        self.assertEqual(save_response.status_code, 201)
        save_data = save_response.json()
        self.assertEqual(save_data["title"], "My custom study bookmark")
        
        # Get bookmarked list
        saved_list_res = self.client.get("/saved", headers=headers)
        self.assertEqual(saved_list_res.status_code, 200)
        saved_list = saved_list_res.json()
        self.assertTrue(any(item["id"] == save_data["id"] for item in saved_list))

        # Delete bookmark
        delete_response = self.client.delete(f"/save/{save_data['id']}", headers=headers)
        self.assertEqual(delete_response.status_code, 200)
        
        # Confirm deleted
        saved_list_res_2 = self.client.get("/saved", headers=headers)
        saved_list_2 = saved_list_res_2.json()
        self.assertFalse(any(item["id"] == save_data["id"] for item in saved_list_2))

    def test_11_logout(self):
        print("Testing user logout and cookie deletion...")
        response = self.client.post("/auth/logout")
        self.assertEqual(response.status_code, 200)
        # Check cookie deleted/expired
        cookie_val = response.cookies.get("access_token")
        self.assertTrue(cookie_val is None or cookie_val == "")

if __name__ == "__main__":
    unittest.main()
