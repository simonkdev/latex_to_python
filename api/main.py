"""FastAPI application for LaTeX to Python conversion."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.routes import router as convert_router

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").lower() == "true"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="LaTeX to Python Translator",
    description="Convert LaTeX mathematical expressions to Python code",
    version="0.1.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
)

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))
app.mount("/public", StaticFiles(directory=str(PROJECT_ROOT / "public")), name="public")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Include routers
app.include_router(convert_router)


@app.get("/", tags=["root"])
async def root(request: Request) -> HTMLResponse:
    """Serve the browser UI."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
