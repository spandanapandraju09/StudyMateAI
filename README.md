# StudyAI — AI Study Companion

A professional web-based AI study companion built with **Python (Flask)**, **HTML/CSS/JavaScript**, **MySQL**, and **OpenAI**.

Students can upload notes, chat with a human-like AI tutor, generate quizzes & flashcards, track progress, and personalize their experience with persona modes and memory.

---

## Features

| Feature | Description |
|---------|-------------|
| **AI Study Chat** | Tutor-like chat that answers from your notes, adapts to mood, remembers weak areas |
| **Memory System** | Stores preferences, topics, and insights for personalized replies |
| **Quiz Generator** | MCQs & short-answer from notes with instant scoring & explanations |
| **Flashcards** | Flip cards, mark known/unknown, revisit weak cards |
| **Dashboard** | Streaks, study time, weak topics, quiz scores, recent activity |
| **Notes Upload** | Paste text or upload `.txt` / `.pdf` files |
| **Persona Modes** | Friendly Buddy, Strict Teacher, Motivational Mentor, Exam Coach |

---

## Project Structure

```
study_companion/
├── backend/
│   ├── app.py                 # Flask entry point
│   ├── config.py              # Config & persona definitions
│   ├── requirements.txt
│   ├── .env                   # Secrets (create from .env.example)
│   ├── db/
│   │   ├── connection.py      # MySQL connection
│   │   └── schema.sql         # Database schema
│   ├── routes/                # API endpoints
│   ├── services/              # OpenAI logic
│   └── utils/                 # Auth & helpers
└── frontend/
    ├── index.html             # Landing page
    ├── login.html / register.html
    ├── onboarding.html        # Goals + persona selection
    ├── dashboard.html
    ├── chat.html
    ├── notes.html
    ├── quiz.html
    ├── flashcards.html
    ├── analytics.html
    ├── settings.html
    ├── css/                   # Styles + animations
    └── js/                    # API client
```

---

## Step-by-Step Setup

### Step 1: Install Prerequisites

- **Python 3.10+**
- **MySQL 8.0+** (XAMPP/WAMP or standalone)
- **OpenAI API key** from [platform.openai.com](https://platform.openai.com)

### Step 2: Create MySQL Database

Open MySQL Workbench or command line:

```bash
mysql -u root -p < backend/db/schema.sql
```

Or run the SQL file manually in MySQL Workbench.

### Step 3: Configure Environment

```bash
cd backend
copy .env.example .env
```

Edit `.env` with your values:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=study_companion
OPENAI_API_KEY=sk-your-key-here
JWT_SECRET=any-random-secret-string
```

### Step 4: Install Python Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### Step 5: Run the Server

```bash
cd backend
python app.py
```

Open **http://localhost:5000** in your browser.

### Step 6: User Flow

1. **Register** → Create account
2. **Onboarding** → Set study goals + choose AI persona
3. **Upload Notes** → Paste or upload study material
4. **Chat** → Ask questions from your notes
5. **Generate Quiz / Flashcards** → AI creates from your notes
6. **Dashboard** → Track streaks, scores, weak topics

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/chat/send` | Send chat message |
| GET/POST | `/api/notes` | List / upload notes |
| POST | `/api/quiz/generate` | Generate quiz |
| POST | `/api/quiz/:id/submit` | Submit quiz answers |
| POST | `/api/flashcards/generate` | Generate flashcards |
| GET | `/api/dashboard` | Dashboard stats |
| GET/PUT | `/api/settings` | User settings |
| GET/POST | `/api/memory` | Memory items |

---

## Hackathon Demo Tips

1. **Pre-upload sample notes** (DBMS, Python, etc.) before demo
2. **Show persona switch** in Settings — chat tone changes immediately
3. **Add manual memory** like "I'm weak in DBMS joins" in Settings
4. **Generate a quiz live** — instant scoring impresses judges
5. **Show dashboard streak** after a few activities

---

## Tech Stack

- **Backend:** Python, Flask, Flask-CORS, PyJWT, bcrypt
- **Database:** MySQL
- **AI:** OpenAI GPT-4o-mini
- **Frontend:** HTML5, CSS3 (animations), Vanilla JavaScript
- **Charts:** Chart.js (analytics page)

---

## License

MIT — Built for hackathons and learning projects.
