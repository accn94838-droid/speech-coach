import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import logging

from fastapi import UploadFile

from app.services.audio_extractor import AudioExtractor
from app.services.transcriber import Transcriber
from app.services.analyzer import SpeechAnalyzer
from app.services.gigachat import GigaChatClient
from app.models.analysis import AnalysisResult
from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    TranscriptionError,
    AnalysisError,
)

logger = logging.getLogger(__name__)


class SpeechAnalysisPipeline:
    """
    Координирует:
    - валидацию загружаемого файла,
    - сохранение во временный файл,
    - извлечение аудио,
    - транскрибацию,
    - анализ,
    - расширенный анализ через GigaChat (если включен).
    """

    def __init__(
        self,
        audio_extractor: AudioExtractor,
        transcriber: Transcriber,
        analyzer: SpeechAnalyzer,
        gigachat_client: Optional[GigaChatClient] = None,
    ):
        self.audio_extractor = audio_extractor
        self.transcriber = transcriber
        self.analyzer = analyzer
        self.gigachat_client = gigachat_client

    async def analyze_upload(self, file: UploadFile) -> AnalysisResult:
        """
        Анализирует загруженное видео и возвращает результаты.
        Включает расширенный анализ через GigaChat, если настроен.
        """
        # Валидация файла перед обработкой
        await self._validate_file(file)

        suffix = Path(file.filename or "video").suffix or ".mp4"

        tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_video_path = Path(tmp_video.name)
        tmp_video.close()

        await self._save_upload_to_path(file, temp_video_path)

        temp_audio_path = temp_video_path.with_suffix(".wav")

        try:
            # 1) Извлекаем аудио из видео
            logger.info(f"Extracting audio from {temp_video_path}")
            self.audio_extractor.extract(temp_video_path, temp_audio_path)

            # 2) Транскрибируем аудио
            logger.info("Transcribing audio...")
            try:
                transcript = self.transcriber.transcribe(temp_audio_path)
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                raise TranscriptionError(
                    f"Failed to transcribe audio: {str(e)}")

            # 3) Анализируем с учётом пути к аудио (для оценки пауз)
            logger.info("Analyzing speech metrics...")
            try:
                result = self.analyzer.analyze(
                    transcript, audio_path=temp_audio_path)
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                raise AnalysisError(f"Failed to analyze speech: {str(e)}")

            # 4) Запрашиваем расширенный анализ через GigaChat, если настроен
            if self.gigachat_client:
                logger.info("Requesting GigaChat analysis...")
                try:
                    gigachat_analysis = await self.gigachat_client.analyze_speech(result)
                    if gigachat_analysis:
                        result.gigachat_analysis = gigachat_analysis
                        logger.info("GigaChat analysis completed successfully")
                    else:
                        logger.warning("GigaChat analysis returned no results")
                except Exception as e:
                    logger.error(f"GigaChat analysis failed: {e}")
                    # Не прерываем основной анализ из-за ошибки GigaChat
                    # Можно добавить поле с ошибкой GigaChat в результат, если нужно

            logger.info("Analysis completed successfully")
            return result

        finally:
            # Удаляем временные файлы
            self._cleanup_temp_files(temp_video_path, temp_audio_path)

    async def _validate_file(self, file: UploadFile) -> None:
        """Валидирует загруженный файл"""
        if not file.filename:
            raise UnsupportedFileTypeError(
                file_extension="unknown",
                allowed_extensions=settings.allowed_video_extensions
            )

        # Проверка расширения файла
        file_ext = Path(file.filename).suffix.lower()
        if not file_ext:
            raise UnsupportedFileTypeError(
                file_extension="no extension",
                allowed_extensions=settings.allowed_video_extensions
            )

        if file_ext not in settings.allowed_video_extensions:
            raise UnsupportedFileTypeError(
                file_extension=file_ext,
                allowed_extensions=settings.allowed_video_extensions
            )

        # Проверка размера файла
        await self._validate_file_size(file)

    async def _validate_file_size(self, file: UploadFile) -> None:
        """Проверяет размер файла"""
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024

        # Сначала пытаемся получить размер из заголовка Content-Length
        if hasattr(file, 'size'):
            file_size = file.size
        else:
            # Если размер не указан, читаем файл для определения размера
            file.file.seek(0, 2)  # Перемещаемся в конец файла
            file_size = file.file.tell()
            file.file.seek(0)  # Возвращаемся в начало

        if file_size > max_size_bytes:
            file_size_mb = file_size / (1024 * 1024)
            raise FileTooLargeError(
                file_size_mb=file_size_mb,
                max_size_mb=settings.max_file_size_mb
            )

    @staticmethod
    async def _save_upload_to_path(upload: UploadFile, dst: Path) -> None:
        """Сохраняет загруженный файл на диск"""
        upload.file.seek(0)
        with dst.open("wb") as out_file:
            # Используем chunked чтение для больших файлов
            chunk_size = 1024 * 1024  # 1 MB
            while True:
                chunk = upload.file.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
        await upload.close()

    @staticmethod
    def _cleanup_temp_files(*paths: Path) -> None:
        """Удаляет временные файлы"""
        for path in paths:
            try:
                if path.exists():
                    os.remove(path)
                    logger.debug(f"Deleted temp file: {path}")
            except OSError as e:
                logger.warning(f"Failed to delete temp file {path}: {e}")
