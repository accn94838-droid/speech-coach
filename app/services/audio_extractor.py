import subprocess
import logging
from pathlib import Path
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioExtractor(Protocol):
    def extract(self, video_path: Path, audio_path: Path) -> None:
        ...


class FfmpegAudioExtractor:
    def __init__(self, ffmpeg_path: str | None = None):
        self.ffmpeg_path = ffmpeg_path or settings.ffmpeg_path

    def extract(self, video_path: Path, audio_path: Path) -> None:
        """
        Извлекает моно WAV 16kHz из видео-файла с помощью ffmpeg.
        """
        cmd = [
            self.ffmpeg_path,
            "-y",  # Перезаписать без подтверждения
            "-i", str(video_path),
            "-vn",  # Без видео
            "-acodec", "pcm_s16le",
            "-ar", "16000",  # Частота дискретизации
            "-ac", "1",  # Моно
            "-hide_banner",  # Скрыть баннер ffmpeg
            "-loglevel", "quiet",  # ТИХИЙ режим - никакого вывода!
            "-nostats",  # Без статистики
            str(audio_path),
        ]

        logger.debug(f"Running ffmpeg: {' '.join(cmd)}")

        try:
            # Используем subprocess.run с DEVNULL для подавления вывода
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,  # Подавляем stdout
                stderr=subprocess.DEVNULL,  # Подавляем stderr
                timeout=300  # Таймаут 5 минут
            )

            logger.info(f"Audio extracted successfully: {audio_path}")

            # Проверяем, что файл создан и не пустой
            if audio_path.exists():
                file_size = audio_path.stat().st_size
                if file_size > 0:
                    logger.debug(f"Audio file size: {file_size} bytes")
                else:
                    raise RuntimeError("Extracted audio file is empty")
            else:
                raise RuntimeError("Audio file was not created")

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout (5 minutes)")
            raise RuntimeError(
                "Audio extraction timeout - video might be too long or corrupted")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed with code {e.returncode}")
            raise RuntimeError(
                f"Failed to extract audio (code: {e.returncode})")
        except FileNotFoundError:
            logger.error(f"FFmpeg not found at: {self.ffmpeg_path}")
            raise RuntimeError(
                f"FFmpeg not found. Please install ffmpeg and add to PATH")
