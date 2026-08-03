import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.memory import router as memory_router
from backend.routers.notes import router as notes_router
from backend.routers.quiz import router as quiz_router
from backend.routers.flashcards import router as flashcards_router
from backend.routers.dashboard import dashboard_router, settings_router
from backend.routers.openai_compat import router as openai_compat_router
from backend.routers.notifications import router as notifications_router
from backend.routers.goals import router as goals_router
from backend.routers.study_sessions import router as study_sessions_router
from backend.routers.profile import router as profile_router
from backend.routers.analytics import router as analytics_router
from backend.routers.workspace import router as workspace_router

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = FastAPI(
    title="Nexus AI Operating System",
    description="Universal AI Operating System combining ChatGPT + Notion + Cursor + Arc Browser + Apple Intelligence + Claude capabilities.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def security_firewall_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(openai_compat_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(notes_router)
app.include_router(quiz_router)
app.include_router(flashcards_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(notifications_router)
app.include_router(goals_router)
app.include_router(study_sessions_router)
app.include_router(profile_router)
app.include_router(analytics_router)
app.include_router(workspace_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "AIRA AI Operating System"}


@app.get("/api/test-db")
def test_db():
    from backend.db.connection import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    db_name = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return {"message": "Connected!", "database": db_name}


# Serve frontend static assets
if os.path.isdir(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.isdir(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{page:path}")
def serve_frontend(page: str):
    if not page.endswith(".html"):
        page += ".html"
    file_path = os.path.join(FRONTEND_DIR, page)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)