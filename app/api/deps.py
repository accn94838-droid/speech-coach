import logging
from functools import lru_cache
from typing import Optional  # Убедитесь, что Optional импортирован

from app.services.audio_extractor_advanced import AdvancedFfmpegAudioExtractor
from app.services.transcriber import LocalWhisperTranscriber
from app.services.analyzer import SpeechAnalyzer
from app.services.gigachat import GigaChatClient
from app.services.pipeline import SpeechAnalysisPipeline
from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_audio_extractor() -> AdvancedFfmpegAudioExtractor:
    return AdvancedFfmpegAudioExtractor()


@lru_cache(maxsize=1)
def get_transcriber() -> LocalWhisperTranscriber:
    return LocalWhisperTranscriber()


@lru_cache(maxsize=1)
def get_analyzer() -> SpeechAnalyzer:
    return SpeechAnalyzer()


@lru_cache(maxsize=1)
def get_gigachat_client() -> Optional[GigaChatClient]:
    """Создает и кеширует клиент GigaChat, если настроен и включен"""
    if not settings.gigachat_enabled:
        logger.info("GigaChat is disabled in settings")
        return None

    if not settings.gigachat_api_key:
        logger.warning("GigaChat API key not configured")
        return None

    try:
        # Создаем клиент с отключенной SSL проверкой для тестирования
        client = GigaChatClient(verify_ssl=False)
        logger.info(
            "GigaChat client created successfully (authentication will happen on demand)")
        return client
    except Exception as e:
        logger.error(f"Failed to create GigaChat client: {e}")
        return None


@lru_cache(maxsize=1)
def get_speech_pipeline() -> SpeechAnalysisPipeline:
    """
    Создаёт и кеширует единственный экземпляр пайплайна на процесс.
    Включает GigaChat клиент, если настроен и включен.
    """
    transcriber = get_transcriber()
    analyzer = get_analyzer()
    gigachat_client = get_gigachat_client()

    logger.info(f"Initializing speech pipeline (GigaChat: {
                'enabled' if gigachat_client else 'disabled'})")

    if gigachat_client:
        logger.info(f"GigaChat client created: {
                    gigachat_client.__class__.__name__}")
        # Пробуем предварительную аутентификацию
        try:
            import asyncio
            # Запускаем в отдельной таске, чтобы не блокировать
            asyncio.create_task(gigachat_client.authenticate())
            logger.info("GigaChat pre-authentication started")
        except Exception as e:
            logger.warning(f"GigaChat pre-authentication failed: {e}")
    else:
        logger.info(
            "GigaChat client is None, GigaChat analysis will not be available")

    return SpeechAnalysisPipeline(
        transcriber=transcriber,
        analyzer=analyzer,
        gigachat_client=gigachat_client,
    )
