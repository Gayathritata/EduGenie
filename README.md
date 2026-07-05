# 🤝 Personalized Networking Assistant

An AI-powered networking assistant that helps users generate personalized conversation starters for professional events and conferences.

Built using **FastAPI**, **Streamlit**, **Natural Language Processing (NLP)**, and **Wikipedia API**.

---

## 📌 Features

- 🔍 Analyze networking event descriptions
- 🧠 Detect important topics using NLP
- 💬 Generate personalized conversation starters
- 📚 Verify topics using Wikipedia
- 📝 Save conversation history
- 👍👎 Collect user feedback on suggestions
- 📄 Download conversation reports as PDF
- 🧪 Unit testing with PyTest
- 📖 Interactive API documentation using Swagger UI

---

## 🏗️ Project Architecture

```text
User
  ↓
Streamlit Frontend
  ↓
FastAPI Backend
  ↓
Services Layer
 ├── Event Analyzer
 ├── Topic Generator
 ├── Fact Checker
 ├── History Logger
 └── Feedback Logger
  ↓
JSON Storage + Wikipedia API
```

---

## 📂 Project Structure

```text
personalized-networking-assistant/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── routers/
│   └── services/
│
├── frontend/
│   └── streamlit_app.py
│
├── tests/
│   ├── conftest.py
│   ├── test_event_analyzer.py
│   ├── test_fact_checker.py
│   └── test_routes.py
│
├── images/
├── history.json
├── feedback.json
├── requirements.txt
├── README.md
└── .env
```

---

## ⚙️ Technologies Used

| Technology | Purpose |
|------------|---------|
| FastAPI | Backend API |
| Streamlit | Frontend UI |
| Transformers | NLP Processing |
| Wikipedia API | Fact Verification |
| ReportLab | PDF Generation |
| PyTest | Unit Testing |
| Git & GitHub | Version Control |

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/samxiao0/skill-wallet---GenAI-Project-.git

cd personalized-networking-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate environment:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run Backend

```bash
python -m uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API Documentation:

```text
http://127.0.0.1:8000/docs
```

---

## ▶️ Run Frontend

```bash
streamlit run frontend/streamlit_app.py
```

Frontend runs at:

```text
http://localhost:8501
```

---

## 🧪 Running Tests

Run all test cases:

```bash
pytest -v
```

Example output:

```text
================ 5 passed =================
```

---

## 📷 Application Screenshots

### 🏠 Home Page

![Home Page](images/homepage.png)

### 📖 Swagger UI

![Swagger UI](images/swagger%20ui.png)

### 🔎 Fact Checker

![Fact Checker](images/fact%20checker.png)

---

## 🌟 Future Enhancements

- Gemini API integration
- User authentication system
- Cloud deployment
- Database integration (MongoDB/PostgreSQL)
- Analytics dashboard
- Dark mode support

---

## 👨‍💻 Author

**Course : Google Cloud Generative AI**

**AITS Kadapa**

**B.Tech CSE (AI & ML)**


**Syed Mohammad Sameer**

Email : syedsame2244@gmail.com

Roll No. : 23HM1A3354

GitHub: https://github.com/samxiao0

1. Name : syed Jaffarhussain 

Email : js8380237@gmail.com

Roll No. :23HM1A3353

GitHub:

2. Name : 

Email :

Roll No. :

GitHub:

3. Name : 

Email :

Roll No. :

GitHub:

4. Name : 

Email :

Roll No. :

GitHub:

---

## 📜 License

This project was developed as part of an internship project for educational purposes.
