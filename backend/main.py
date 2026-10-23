"""
Entry point for Vercel deployment of CryptoScope FastAPI backend.
"""
import sys
from pathlib import Path

# Ensure root of repo and backend directory are in sys.path
backend_dir = Path(__file__).resolve().parent
repo_root = backend_dir.parent

for p in (str(repo_root), str(backend_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.main import app
