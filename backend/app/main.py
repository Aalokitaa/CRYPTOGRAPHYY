"""
CryptoScope Backend Application Entry Point
FastAPI + SQLAlchemy + Multi-Architecture Binary Analysis + ML Training Engine
"""

import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.analysis_router import router as analysis_router
from backend.app.api.ml_router import router as ml_router
from backend.app.api.reports_router import router as reports_router

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("cryptoscope")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite tables
    logger.info("Initializing CryptoScope database schema...")
    init_db()
    logger.info("CryptoScope backend initialized successfully.")
    yield
    logger.info("CryptoScope backend shutting down...")

app = FastAPI(
    title="CryptoScope",
    version="1.0.0",
    description="Defensive AI/ML Identification of Cryptographic Primitives and Protocol Patterns in Multi-Architecture Firmware",
    lifespan=lifespan
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Error Envelopes
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "Validation Error",
            "details": exc.errors(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": f"Internal server error: {str(exc)}",
            "path": request.url.path
        }
    )

# Health & Status
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "service": "CryptoScope Backend",
        "version": "1.0.0"
    }

# Mount Routers under /api
app.include_router(analysis_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
