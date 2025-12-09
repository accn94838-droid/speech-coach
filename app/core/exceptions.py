"""
Кастомные исключения для приложения.
"""

from fastapi import HTTPException, status


class SpeechCoachException(HTTPException):
    """Базовое исключение для Speech Coach"""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class FileValidationError(SpeechCoachException):
    """Ошибка валидации файла"""

    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileTooLargeError(FileValidationError):
    """Файл слишком большой"""

    def __init__(self, file_size_mb: float, max_size_mb: int):
        detail = (
            f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed size "
            f"({max_size_mb} MB)"
        )
        super().__init__(detail=detail)


class UnsupportedFileTypeError(FileValidationError):
    """Неподдерживаемый тип файла"""

    def __init__(self, file_extension: str, allowed_extensions: list):
        detail = (
            f"File type '{file_extension}' is not supported. "
            f"Allowed types: {', '.join(allowed_extensions)}"
        )
        super().__init__(detail=detail)


class TranscriptionError(SpeechCoachException):
    """Ошибка транскрипции"""

    def __init__(self, detail: str = "Failed to transcribe audio"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalysisError(SpeechCoachException):
    """Ошибка анализа"""

    def __init__(self, detail: str = "Failed to analyze speech"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GigaChatError(SpeechCoachException):
    """Ошибка GigaChat API"""

    def __init__(self, detail: str = "GigaChat analysis failed"):
        super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
