# 🚀 StudyMate AI — Deployment Guide

This guide provides step-by-step instructions for deploying StudyMate AI to production using **Vercel**, **Render**, **Railway**, or **Docker**.

---

## 📌 Environment Variables Needed

Before deploying to any provider, prepare these environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | **Yes (Free)** | Free AI Key from [console.groq.com](https://console.groq.com) | `gsk_...` |
| `JWT_SECRET` | **Yes** | Any random 32+ character secret string | `super_secret_jwt_key_2026` |
| `OPENAI_API_KEY` | Optional | Optional OpenAI Key from [platform.openai.com](https://platform.openai.com) | `sk-proj-...` |
| `DB_HOST` | Optional | MySQL host (Default: SQLite local file) | `localhost` or Cloud MySQL |
| `DB_USER` | Optional | MySQL username | `root` |
| `DB_PASSWORD` | Optional | MySQL password | `your_password` |
| `DB_NAME` | Optional | Database name | `study_companion` |

---

## Option 1: Deploy to Vercel (Recommended — Free & Fast)

Vercel hosts both the FastAPI backend and frontend static assets effortlessly.

### Step 1: Install Vercel CLI (or connect GitHub)
```bash
npm install -g vercel
```

### Step 2: Deploy using Vercel CLI
From the root of the project (`study_companion`):
```bash
vercel
```
Follow the prompts:
- **Set up and deploy?** `Y`
- **Which scope?** (Select your account)
- **Link to existing project?** `N`
- **Project name?** `studymate-ai`
- **In which directory is your code located?** `./`

### Step 3: Set Environment Variables on Vercel
Go to your Vercel Dashboard ➔ Project Settings ➔ **Environment Variables**:
- Add `GROQ_API_KEY`
- Add `JWT_SECRET`

Then deploy to production:
```bash
vercel --prod
```
🎉 Your app will be live at `https://studymate-ai.vercel.app`!

---

## Option 2: Deploy to Render (Web Service)

Render provides free hosting for Python FastAPI Web Services.

### Step 1: Push project to GitHub
Create a GitHub repository and push your `study_companion` code.

### Step 2: Create a Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** ➔ **Web Service**.
3. Connect your GitHub repository.
4. Fill in the settings:
   - **Name:** `studymate-ai`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `python backend/main.py`
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY` = `your_groq_api_key`
   - `JWT_SECRET` = `your_random_secret`

6. Click **Create Web Service**.
Render will build and launch your application automatically!

---

## Option 3: Deploy with Docker / Railway

If you prefer containerized deployment:

### Local Docker Run:
```bash
docker-compose up --build
```
Open `http://localhost:5000` in your browser.

### Railway Deployment:
1. Go to [Railway.app](https://railway.app) and create a project.
2. Select **Deploy from GitHub repo**.
3. Add `GROQ_API_KEY` and `JWT_SECRET` under Railway Variables.
4. Railway will automatically detect the `Dockerfile` and launch your app!

---

## 🛠️ Testing Your Deployment
After deployment:
1. Open your public URL.
2. Try registering a new user account.
3. Test uploading notes and chatting with the AI.
4. Confirm all features work seamlessly in production!
