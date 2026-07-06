# File: app/database/base.py
# Part of EduGenie SmartBridge Project

# Import all models so SQLAlchemy metadata registers them
from app.database.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.query import Query  # noqa
from app.models.response import AIResponse  # noqa
from app.models.quiz import Quiz  # noqa
from app.models.summary import Summary  # noqa
from app.models.learning_path import LearningPath  # noqa
from app.models.history import History  # noqa
from app.models.saved_response import SavedResponse  # noqa
from app.models.activity_log import ActivityLog  # noqa
