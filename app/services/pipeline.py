"""
Модуль пайплайна анализа речи.
Координирует обработку видеофайла: валидацию, извлечение аудио, транскрипцию, анализ.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import logging

from fastapi import UploadFile

from app.services.audio_extractor_advanced import AdvancedFfmpegAudioExtractor, TimeoutException
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
    Координирует весь процесс анализа речи:
    - валидацию загружаемого файла,
    - сохранение во временный файл,
    - извлечение аудио,
    - транскрибацию,
    - анализ,
    - расширенный анализ через GigaChat (если включен).
    """

    def __init__(
        self,
        transcriber: Transcriber,
        analyzer: SpeechAnalyzer,
        gigachat_client: Optional[GigaChatClient] = None,
    ):
        # Используем продвинутый экстрактор аудио
        self.audio_extractor = AdvancedFfmpegAudioExtractor()
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
            logger.info(f"Extracting audio from {temp_video_path.name}")
            try:
                self.audio_extractor.extract(
                    temp_video_path, temp_audio_path, timeout=300)
            except TimeoutException as e:
                logger.error(f"Audio extraction timeout: {e}")
                raise AnalysisError(
                    "Audio extraction took too long. Video might be too long or corrupted.")
            except RuntimeError as e:
                logger.error(f"Audio extraction failed: {e}")
                error_msg = str(e)
                if "file does not exist" in error_msg.lower():
                    raise AnalysisError("Video file is corrupted or empty")
                elif "already exists" in error_msg.lower():
                    raise AnalysisError(
                        "Temporary file conflict, please try again")
                elif "ffmpeg command not found" in error_msg.lower():
                    raise AnalysisError(
                        "FFmpeg is not installed or not in PATH")
                else:
                    raise AnalysisError(
                        f"Failed to extract audio: {error_msg}")
            except Exception as e:
                logger.error(f"Audio extraction failed: {e}")
                raise AnalysisError(f"Failed to extract audio: {str(e)}")

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
            if self.gigachat_client and settings.gigachat_enabled:
                logger.info("Requesting GigaChat analysis...")
                try:
                    gigachat_analysis = await self.gigachat_client.analyze_speech(result)
                    if gigachat_analysis:
                        logger.info(f"GigaChat analysis received: {
                                    gigachat_analysis.overall_assessment[:100]}...")

                        # Ключевое исправление: создаем новый AnalysisResult с gigachat_analysis
                        result = AnalysisResult(
                            duration_sec=result.duration_sec,
                            speaking_time_sec=result.speaking_time_sec,
                            speaking_ratio=result.speaking_ratio,
                            words_total=result.words_total,
                            words_per_minute=result.words_per_minute,
                            filler_words=result.filler_words,
                            pauses=result.pauses,
                            phrases=result.phrases,
                            advice=result.advice,
                            transcript=result.transcript,
                            gigachat_analysis=gigachat_analysis  # Добавляем анализ
                        )
                        logger.info(
                            "GigaChat analysis added to result successfully")
                    else:
                        logger.warning("GigaChat analysis returned None")
                except Exception as e:
                    logger.error(f"GigaChat analysis failed: {e}")
                    logger.info("Continuing without GigaChat analysis")

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

        file_size = None

        # Способ 1: Используем атрибут size, если он есть
        if hasattr(file, 'size'):
            file_size = file.size
            logger.debug(f"File size from attribute: {file_size} bytes")

        # Способ 2: Если нет атрибута size, пытаемся определить через seek/tell
        if file_size is None and hasattr(file.file, 'seekable') and file.file.seekable():
            try:
                # Сохраняем текущую позицию
                original_position = file.file.tell()

                # Переходим в конец файла
                file.file.seek(0, 2)  # SEEK_END
                file_size = file.file.tell()

                # Возвращаемся в исходную позицию
                file.file.seek(original_position)
                logger.debug(f"File size from seek/tell: {file_size} bytes")

            except (AttributeError, OSError) as e:
                logger.warning(
                    f"Could not determine file size via seek/tell: {e}")

        # Способ 3: Читаем содержимое файла для определения размера
        if file_size is None:
            logger.warning(
                "File size unknown, reading file to determine size...")
            try:
                # Читаем все содержимое файла
                content = await file.read()
                file_size = len(content)

                # Возвращаем указатель в начало файла
                await file.seek(0)
                logger.debug(f"File size from reading content: {
                             file_size} bytes")

            except Exception as e:
                logger.error(f"Failed to read file for size check: {e}")
                # Не прерываем выполнение из-за ошибки определения размера
                # Просто логируем и продолжаем
                logger.warning(
                    "Skipping file size validation due to read error")
                return

        # Теперь проверяем размер, если удалось его определить
        if file_size is not None:
            if file_size > max_size_bytes:
                file_size_mb = file_size / (1024 * 1024)
                raise FileTooLargeError(
                    file_size_mb=file_size_mb,
                    max_size_mb=settings.max_file_size_mb
                )
            else:
                logger.info(f"File size OK: {
                            file_size / (1024 * 1024):.2f} MB")
        else:
            logger.warning(
                "Could not determine file size, skipping size validation")

    @staticmethod
    async def _save_upload_to_path(upload: UploadFile, dst: Path) -> None:
        """Сохраняет загруженный файл на диск"""
        # Убедимся, что указатель в начале файла
        await upload.seek(0)

        with dst.open("wb") as out_file:
            # Используем chunked чтение для больших файлов
            chunk_size = 1024 * 1024  # 1 MB
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)

        logger.info(f"File saved to temporary location: {dst}")
        # Закрываем файл
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

    # Метод для обработки локальных файлов (для тестирования)
    async def analyze_local_file(self, video_path: Path) -> AnalysisResult:
        """
        Анализирует локальный видеофайл.
        Полезно для тестирования и отладки.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Создаем временный UploadFile для совместимости
        import io
        from fastapi import UploadFile as FastAPIUploadFile

        with open(video_path, 'rb') as f:
            content = f.read()

        # Создаем UploadFile с корректным размером
        file_bytes = io.BytesIO(content)
        upload_file = FastAPIUploadFile(
            filename=video_path.name,
            file=file_bytes,
            size=len(content)
        )

        # Используем основной метод
        return await self.analyze_upload(upload_file)
