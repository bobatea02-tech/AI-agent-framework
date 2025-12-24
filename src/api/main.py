import logging
import os
import sys
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from src.api.routes import router, kafka_producer
from src.utils.logger import setup_logging, get_logger

# --- Configure Logging ---
setup_logging()
logger = get_logger("api")


# --- FastAPI App Setup ---

app = FastAPI(
    title="AI Agent Framework API",
    version="1.0.0",
    description="API for managing AI agent workflows and tasks",
)

# --- Metrics Endpoint ---
# Create ASGI app for Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


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
        kafka_producer.close()
    logger.info("Kafka producer closed")


# --- Exception Handlers ---

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Internal Server Error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Not Found", path=request.url.path)
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found", "path": str(request.url.path)},
    )


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warning("Validation Error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation Error", "body": str(exc)},
    )
