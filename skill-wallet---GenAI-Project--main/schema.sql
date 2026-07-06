-- EduGenie Database Schema DDL (SQLite)
-- Configured for production compliance under SQLAlchemy ORM and FastAPI integration.

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Table: users
-- Holds verified student user account records.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Table: queries
-- Logs all raw natural language queries entered by the student.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL, -- e.g., "qa", "explain", "quiz_gen", "summarize", "roadmap_gen"
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: responses
-- Logs AI system responses generated for each student query.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER UNIQUE, -- Strict 1-to-1 query-response linkage
    user_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    model_used VARCHAR(50) NOT NULL, -- e.g., "gemini-1.5-flash", "lamini-flan-t5"
    latency_ms INTEGER, -- Monitor performance latency of APIs
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(query_id) REFERENCES queries(id) ON DELETE SET NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: quizzes
-- Contains generated interactive multiple-choice quizzes and scores.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    topic VARCHAR(255) NOT NULL,
    questions_data JSON NOT NULL, -- Holds choices, questions, correct keys, explanations
    score INTEGER, -- Populated after the student submits choices
    total_questions INTEGER NOT NULL DEFAULT 5,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: summaries
-- Logs document text summarization sessions.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    length_type VARCHAR(50) NOT NULL, -- "short", "medium", "long"
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: learning_paths
-- Tracks progress milestones for customized education roadmaps.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    topic VARCHAR(255) NOT NULL,
    difficulty VARCHAR(50) NOT NULL, -- "Beginner", "Intermediate", "Advanced"
    roadmap_data JSON NOT NULL, -- Roadmap steps structure
    current_step INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: history
-- Timeline logs representing student study milestones.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL, -- e.g., "asked_question", "completed_quiz"
    entity_id INTEGER, -- Generic FK reference to target table (quiz_id, path_id, etc.)
    entity_type VARCHAR(50), -- Defines entity table type ("quiz", "learning_path")
    description TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Table: saved_responses
-- Bookmarked AI content saved by the user.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS saved_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    source_response_id INTEGER, -- Soft link to original response log
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- e.g., "qa", "roadmap", "quiz", "summary"
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(source_response_id) REFERENCES responses(id) ON DELETE SET NULL
);

-- -----------------------------------------------------
-- Table: activity_logs
-- Security logging auditing logins, actions, and API events.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL, -- e.g., "login_success", "api_call", "logout"
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- -----------------------------------------------------
-- Index Optimization Setup
-- -----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id);
CREATE INDEX IF NOT EXISTS idx_queries_query_type ON queries(query_type);
CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);
CREATE INDEX IF NOT EXISTS idx_responses_query_id ON responses(query_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_summaries_user_id ON summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_id ON learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user_id ON history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_action ON history(action);
CREATE INDEX IF NOT EXISTS idx_saved_responses_user_id ON saved_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_responses_category ON saved_responses(category);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action);
