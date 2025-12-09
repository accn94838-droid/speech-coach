import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.routes.health import router as health_router
from app.api.routes.analysis import router as analysis_router
from app.core.lifespan import lifespan
from app.core.config import settings
from app.core.exceptions import SpeechCoachException
from app.core.logging_config import setup_logging

# Настраиваем логирование
setup_logging(log_level="INFO")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Speech Coach API",
    description="Сервис для анализа качества публичной речи с поддержкой AI-анализа через GigaChat",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Глобальный обработчик кастомных исключений
@app.exception_handler(SpeechCoachException)
async def speech_coach_exception_handler(request: Request, exc: SpeechCoachException):
    logger.warning(f"SpeechCoachException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": exc.__class__.__name__
        },
    )


# Обработчик ошибок валидации запросов
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        },
    )


# Глобальный обработчик неожиданных ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": exc.__class__.__name__,
            "message": str(exc)
        },
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Включаем роутеры
app.include_router(health_router)
app.include_router(analysis_router)


@app.get("/")
async def root():
    """Корневой эндпоинт с информацией о API"""
    logger.info("Root endpoint accessed")
    return {
        "name": "Speech Coach API",
        "version": "1.0.0",
        "description": "Анализ качества публичной речи с AI-анализом",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze"
        },
        "features": {
            "whisper_transcription": True,
            "speech_metrics": True,
            "gigachat_analysis": settings.gigachat_enabled,
            "max_file_size_mb": settings.max_file_size_mb,
            "supported_formats": settings.allowed_video_extensions
        }
    }
