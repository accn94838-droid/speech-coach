import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.deps import get_gigachat_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения.
    """
    logger.info("Starting Speech Coach API")

    gigachat_client = get_gigachat_client()
    if gigachat_client:
        logger.info("GigaChat client initialized and ready")
        # Предварительная аутентификация
        try:
            await gigachat_client.authenticate()
        except Exception as e:
            logger.error(f"GigaChat pre-authentication failed: {e}")
    else:
        logger.info("GigaChat client not available")

    yield

    logger.info("Shutting down Speech Coach API")

    if gigachat_client:
        try:
            await gigachat_client.close()
            logger.info("GigaChat client closed successfully")
        except Exception as e:
            logger.error(f"Error closing GigaChat client: {e}")
