# File: test_backend.py
# Verification script for EduGenie Backend

import sys
import os

# Add root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("Testing module imports...")
    try:
        from app.config import settings
        from app.database.session import SessionLocal, engine, get_db
        from app.models.user import User
        from app.models.query import Query
        from app.models.response import AIResponse
        from app.models.quiz import Quiz
        from app.models.summary import Summary
        from app.models.learning_path import LearningPath
        from app.models.history import History
        from app.models.saved_response import SavedResponse
        from app.models.activity_log import ActivityLog
        from app.schemas.auth import UserRegister, UserLogin
        from app.schemas.ai import QARequest, QuizRequest
        from app.schemas.history import HistoryOut
        from app.services.auth_service import get_password_hash, verify_password
        from app.services.prompt_manager import PromptManager
        from app.services.ai_orchestrator import AIOrchestrator
        from app.services.edu_service import EduService
        from app.main import app

        print("[OK] All module imports succeeded.")
        return True
    except Exception as e:
        print(f"[ERROR] Module imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_db_setup():
    print("\nTesting database setup...")
    try:
        from app.database.session import SessionLocal, engine
        from app.database.base import Base
        
        # Create database tables
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created successfully.")
        
        # Test session creation
        db = SessionLocal()
        print("[OK] Database session created successfully.")
        db.close()
        return True
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        return False

def test_auth_cryptography():
    print("\nTesting password hashing and cryptography...")
    try:
        from app.services.auth_service import get_password_hash, verify_password
        
        password = "SuperSecurePassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password, "Hashed password matches plaintext!"
        assert verify_password(password, hashed), "Password verification failed!"
        assert not verify_password("WrongPassword", hashed), "Verification succeeded on wrong password!"
        
        print("[OK] Cryptography checks passed.")
        return True
    except Exception as e:
        print(f"[ERROR] Cryptography checks failed: {e}")
        return False

def main():
    print("================ EduGenie Backend Verification ==================")
    imports_ok = test_imports()
    db_ok = test_db_setup() if imports_ok else False
    auth_ok = test_auth_cryptography() if imports_ok else False
    
    print("=================================================================")
    if imports_ok and db_ok and auth_ok:
        print("[SUCCESS] Verification SUCCESSFUL! Backend is ready for production.")
        sys.exit(0)
    else:
        print("[ERROR] Verification FAILED. Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
