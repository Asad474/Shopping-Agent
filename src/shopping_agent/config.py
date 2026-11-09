import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project root directory: 3 levels up from src/shopping_agent/config.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database path (configurable via DB_PATH env var, defaults to store.db in project root)
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "store.db"))

# LLM model names
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-3.5-flash-lite")
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-3.1-flash-lite-image")
