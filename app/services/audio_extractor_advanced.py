"""
Продвинутый экстрактор аудио с обработкой ошибок и логированием.
"""

import subprocess
import logging
import threading
import time
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    """Исключение для таймаута"""
    pass


class AdvancedFfmpegAudioExtractor:
    def __init__(self, ffmpeg_path: str | None = None):
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"
        self._process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()

    def extract(self, video_path: Path, audio_path: Path, timeout: int = 600) -> None:
        """
        Извлекает аудио с обработкой таймаутов и лучшим управлением процессом.
        """
        logger.info(f"Extracting audio from {
                    video_path.name} (timeout: {timeout}s)")

        # Убедимся, что видеофайл существует
        if not video_path.exists():
            raise RuntimeError(f"Video file does not exist: {video_path}")

        # Проверим размер видеофайла
        video_size = video_path.stat().st_size
        if video_size == 0:
            raise RuntimeError(f"Video file is empty: {video_path}")

        logger.info(f"Video file size: {video_size:,} bytes")

        # Удаляем старый аудиофайл если существует (это причина кода 183!)
        if audio_path.exists():
            try:
                audio_path.unlink()
                logger.debug(f"Deleted existing audio file: {audio_path}")
            except Exception as e:
                logger.warning(f"Could not delete existing audio file: {e}")

        cmd = [
            self.ffmpeg_path,
            "-y",  # Критически важно: разрешить перезапись
            "-i", str(video_path),
            "-vn",  # Без видео
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-hide_banner",
            "-loglevel", "error",  # Только ошибки
            "-nostats",
            str(audio_path)
        ]

        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        def run_ffmpeg():
            """Запускает ffmpeg в отдельном потоке"""
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )

                # Читаем stderr для прогресса и ошибок
                stderr_lines = []
                while not self._stop_event.is_set():
                    line = self._process.stderr.readline()
                    if not line and self._process.poll() is not None:
                        break
                    if line:
                        stderr_lines.append(line.strip())
                        logger.debug(f"FFmpeg: {line.strip()}")

                # Ждём завершения
                stdout, stderr = self._process.communicate()
                return_code = self._process.returncode

                if return_code != 0:
                    # Собираем все сообщения об ошибках
                    error_msg = '\n'.join(
                        stderr_lines) if stderr_lines else f"FFmpeg exited with code {return_code}"
                    logger.error(
                        f"FFmpeg error (code {return_code}): {error_msg}")

                    # Распространенные коды ошибок FFmpeg
                    if return_code == 1:
                        error_msg = f"General FFmpeg error: {error_msg}"
                    elif return_code == 183:
                        error_msg = f"File already exists or permission denied: {
                            error_msg}"
                    elif return_code == 127:
                        error_msg = f"FFmpeg command not found: {
                            self.ffmpeg_path}"

                    raise RuntimeError(f"FFmpeg failed: {error_msg}")

            except Exception as e:
                logger.error(f"FFmpeg thread exception: {e}")
                raise

        # Запускаем ffmpeg в отдельном потоке
        ffmpeg_thread = threading.Thread(target=run_ffmpeg)
        ffmpeg_thread.daemon = True
        ffmpeg_thread.start()

        # Ждём завершения с таймаутом
        ffmpeg_thread.join(timeout=timeout)

        if ffmpeg_thread.is_alive():
            # Таймаут - убиваем процесс
            logger.error(f"FFmpeg timeout after {timeout} seconds")
            self._stop_event.set()

            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except:
                    if self._process.poll() is None:
                        self._process.kill()

            ffmpeg_thread.join(timeout=5)
            raise TimeoutException(
                f"Audio extraction timeout after {timeout} seconds")

        # Проверяем результат
        if not audio_path.exists():
            raise RuntimeError(f"Audio file was not created: {audio_path}")

        file_size = audio_path.stat().st_size
        if file_size == 0:
            raise RuntimeError(f"Extracted audio file is empty: {audio_path}")

        logger.info(f"Audio extracted: {
                    audio_path.name} ({file_size:,} bytes)")

    def __del__(self):
        """Деструктор - гарантируем завершение процесса"""
        self._stop_event.set()
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except:
                pass
