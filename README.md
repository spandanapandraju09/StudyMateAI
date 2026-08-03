# Nexus AI OS — Next-Gen AI Operating System

A premium, high-performance web-based AI Operating System built with **FastAPI / Python**, **Three.js**, **GSAP**, **HTML5/CSS3/JavaScript**, **SQLite/MySQL**, and **Groq / OpenAI**.

Nexus AI combines the power of **ChatGPT + Notion + Cursor + Arc Browser + Apple Intelligence + Claude** into one unified platform.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Universal AI Chat** | Multi-model streaming AI supporting Coding, Debugging, Writing, Translation, Business, Resume, Math & Science |
| **Chat History Panel** | Search, pin, archive, favorite, category filters, JSON export/import, single/batch delete |
| **Explicit Memory Bank** | User-controlled explicit memory storage (Personal, Coding, Projects, Goals) with enable/disable toggle |
| **Universal Library** | Multi-format document hub supporting PDF, DOCX, TXT, Code (.py, .js, .cpp, .rs), CSV, PPTX & Excel |
| **AI Workspace** | Interactive Code Playground, Canvas / Whiteboard, Markdown Notebook, Kanban Tasks, Sticky Notes, Pomodoro Timer & Prompt Library |
| **Gamification & Analytics** | XP tracking, Level progression, Achievements, Activity Heatmaps & Usage Analytics |
| **Futuristic UI/UX** | Three.js cosmic background, 3D mascot robot, Aurora glassmorphism, floating icons & Command Palette (`Ctrl+K`) |

---

## Project Structure

```
study_companion/
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── app.py                 # Alternative FastAPI entry point
│   ├── config.py              # System personas & config
│   ├── db/
│   │   ├── connection.py      # SQLite / MySQL auto-migration connection
│   │   └── schema.sql         # Base database schema
│   ├── routers/               # FastAPI routers (chat, memory, notes, workspace, analytics, etc.)
│   └── services/              # Groq & OpenAI streaming AI services
└── frontend/
    ├── index.html             # Landing page
    ├── dashboard.html         # Dashboard & 3D Mascot Showcase
    ├── chat.html              # Universal AI Chat with History Panel
    ├── library.html           # Universal Library & Document Hub
    ├── workspace.html         # AI Workspace (Playground, Canvas, Tasks, Pomodoro)
    ├── quiz.html              # Quiz Generator
    ├── flashcards.html        # Spaced Repetition 3D Flashcards
    ├── analytics.html         # Activity Heatmaps & Progress
    ├── settings.html          # Appearance, AI Persona & Explicit Memory Controls
    ├── css/                   # Styles, Glassmorphism & Animations
    └── js/                    # API client, 3D Canvas & Command Palette
```

---

## Quick Setup & Execution

### 1. Install Python Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` inside `backend/`:

```
GROQ_API_KEY=your-groq-key-here
OPENAI_API_KEY=your-openai-key-here
JWT_SECRET=nexus-ai-os-secret
```

### 3. Run FastAPI Application

```bash
python main.py
```

Open **http://localhost:5000** in your browser.

---

## License

MIT — Nexus AI OS. All rights reserved.
