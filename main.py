"""Main application entry point for The Café Companion.

Initializes FastAPI application, mounts static assets, registers routes,
configures CORS, runs database migrations/seeds on startup, and launches
the Uvicorn server when executed directly.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import HOST, PORT
from app.database import init_database
from app.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to handle application startup and shutdown tasks."""
    # Ensure database schema exists and initial catalog is populated
    init_database()
    yield
    # Teardown logic can be placed here if needed


# Instantiate FastAPI application
app = FastAPI(
    title="The Café Companion",
    description="A smarter café experience powered by Google Cloud & Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset directory for CSS, JS, and high-resolution café photography
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register API routes
app.include_router(api_router)


@app.get("/", summary="Root application UI")
async def serve_index():
    """Serve the single-page application user interface."""
    index_file = TEMPLATES_DIR / "index.html"
    return FileResponse(index_file)


if __name__ == "__main__":
    # Launch Uvicorn ASGI server
    print(f"Starting The Café Companion at http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
