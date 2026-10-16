import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import init_db, get_db
from app.api.router import api_router
from app.api.v1.health import get_system_health
from app.schemas.health import HealthResponse

logger = logging.getLogger("borderwise.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    # Ensure database schema is initialized
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Cross-border financial copilot for international students.",
    lifespan=lifespan,
)


# Security: Limit maximum incoming request body size to prevent DoS
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_REQUEST_SIZE_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Payload too large. Maximum allowed request size is {settings.MAX_REQUEST_SIZE_BYTES} bytes."},
                    )
            except ValueError:
                pass
        return await call_next(request)


app.add_middleware(RequestSizeLimitMiddleware)

# Configure CORS restricted to intended origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global unhandled exception handler to prevent leaking internal stack traces or secrets
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify your request or try again later."},
    )


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with service identity and documentation pointers."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }


# Standard /health endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def top_level_health(db: Session = Depends(get_db)):
    """Standard top-level health probe."""
    return get_system_health(db=db)


# Explicit /api/health endpoint
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def api_level_health(db: Session = Depends(get_db)):
    """Standard API health probe."""
    return get_system_health(db=db)


# Include API v1 router
app.include_router(api_router)
