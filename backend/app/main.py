from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.scan import router as scan_router

# Import database components and models
from app.core.database import Base, engine
from app.models.scan import Scan  # Ensures the Scan table is registered

# ==================== App Initialization ====================
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
)

# Create tables in the database on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.error(f"Database connection/startup failed: {e}")

# ==================== CORS Middleware ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request Logging Middleware ====================
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Completed: {response.status_code} in {process_time:.2f}s")
        return response

app.add_middleware(LoggingMiddleware)

# ==================== Global Error Handler ====================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 1. If it's a validation error (422), let FastAPI's internal handler 
    # show the exact field that failed instead of hiding it.
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    # 2. For all other errors, log the full message and return a 500
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error_type": type(exc).__name__,
            "message": str(exc)
        },
    )

# ==================== Endpoints & Routers ====================

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
    }

# Include the scan router with the versioned prefix
app.include_router(scan_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}! Visit /docs for API documentation."}