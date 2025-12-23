from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.config import settings
from app.core.logging import logger  # ← New better logger

# Create the FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
)

# ==================== CORS Middleware ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
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
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# ==================== Health Check Endpoint ====================
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
    }

# ==================== Root Endpoint ====================
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}! Visit /docs for API documentation."}