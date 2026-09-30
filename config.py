import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or os.urandom(32).hex()
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    DATABASE_PATH = os.getenv(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "resume_analyzer.sqlite3")
    )
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    ALLOWED_EXTENSIONS = {"pdf", "docx"}
    MAX_RESUME_CHARS = 40_000
    MAX_PDF_PAGES = 50
    MAX_DOCX_UNCOMPRESSED_BYTES = 15 * 1024 * 1024
