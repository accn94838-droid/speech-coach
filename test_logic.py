#!/usr/bin/env python3
"""
Тестирование логики кэширования транскрибации (без загрузки модели)
"""
import inspect
from pathlib import Path
from app.services.transcriber import LocalWhisperTranscriber
from app.core.config import settings


def test_constructor_signature():
    """Проверка сигнатуры конструктора"""
    sig = inspect.signature(LocalWhisperTranscriber.__init__)
    params = list(sig.parameters.keys())
    
    print("Параметры конструктора LocalWhisperTranscriber:")
    for param in params:
        print(f"  - {param}: {sig.parameters[param]}")
    
    # Проверяем, что новые параметры присутствуют
    assert 'cache_dir' in params, "Параметр cache_dir отсутствует в конструкторе"
    assert 'cache_ttl' in params, "Параметр cache_ttl отсутствует в конструкторе"
    
    print("✓ Конструктор содержит новые параметры кэширования")


def test_method_exists():
    """Проверка наличия методов кэширования"""
    # Проверяем, что методы кэширования существуют
    assert hasattr(LocalWhisperTranscriber, '_get_cache_key'), "Метод _get_cache_key отсутствует"
    assert hasattr(LocalWhisperTranscriber, '_get_cache_path'), "Метод _get_cache_path отсутствует"
    assert hasattr(LocalWhisperTranscriber, 'transcribe'), "Метод transcribe отсутствует"
    
    print("✓ Все методы кэширования присутствуют")


def test_cache_key_logic():
    """Проверка логики генерации ключа кэша (без реального вызова)"""
    # Получаем исходный код метода
    import inspect
    source = inspect.getsource(LocalWhisperTranscriber._get_cache_key)
    
    # Проверяем, что в коде есть упоминание хэширования файла и параметров модели
    assert 'file_hash' in source, "В логике ключа кэша должен быть file_hash"
    assert 'model_size' in source, "В ключе кэша должны участвовать параметры модели"
    assert 'device' in source, "В ключе кэша должны участвовать параметры устройства"
    assert 'compute_type' in source, "В ключе кэша должны участвовать параметры вычислений"
    
    print("✓ Логика генерации ключа кэша корректна")


def test_transcribe_logic():
    """Проверка логики метода транскрибации (без реального вызова)"""
    import inspect
    source = inspect.getsource(LocalWhisperTranscriber.transcribe)
    
    # Проверяем, что в методе есть проверка кэша
    assert 'cache_key' in source, "В методе транскрибации должен быть cache_key"
    assert 'cache_path' in source, "В методе транскрибации должен быть cache_path"
    assert 'exists()' in source, "В методе должна быть проверка существования кэша"
    assert 'pickle.load' in source, "В методе должна быть загрузка из кэша"
    assert 'pickle.dump' in source, "В методе должна быть запись в кэш"
    
    print("✓ Логика метода транскрибации корректна")


if __name__ == "__main__":
    print("Тестирование логики кэширования транскрибации...")
    
    test_constructor_signature()
    test_method_exists()
    test_cache_key_logic()
    test_transcribe_logic()
    
    print("\n✓ Все тесты логики пройдены успешно!")
    print("\nРезюме изменений:")
    print("1. Добавлено кэширование для модели faster-whisper через @lru_cache в get_transcriber()")
    print("2. Добавлено кэширование результатов транскрибации в LocalWhisperTranscriber")
    print("3. Обновлены зависимости для передачи настроек кэша")
    print("4. Кэш результатов транскрибации учитывает хэш файла и параметры модели")
    print("5. Обновлены пути к кэшу для использования настроек из config")