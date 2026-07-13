# EduGenie – Google Gemini Powered Learning Assistant

EduGenie is a production-quality, secure, and responsive AI-powered educational co-pilot. The application leverages **Google Gemini 1.5 Flash** for advanced reasoning (Q&A, Quiz Generation, Summarization, and Roadmap Progression Plans) and **LaMini-Flan-T5** for structured concept explanations.

The system is engineered using a decoupled architecture, combining a high-performance **FastAPI backend** (with SQLite + SQLAlchemy) and a premium **Jinja2 + Vanilla JS Single-Page Application (SPA)** frontend featuring modern glassmorphic designs.

### Recent UI updates
- The dashboard Quick Start cards now navigate directly to the relevant workspace section after login.
- The Sign Out action redirects users back to the landing page.
- Protected dashboard sections now load correctly once the user session is active.

> To enable the full AI experience, add your `GEMINI_API_KEY` and `HF_API_KEY` values in the `.env` file before starting the app.

---

## 1. Project Directory Structure

```text
e:\Edugenie
│   .env.example             # Template for secure environment credentials
│   edugenie.db              # SQLite Database (auto-generated)
│   edugenie.log             # System runtime log (auto-generated)
│   README.md                # System Documentation & Guide
│   requirements.txt         # Package dependency requirements
│   schema.sql               # Relational DDL definitions & index scripts
│   test_backend.py          # Validation script for environment compilation
│
└───app
    │   config.py            # Pydantic Settings loader configuration
    │   main.py              # Application entry point & middleware configurations
    │
    ├───api
    │   │   api_v1.py        # Central Router aggregator
    │   │
    │   └───endpoints
    │           auth.py      # Registration, Session tokens, and Profiles
    │           ai_core.py   # AI inference endpoints (QA, Quiz, Explainer, etc.)
    │           history.py   # Milestone timeline logs & Bookmarks actions
    │           pages.py     # HTML Page views router (Landing, Dashboard, Login)
    │
    ├───database
    │       base.py          # Central SQLAlchemy declarative Base metadata
    │       session.py       # Engine creation, listeners, and session generators
    │
    ├───models               # SQLAlchemy Database Models (9 tables)
    │       activity_log.py  # User security audit records
    │       history.py       # Timeline study logs
    │       learning_path.py # Roadmap timelines & progression plans
    │       query.py         # Raw input inquiry strings
    │       quiz.py          # Multiple choice datasets and scoring
    │       response.py      # AI output text blocks & latency trackers
    │       saved_response.py# Saved bookmark items
    │       summary.py       # Summarizer text inputs/outputs
    │       user.py          # Security credentials profiles
    │
    ├───schemas              # Pydantic Request/Response Serializers
    │       ai.py            # AI feature requests & grading responses schemas
    │       auth.py          # Authentication requests, tokens, and output user schemas
    │       history.py       # Study logs and bookmarks payload schemas
    │
    ├───services             # Application Business Logic
    │       ai_orchestrator.py # Google Gemini & LaMini HF Inference engines
    │       auth_service.py  # Bcrypt security controls & JWT builders
    │       edu_service.py   # Transaction coordinator & scoring evaluator
    │       prompt_manager.py# Strict JSON system prompt formatting templates
    │
    ├───static               # Public Static Assets
    │   ├───css
    │   │       dashboard.css# Sidebar layout & MCQ grid styles
    │   │       main.css     # Spinners, buttons, inputs, & toasts styles
    │   │       variables.css# Custom HSL color variables & blur filters
    │   │
    │   └───js
    │           api_client.js# Asynchronous Fetch wrapper client
    │           ai_features.js# Dynamic view swapper & bookmark controller
    │           auth.js      # Credentials validator & logout dispatcher
    │           quiz.js      # Quiz timer, grades, and retry dispatcher
    │           roadmap.js   # Progression milestones rendering tree
    │
    └───templates            # Jinja2 Layout Templates
        │   base.html        # Shell layout declaring fonts and static scripts
        │   landing.html     # Hero showcase with glass features layout
        │
        ├───auth
        │       login.html   # Credentials gate
        │       register.html# Registration gate
        │
        └───dashboard
                index.html   # Authenticated dynamic workspace SPA
```

---

## 2. Relational Database Design

The database contains 9 highly normalized tables defined in `schema.sql`:

1. **`users`**: Academic credentials, hashes, and profiles.
2. **`queries`**: Audits raw prompts and classifies inquiry types.
3. **`responses`**: Maps AI outputs, models used, and latency in milliseconds.
4. **`quizzes`**: Stores multiple-choice question datasets and student scores.
5. **`summaries`**: Logs original source files and summarized outputs.
6. **`learning_paths`**: Saves step-based timelines and milestone roadmaps.
7. **`saved_responses`**: Student response bookmarks.
8. **`history`**: Audit logs populating the student timeline.
9. **`activity_logs`**: Logs connection, security, and verification activities.

Optimization indexes are configured on foreign keys and unique columns (e.g. `username`, `email`, `user_id`, etc.) to maximize fetch speeds.

---

## 3. Installation & Setup Guide

### Step 3.1 Prerequisite Check
Ensure you have **Python 3.10** or higher installed on your system.

### Step 3.2 Initialize Virtual Environment
Clone the project, navigate to the directory, and spin up an isolated virtual environment:
```powershell
# Create Virtual Environment using Python 3.10
"C:\Program Files\Python310\python.exe" -m venv venv

# Activate Virtual Environment
.\venv\Scripts\Activate.ps1
```

### Step 3.3 Install Dependencies
Install packages within the virtual environment using the local mirror configuration:
```powershell
pip install -r requirements.txt --default-timeout=120 --no-cache-dir
```

### Step 3.4 Configure Environment Credentials
Copy the environment template and name it `.env`:
```powershell
copy .env.example .env
```
Open `.env` and fill in your credentials:
* **`GEMINI_API_KEY`**: Obtain from Google AI Studio.
* **`HF_API_KEY`**: Obtain from Hugging Face Settings.

After saving the file, restart the server so the new values are loaded.

*Note: If no API keys are configured, the system automatically redirects requests to local mock fallbacks so you can test all features without API credentials.*

---

## 4. System Verification

To verify that the workspace compiles, handles database pipelines, and registers encryption routines, execute the verification script:
```powershell
python test_backend.py
```
On success, you will see:
```text
================ EduGenie Backend Verification ==================
Testing module imports...
[OK] All module imports succeeded.

Testing database setup...
[OK] Database tables created successfully.
[OK] Database session created successfully.

Testing password hashing and cryptography...
[OK] Cryptography checks passed.
=================================================================
[SUCCESS] Verification SUCCESSFUL! Backend is ready for production.
```

---

## 5. Running the Application

To launch the local web server:
```powershell
python -m uvicorn app.main:app --reload
```
Once initialized, access the portal in your browser:
* **Interactive Frontend**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **FastAPI Swagger API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

After signing in, use the Quick Start cards on the dashboard to jump straight to Smart Q&A, Concept Explainer, Roadmap, Quiz, or Summarizer views.

---

## 6. SmartBridge Submission Compliance

All core SmartBridge requirements have been satisfied:
* [x] **Secure Authentication**: Uses native `bcrypt` cryptography to hash passwords. Employs signed `HS256` JSON Web Tokens (JWT) inside HTTP-only cookies to validate student routes.
* [x] **Relational SQLite Normalization**: 9 tables configured with foreign key constraints (`ON DELETE CASCADE`, `ON DELETE SET NULL`) and indexes.
* [x] **SPA View Controller**: Switches views asynchronously without full-page reloads.
* [x] **Google Gemini Integration**: Standardized prompts enforce JSON formats for roadmap steps, summaries, Q&A responses, and MCQs.
* [x] **LaMini-Flan-T5 Explainer**: Formulates multi-level educational summaries based on concepts.
* [x] **Grading & Retry Engine**: Tracks score accuracy and enables one-click retakes.
* [x] **Glassmorphic Responsive UX**: Premium Dark Mode CSS tokens optimized for desktop, tablet, and mobile views.

---

## 7. Future Scope & Roadmap

To scale EduGenie beyond a desktop assistant into an enterprise-level SaaS platform:
1. **Containerization & Deployment**: Set up a `Dockerfile` and `docker-compose` YAML to deploy the backend and Postgres service clusters.
2. **Vector Indexing (RAG)**: Integrate **ChromaDB** or **FAISS** with LangChain, enabling students to upload custom PDF textbook chapters and execute semantic searches.
3. **Advanced Analytics**: Integrate **Charts.js** to render weekly academic statistics, tracking response bookmarks count, quiz averages, and study times.
4. **Offline Local Models**: Integrate a local **Ollama** server connection to run open-weight models (like Llama 3 or Phi 3) locally on the student's GPU.

---

## 8. Screenshots & Media Placeholder

Below are visual showcases demonstrating the premium user experience across all key student workflows:
- **Interactive Workspace & AI Copilot**: *(Image placeholder for future deployment renders)*
- **Smart Quiz Generator & Timeline Tracker**: *(Image placeholder for future deployment renders)*

---

## 9. Project License

This repository is licensed under the terms of the MIT License. See below for details:

```text
Copyright (c) 2026 EduGenie Developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```
