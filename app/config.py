"""Application configuration module for Café Companion.

Handles environment variables, Google Cloud credentials, database
connection parameters, and application defaults following PEP 8.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Database configuration: Cloud SQL PostgreSQL or local SQLite fallback
# When deploying to Google Cloud Run, CLOUD_SQL_CONNECTION_NAME can be set.
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Use SQLite for local development and self-contained zero-setup operation
    DATABASE_PATH = BASE_DIR / "cafe_companion.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Cafe Metadata
CAFE_NAME = "The Artisan Roast & Byte"
CAFE_TAGLINE = "Where Specialty Coffee Meets Human Connection"
MAX_QUEUE_ESTIMATE_PER_ORDER = 4  # minutes per typical barista preparation
