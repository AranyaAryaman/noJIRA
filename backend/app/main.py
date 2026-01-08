from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.config import get_settings
from app.routes import auth, projects, teams, tasks, comments, attachments

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Tasker API",
    description="Local-first task tracking for small teams",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(comments.router, prefix="/api/comments", tags=["comments"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["attachments"])


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
