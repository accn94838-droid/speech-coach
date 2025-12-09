import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from app.api.deps import get_speech_pipeline
from app.models.analysis import AnalysisResult
from app.services.pipeline import SpeechAnalysisPipeline
from app.core.exceptions import (
    SpeechCoachException,
    FileValidationError,
    TranscriptionError,
    AnalysisError,
)

router = APIRouter(prefix="/api/v1", tags=["analysis"])
logger = logging.getLogger(__name__)


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Анализ видеофайла с речью",
    description="""
    Загрузите видеофайл для анализа публичной речи.
    
    Поддерживаемые форматы: MP4, MOV, AVI, MKV, WEBM, FLV, WMV, M4V
    Максимальный размер файла: 100 MB
    
    Возвращает:
    - Базовые метрики речи (темп, паузы, слова-паразиты)
    - Транскрипт текста
    - Рекомендации по улучшению
    - Расширенный AI-анализ через GigaChat (если включен)
    """,
    responses={
        200: {"description": "Анализ успешно выполнен"},
        400: {"description": "Некорректный файл или формат"},
        413: {"description": "Файл слишком большой"},
        500: {"description": "Ошибка при обработке файла"},
    }
)
async def analyze_video(
    file: UploadFile = File(
        ...,
        description="Видеофайл для анализа (до 100 MB)",
    ),
    pipeline: SpeechAnalysisPipeline = Depends(get_speech_pipeline),
):
    """
    Анализирует загруженное видео и возвращает результаты анализа речи.

    Процесс анализа:
    1. Валидация файла (размер, формат)
    2. Извлечение аудио из видео
    3. Транскрипция речи с помощью Whisper
    4. Расчет метрик (темп, паузы, слова-паразиты)
    5. Генерация рекомендаций
    6. Расширенный AI-анализ через GigaChat (опционально)
    """
    logger.info(f"Received analysis request for file: {file.filename}")

    try:
        result = await pipeline.analyze_upload(file)
        logger.info(f"Analysis completed for {file.filename}")
        return result

    except FileValidationError as e:
        # Ошибки валидации файла (размер, формат)
        logger.warning(f"File validation error for {
                       file.filename}: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except (TranscriptionError, AnalysisError) as e:
        # Ошибки обработки (транскрипция, анализ)
        logger.error(f"Processing error for {file.filename}: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except SpeechCoachException as e:
        # Другие кастомные исключения
        logger.error(f"SpeechCoach error for {file.filename}: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        # Неожиданные ошибки
        logger.error(f"Unexpected error for {
                     file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing the file"
        )
