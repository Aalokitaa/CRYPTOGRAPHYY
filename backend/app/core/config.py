"""
CryptoScope Backend Configuration Settings
"""

import os
import shutil
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    PROJECT_NAME: str = "CryptoScope"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    IS_VERCEL: bool = os.environ.get("VERCEL") == "1"

    UPLOAD_DIR: Path = Path("/tmp/uploads") if os.environ.get("VERCEL") == "1" else BASE_DIR / "uploads"
    DATASET_DIR: Path = BASE_DIR / "datasets"
    MODEL_DIR: Path = BASE_DIR / "backend" / "app" / "models"
    REPORTS_DIR: Path = Path("/tmp/reports") if os.environ.get("VERCEL") == "1" else BASE_DIR / "reports"
    
    # SQLite Database
    DATABASE_URL: str = (
        "sqlite:////tmp/cryptoscope.db"
        if os.environ.get("VERCEL") == "1"
        else "sqlite:///./cryptoscope.db"
    )
    
    # 100 MB max upload limit for firmware blobs
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024
    
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()

# When running in Vercel serverless, seed /tmp with existing sqlite db if available
if settings.IS_VERCEL:
    tmp_db = Path("/tmp/cryptoscope.db")
    src_db = settings.BASE_DIR / "cryptoscope.db"
    if not tmp_db.exists() and src_db.exists():
        try:
            shutil.copy2(src_db, tmp_db)
        except Exception:
            pass

# Ensure required directories exist (safely catch Read-only FS on serverless)
try:
    for p in [settings.UPLOAD_DIR, settings.REPORTS_DIR]:
        p.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

