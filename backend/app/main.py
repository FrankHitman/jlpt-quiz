"""JLPT N1 quiz backend — FastAPI app factory."""
from __future__ import annotations

from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import attempts, auth, exams, practice, wrong_answers


IS_PRODUCTION = os.getenv("APP_ENV", "development") == "production"

app = FastAPI(
    title="JLPT N1 Quiz API",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
    version="1.0.0",
)

# 音頻等靜態資源：backend/static/audio/*.mp3 → /static/audio/*.mp3
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "static"),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://jlpt.gothruwall.eu.org:5173", "http://jlpt.gothruwall.eu.org:8000"],
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
