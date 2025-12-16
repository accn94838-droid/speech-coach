import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Optional
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Кеш для результатов анализа"""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        """
        Args:
            cache_dir: Директория для кеша
            ttl_seconds: Время жизни кеша в секундах
        """
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, data: bytes) -> str:
        """Генерирует ключ кеша на основе данных"""
        return hashlib.sha256(data).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Возвращает путь к файлу кеша"""
        return self.cache_dir / f"{key}.cache"

    def get(self, data: bytes) -> Optional[Any]:
        """Получает данные из кеша"""
        key = self._get_cache_key(data)
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            # Проверяем TTL
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime > self.ttl_seconds:
                cache_file.unlink()
                return None

            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                logger.debug(f"Кеш hit: {key}")
                return cached_data

        except Exception as e:
            logger.warning(f"Ошибка чтения кеша: {e}")
            return None

    def set(self, data: bytes, result: Any) -> None:
        """Сохраняет данные в кеш"""
        key = self._get_cache_key(data)
        cache_file = self._get_cache_path(key)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Кеш set: {key}")
        except Exception as e:
            logger.warning(f"Ошибка записи в кеш: {e}")

    def clear_old(self) -> int:
        """Очищает старые записи кеша, возвращает количество удаленных"""
        deleted = 0
        now = time.time()

        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                mtime = cache_file.stat().st_mtime
                if now - mtime > self.ttl_seconds:
                    cache_file.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning(f"Ошибка удаления кеша {cache_file}: {e}")

        logger.info(f"Удалено {deleted} старых записей кеша")
        return deleted

    # --- Новые методы для работы по ключу (чтобы не держать весь файл в памяти) ---
    def get_by_key(self, key: str) -> Optional[Any]:
        cache_file = self._get_cache_path(key)
        if not cache_file.exists():
            return None
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime > self.ttl_seconds:
                cache_file.unlink()
                return None
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Ошибка чтения кеша: {e}")
            return None

    def set_by_key(self, key: str, result: Any) -> None:
        cache_file = self._get_cache_path(key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(f"Кеш set: {key}")
        except Exception as e:
            logger.warning(f"Ошибка записи в кеш: {e}")


def cache_analysis(ttl_hours: int = 1):
    """Декоратор для кеширования результатов анализа"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, file, *args, **kwargs):
            # Пропускаем кеширование если отключено
            if not getattr(self, 'cache', None):
                return await func(self, file, *args, **kwargs)

            # Читаем файл по частям и считаем sha256 для ключа кеша
            import hashlib
            sha = hashlib.sha256()
            try:
                await file.seek(0)
            except Exception:
                pass
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                sha.update(chunk)
            await file.seek(0)
            key = sha.hexdigest()
            
            # Добавляем флаг использования GigaChat в ключ кеша
            gigachat_enabled = getattr(self, 'gigachat_client', None) is not None
            key_with_gigachat = f"{key}_gigachat_{gigachat_enabled}"

            # Проверяем кеш по ключу
            # Offload file IO to thread to avoid blocking event loop
            import asyncio
            cached_result = await asyncio.to_thread(self.cache.get_by_key, key_with_gigachat)
            if cached_result is not None:
                logger.info(f"Используется кешированный результат для {file.filename}")
                return cached_result

            # Выполняем анализ
            result = await func(self, file, *args, **kwargs)

            # Сохраняем в кеш
            try:
                import asyncio
                await asyncio.to_thread(self.cache.set_by_key, key_with_gigachat, result)
            except Exception as e:
                logger.warning(f"Не удалось сохранить в кеш: {e}")

            return result
        return wrapper
    return decorator
