from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, validator
import json


class Settings(BaseSettings):
    # Путь к ffmpeg (по умолчанию просто "ffmpeg" из PATH)
    ffmpeg_path: str = Field(default="ffmpeg", alias="FFMPEG_PATH")

    # Настройки локального Whisper (faster-whisper)
    whisper_model: str = Field(
        default="small", alias="WHISPER_MODEL"
    )
    whisper_device: str = Field(
        default="cpu", alias="WHISPER_DEVICE"
    )
    whisper_compute_type: str = Field(
        default="int8", alias="WHISPER_COMPUTE_TYPE"
    )

    # Настройки GigaChat API
    gigachat_enabled: bool = Field(
        default=False, alias="GIGACHAT_ENABLED"
    )
    gigachat_api_key: Optional[SecretStr] = Field(
        default=None, alias="GIGACHAT_API_KEY"
    )
    gigachat_base_url: str = Field(
        default="https://gigachat.devices.sberbank.ru/api/v1",
        alias="GIGACHAT_BASE_URL"
    )
    gigachat_model: str = Field(
        default="GigaChat", alias="GIGACHAT_MODEL"
    )
    gigachat_timeout: int = Field(
        default=30, alias="GIGACHAT_TIMEOUT"
    )
    gigachat_max_tokens: int = Field(
        default=2000, alias="GIGACHAT_MAX_TOKENS"
    )

    # Настройки валидации файлов
    max_file_size_mb: int = Field(
        default=100, alias="MAX_FILE_SIZE_MB"
    )
    allowed_video_extensions: List[str] = Field(
        default=[".mp4", ".mov", ".avi", ".mkv",
                 ".webm", ".flv", ".wmv", ".m4v"],
        alias="ALLOWED_VIDEO_EXTENSIONS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("max_file_size_mb")
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError("MAX_FILE_SIZE_MB must be positive")
        if v > 1024:  # 1GB max
            raise ValueError("MAX_FILE_SIZE_MB cannot exceed 1024 (1GB)")
        return v

    @validator("allowed_video_extensions", pre=True)
    def parse_allowed_extensions(cls, v):
        """Парсит значение в список расширений"""
        if v is None:
            return cls.__fields__["allowed_video_extensions"].default

        if isinstance(v, str):
            try:
                # Сначала пробуем как JSON
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    v = parsed
                else:
                    # Если не JSON, то как строку с разделителями
                    v = [ext.strip() for ext in v.split(",") if ext.strip()]
            except json.JSONDecodeError:
                # Если не JSON, то как строку с разделителями
                v = [ext.strip() for ext in v.split(",") if ext.strip()]

        # Убедимся, что расширения начинаются с точки и в нижнем регистре
        if isinstance(v, list):
            validated = []
            for ext in v:
                if isinstance(ext, str):
                    if not ext.startswith("."):
                        ext = f".{ext}"
                    validated.append(ext.lower())
            return validated

        return v


settings = Settings()
