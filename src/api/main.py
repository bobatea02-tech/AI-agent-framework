from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router, kafka_producer

# --- Configure Structlog ---

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if os.getenv("LOG_FORMAT") == "json" else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()


# --- FastAPI App Setup ---

app = FastAPI(
    title="AI Agent Framework API",
    version="1.0.0",
    description="API for managing AI agent workflows and tasks",
)

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
