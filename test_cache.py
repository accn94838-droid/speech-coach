#!/usr/bin/env python3
"""
Тестирование кэширования транскрибации
"""
import asyncio
from pathlib import Path
from app.services.transcriber import LocalWhisperTranscriber
from app.core.config import settings


async def test_transcription_cache():
    """Тестирование кэширования транскрибации"""
    print("Создание транскрибера с кэшированием...")
    
    # Создаем транскрибер с кэшированием
    transcriber = LocalWhisperTranscriber(
        cache_dir=Path(settings.cache_dir),
        cache_ttl=settings.cache_ttl
    )
    
    print(f"Модель загружена: {transcriber.model_size}")
    print(f"Кэш директория: {transcriber.cache_dir}")
    print(f"TTL кэша: {transcriber.cache_ttl} секунд")
    
    # Создаем тестовый аудиофайл (пустой для тестирования кэша)
    test_audio = Path("test_empty.wav")
    
    # Создаем простой WAV файл с заголовком
    with open(test_audio, "wb") as f:
        # Простой WAV заголовок для пустого файла
        f.write(b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
    
    try:
        print(f"Транскрибация файла {test_audio}...")
        result1 = transcriber.transcribe(test_audio)
        print("Первая транскрибация завершена")
        
        print(f"Повторная транскрибация файла {test_audio}...")
        result2 = transcriber.transcribe(test_audio)
        print("Вторая транскрибация завершена")
        
        # Проверяем, что результаты одинаковы (означает использование кэша)
        print(f"Результаты одинаковы: {result1.text == result2.text}")
        
        # Проверяем файлы кэша
        cache_files = list(transcriber.cache_dir.glob("*.pkl"))
        print(f"Файлов кэша: {len(cache_files)}")
        
    finally:
        # Удаляем тестовый файл
        if test_audio.exists():
            test_audio.unlink()
        
        # Удаляем кэш файлы
        for cache_file in transcriber.cache_dir.glob("*.pkl"):
            cache_file.unlink()
            print(f"Удален кэш файл: {cache_file}")


if __name__ == "__main__":
    asyncio.run(test_transcription_cache())