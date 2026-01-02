import logging
import os
import time
import uuid
import structlog
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.routes import router, kafka_producer
from src.utils.logger import setup_logging, get_logger
from src.utils.exceptions import AppError

# --- Configure Logging ---
setup_logging()
logger = get_logger("api")

# --- Rate Limiter Setup ---
limiter = Limiter(key_func=get_remote_address)

# --- FastAPI App Setup ---
app = FastAPI(
    title="AI Agent Framework API",
    version="1.0.0",
    description="Enterprise-grade API for managing AI agent workflows",
)

# --- Middleware: Request ID & Correlation ---
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request details (at INFO level)
    # logger.info(
    #     "Request processed",
    #     method=request.method,
    #     path=request.url.path,
    #     status_code=response.status_code,
    #     duration=process_time
    # )
    
    return response

# --- Metrics Endpoint ---
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- Rate Limiting State ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS Middleware ---
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(router)

# --- Event Handlers ---
@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Application started", version=app.version)

@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Application shutting down")
    if kafka_producer:
        try:
            # Check if close is awaitable or sync depending on implementation
            # usually kafka-python producer.close() is sync
            kafka_producer.close()
        except Exception as e:
            logger.error("Error closing Kafka producer", error=str(e))
    logger.info("Kafka producer closed")

# --- Exception Handlers ---

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppErrors with standardized structure."""
    logger.error(exc.message, code=exc.code, details=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global handler for unhandled exceptions."""
    logger.exception("Internal Server Error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred."
            }
        },
    )
