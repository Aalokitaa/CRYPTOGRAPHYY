"""
CryptoScope Backend Configuration Settings
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "CryptoScope"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DATASET_DIR: Path = BASE_DIR / "datasets"
    MODEL_DIR: Path = BASE_DIR / "backend" / "app" / "models"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    
    # SQLite Database
    DATABASE_URL: str = "sqlite:///./cryptoscope.db"
    
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

# Ensure required directories exist
for p in [settings.UPLOAD_DIR, settings.REPORTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
