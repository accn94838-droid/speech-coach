#!/usr/bin/env python3
"""
Тест с обработкой лимита запросов.
"""

import asyncio
import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_with_delay():
    """Тест с задержкой между запросами"""
    from app.api.deps import get_gigachat_client
    from app.models.analysis import AnalysisResult, FillerWordsStats, PausesStats, PhraseStats, AdviceItem

    print("="*60)
    print("ТЕСТ С ОБРАБОТКОЙ ЛИМИТА ЗАПРОСОВ")
    print("="*60)

    client = get_gigachat_client()

    if not client:
        print("❌ GigaChat client not available")
        return False

    # Ждем перед первым запросом
    print("\n1. Ждем 60 секунд перед запросом (чтобы обойти лимит)...")
    for i in range(60, 0, -1):
        print(f"\r   Осталось: {i} секунд", end="", flush=True)
        await asyncio.sleep(1)
    print("\n   Продолжаем...")

    # Создаем тестовые данные
    test_result = AnalysisResult(
        duration_sec=120.0,
        speaking_time_sec=95.0,
        speaking_ratio=0.79,
        words_total=250,
        words_per_minute=157.9,
        filler_words=FillerWordsStats(
            total=15,
            per_100_words=6.0,
            items=[
                {"word": "ну", "count": 8},
                {"word": "вот", "count": 4},
                {"word": "как бы", "count": 3}
            ]
        ),
        pauses=PausesStats(
            count=12,
            avg_sec=1.5,
            max_sec=3.0,
            long_pauses=[]
        ),
        phrases=PhraseStats(
            count=45,
            avg_words=5.6,
            avg_duration_sec=2.1,
            min_words=2,
            max_words=15,
            min_duration_sec=0.5,
            max_duration_sec=3.5,
            length_classification="balanced",
            rhythm_variation="moderately_variable"
        ),
        advice=[
            AdviceItem(
                category="speech_rate",
                severity="suggestion",
                title="Темп речи",
                observation="Темп речи немного выше оптимального",
                recommendation="Рекомендуется слегка замедлить темп"
            )
        ],
        transcript="Короткий тестовый транскрипт для проверки."
    )

    print("\n2. Отправляем запрос к GigaChat...")
    try:
        start_time = time.time()
        analysis = await client.analyze_speech(test_result)
        elapsed = time.time() - start_time

        if analysis:
            print(f"   ✅ Анализ получен за {elapsed:.1f} секунд")
            print(f"   Общая оценка: {analysis.overall_assessment[:100]}...")
            print(f"   Уверенность: {analysis.confidence_score}")

            # Проверяем наличие GigaChat анализа в полном результате
            full_result = AnalysisResult(
                **test_result.dict(),
                gigachat_analysis=analysis
            )

            print(f"\n3. Проверка полного результата:")
            print(f"   gigachat_analysis присутствует: {
                  full_result.gigachat_analysis is not None}")

            return True
        else:
            print("   ⚠️  GigaChat вернул None (возможно, лимит запросов)")
            return False

    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


async def test_api_with_real_file():
    """Тест API с реальным файлом"""
    import httpx
    import tempfile
    from pathlib import Path

    print("\n" + "="*60)
    print("ТЕСТ API С РЕАЛЬНЫМ ФАЙЛОМ")
    print("="*60)

    # Ждем перед запросом
    print("\nЖдем 60 секунд перед запросом к API...")
    for i in range(60, 0, -1):
        print(f"\r   Осталось: {i} секунд", end="", flush=True)
        await asyncio.sleep(1)

    # Создаем тестовый файл
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.mp4"

    with open(test_file, 'wb') as f:
        f.write(b'\x00\x00\x00\x1C667479706D703432000000006D70343269736F6D')
        f.write(b'\x00\x00\x00\x086D6F6F76')
        f.write(b'video_content' * 100)

    print(f"\n\nОтправляем запрос к API...")

    client = httpx.AsyncClient(timeout=120.0)

    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test.mp4', f, 'video/mp4')}

            response = await client.post(
                "http://127.0.0.1:8000/api/v1/analyze",
                files=files
            )

        print(f"Статус ответа: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            # Сохраняем результат
            import json
            with open("api_result_with_gigachat.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ Анализ успешен!")

            # Проверяем GigaChat анализ
            if result.get('gigachat_analysis'):
                print(f"✅ GIGACHAT АНАЛИЗ ПРИСУТСТВУЕТ!")
                gigachat = result['gigachat_analysis']
                print(f"   Общая оценка: {gigachat.get(
                    'overall_assessment', '')[:100]}...")
                print(f"   Уверенность: {gigachat.get('confidence_score', 0)}")
                return True
            else:
                print(f"⚠️  GigaChat анализ отсутствует в результате")
                print(f"   Возможные причины:")
                print(f"   1. Лимит запросов GigaChat")
                print(f"   2. Ошибка аутентификации")
                print(f"   3. settings.gigachat_enabled = False")
                return False
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Тело ответа: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при запросе: {e}")
        return False
    finally:
        await client.aclose()
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    """Основная функция"""
    print("Тестирование с учетом лимита запросов GigaChat...")

    # Тест 1: Прямой запрос с задержкой
    print("\n[ТЕСТ 1] Прямой запрос к GigaChat")
    test1 = await test_with_delay()

    # Ждем между тестами
    print("\nЖдем 30 секунд перед следующим тестом...")
    await asyncio.sleep(30)

    # Тест 2: Запрос через API
    print("\n[ТЕСТ 2] Запрос через API")
    test2 = await test_api_with_real_file()

    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"Тест 1 (прямой): {'✅ УСПЕХ' if test1 else '❌ ПРОВАЛ'}")
    print(f"Тест 2 (API): {'✅ УСПЕХ' if test2 else '❌ ПРОВАЛ'}")

    if test1 and test2:
        print("\n🎉 Все тесты пройдены! GigaChat работает корректно.")
        print("Проблема с лимитом запросов решена ожиданием.")
        return 0
    elif test1 and not test2:
        print("\n🔍 Проблема в интеграции с пайплайном.")
        print("GigaChat работает напрямую, но не через API.")
        return 1
    else:
        print("\n🔧 Требуется дополнительная настройка.")
        return 1


if __name__ == "__main__":
    # Проверяем, запущен ли сервер
    import subprocess
    import socket

    def check_server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        return result == 0

    if not check_server():
        print("⚠️  Сервер не запущен на порту 8000")
        print("Запустите сервер в отдельном терминале:")
        print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nЗапускаю тест только GigaChat...")

        # Запускаем только тест GigaChat без API
        async def test_gigachat_only():
            from app.api.deps import get_gigachat_client
            from app.models.analysis import AnalysisResult, FillerWordsStats, PausesStats, PhraseStats, AdviceItem

            print("\nЖдем 60 секунд для обхода лимита...")
            await asyncio.sleep(60)

            client = get_gigachat_client()
            if client:
                test_result = AnalysisResult(
                    duration_sec=120.0,
                    speaking_time_sec=95.0,
                    speaking_ratio=0.79,
                    words_total=250,
                    words_per_minute=157.9,
                    filler_words=FillerWordsStats(
                        total=15, per_100_words=6.0, items=[]),
                    pauses=PausesStats(count=12, avg_sec=1.5,
                                       max_sec=3.0, long_pauses=[]),
                    phrases=PhraseStats(
                        count=45, avg_words=5.6, avg_duration_sec=2.1,
                        min_words=2, max_words=15, min_duration_sec=0.5,
                        max_duration_sec=3.5, length_classification="balanced",
                        rhythm_variation="moderately_variable"
                    ),
                    advice=[],
                    transcript="Тест."
                )

                analysis = await client.analyze_speech(test_result)
                if analysis:
                    print(f"✅ GigaChat работает! Анализ: {
                          analysis.overall_assessment[:100]}...")
                    return True
                else:
                    print("❌ GigaChat вернул None")
                    return False
            else:
                print("❌ GigaChat client not available")
                return False

        exit_code = asyncio.run(test_gigachat_only())
        sys.exit(0 if exit_code else 1)
    else:
        print("✅ Сервер запущен, начинаем полное тестирование...")
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
