"""JLPT N1 quiz backend — FastAPI app factory."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import attempts, auth, exams, practice, wrong_answers

app = FastAPI(title="JLPT N1 Quiz API", version="0.1.0")

# 音頻等靜態資源：backend/static/audio/*.mp3 → /static/audio/*.mp3
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exams.router, prefix="/api")
app.include_router(practice.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(wrong_answers.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
