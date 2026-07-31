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

FRONTEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = FastAPI(title="StudyMate AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:8080"],
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

for r in [openai_compat_router, auth_router, chat_router, memory_router, notes_router,
          quiz_router, flashcards_router, dashboard_router, settings_router,
          notifications_router, goals_router, study_sessions_router,
          profile_router, analytics_router]:
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "StudyMate AI"}


# Serve frontend static assets
if os.path.isdir(os.path.join(FRONTEND, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND, "css")), name="css")
if os.path.isdir(os.path.join(FRONTEND, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND, "js")), name="js")


@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


@app.get("/{page:path}")
def serve_page(page: str):
    if not page.endswith(".html"):
        page += ".html"
    path = os.path.join(FRONTEND, page)
    if os.path.isfile(path):
        return FileResponse(path)
    return FileResponse(os.path.join(FRONTEND, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
