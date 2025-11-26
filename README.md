Smart Task Analyzer – Internship Assignment (2025)

A full-stack task prioritization system based on urgency, importance, effort & dependencies.

Built by: Som Kumar Pawar
Role Target: Software Development Intern — Singularium Technologies
Tech Stack: Django (Python), HTML/CSS/JS


🚀 Overview

This project implements an intelligent task ranking system that helps users decide which tasks to complete first.

The algorithm considers:
Urgency (due dates, overdue tasks, near deadlines)

Importance (user-defined 1–10 scale)

Effort (estimated hours)

Dependencies (which tasks unlock others)

Quick wins vs high-impact tasks

Circular dependency detection


📦 Features
1. Task Prioritization

Each task receives a final score (0–1) that determines its priority based on:

Deadline proximity

Importance

Effort (low effort = “quick win”)

Dependency graph influence

Strategy selected (smart balance, high impact, etc.)

2. Scoring Strategies

You can choose between:

Strategy	Behavior
Smart Balance	Balanced mix of all factors
Fastest Wins	Prioritizes low-effort tasks
High Impact	Prioritizes high-importance tasks
Deadline Driven	Prioritizes near-deadline tasks

3. Dependency Handling

Tasks that unlock many others get higher priority

A full cycle detection algorithm identifies circular dependencies

4. API Endpoints
POST /api/tasks/analyze/

Request body:

{
  "strategy": "smart_balance",
  "tasks": [
    {
      "id": "T1",
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ]
}


Response:

Sorted tasks with score + explanation

Warnings (e.g., circular dependencies)

GET /api/tasks/suggest/

Returns top 3 tasks:

/api/tasks/suggest/?strategy=fastest_wins&tasks=[...]

⚙️ Project Setup
Backend
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py runserver


Backend runs at:

http://127.0.0.1:8000/

Frontend

Open this file in any browser:

frontend/index.html


No frameworks required.

🧠 Algorithm Explanation

The system generates a priority score for each task using:

1. Urgency

Calculated from due dates:

Overdue → maximum urgency

Due today → high urgency

Within 30 days → proportional decline

Missing → neutral

2. Importance

Normalized 1–10 → 0–1 scale.

3. Effort

Less effort = higher priority ("quick wins").

4. Dependencies

Tasks that other tasks depend on are weighted higher.

5. Circular Dependency Detection

A DFS-based cycle detection prevents infinite loops.

6. Final Score

Each strategy uses a different weighted formula to compute the score.

🧪 Sample Data for Testing 
[
  {
    "id": "T1",
    "title": "Prepare presentation for Monday client meeting",
    "due_date": "2025-11-29",
    "estimated_hours": 4,
    "importance": 9,
    "dependencies": []
  },
  {
    "id": "T2",
    "title": "Reply to pending HR emails",
    "due_date": "2025-11-27",
    "estimated_hours": 1,
    "importance": 5,
    "dependencies": []
  },
  {
    "id": "T3",
    "title": "Fix logout redirect bug on website",
    "due_date": "2025-11-30",
    "estimated_hours": 2,
    "importance": 8,
    "dependencies": ["T4"]
  },
  {
    "id": "T4",
    "title": "Update API documentation",
    "due_date": "2025-12-02",
    "estimated_hours": 3,
    "importance": 6,
    "dependencies": []
  }
]

🧹 Folder Structure
task-analyzer/
│
├── backend/
│   ├── task_analyzer/
│   ├── tasks/
│   │   ├── scoring.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   └── manage.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
└── README.md

