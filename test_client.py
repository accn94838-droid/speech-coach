#!/usr/bin/env python3
"""
Тестовый клиент для Speech Coach API.
Можно использовать для проверки работы сервера.
"""

import asyncio
import aiohttp
import json
import sys
from pathlib import Path
import mimetypes


async def test_health(api_url: str):
    """Тестирует health check эндпоинт"""
    print("🔍 Проверка health endpoint...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{api_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except aiohttp.ClientError as e:
            print(f"❌ Сервер недоступен: {e}")
            return False


async def test_analysis(api_url: str, video_path: str, timeout: int = 300):
    """Тестирует эндпоинт анализа"""
    if not Path(video_path).exists():
        print(f"❌ Файл не найден: {video_path}")
        return False

    print(f"\n📤 Отправка файла {video_path} на анализ...")

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        # Определяем MIME-тип файла
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type:
            mime_type = "video/mp4"

        form_data = aiohttp.FormData()
        form_data.add_field(
            'file',
            open(video_path, 'rb'),
            filename=Path(video_path).name,
            content_type=mime_type
        )

        try:
            async with session.post(
                f"{api_url}/api/v1/analyze",
                data=form_data
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    print("\n✅ Анализ успешен!")
                    print(f"📊 Длительность: {result['duration_sec']:.1f} сек")
                    print(f"📝 Слов: {result['words_total']}")
                    print(f"⚡ Темп: {result['words_per_minute']:.1f} слов/мин")

                    if result.get('filler_words'):
                        fillers = result['filler_words']
                        print(
                            f"🗣️  Слова-паразиты: {fillers['total']} ({fillers['per_100_words']:.1f} на 100 слов)")

                    if result.get('gigachat_analysis'):
                        print("\n🤖 AI-анализ (GigaChat):")
                        print(f"   📈 Общая оценка: {
                              result['gigachat_analysis']['overall_assessment'][:200]}...")
                        if result['gigachat_analysis']['strengths']:
                            print(f"   ✅ Сильные стороны: {
                                  result['gigachat_analysis']['strengths'][0]}")

                    # Сохраняем результат в файл
                    output_file = f"result_{Path(video_path).stem}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"\n💾 Результат сохранен в {output_file}")
                    return True

                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка: {response.status}")
                    try:
                        error_json = json.loads(error_text)
                        print(f"   Детали: {
                              error_json.get('detail', error_text)}")
                    except:
                        print(f"   Детали: {error_text}")
                    return False

        except aiohttp.ClientError as e:
            print(f"❌ Ошибка соединения: {e}")
            return False
        except asyncio.TimeoutError:
            print(f"❌ Таймаут ({timeout} секунд)")
            return False


async def test_invalid_file(api_url: str):
    """Тестирует обработку невалидных файлов"""
    print("\n🧪 Тестирование обработки невалидных файлов...")

    async with aiohttp.ClientSession() as session:
        # Тест 1: Слишком большой файл (симулируем)
        print("1. Тест слишком большого файла...")
        form_data = aiohttp.FormData()
        form_data.add_field('file', b'x' * 150 * 1024 *
                            1024, filename='large.mp4')

        async with session.post(f"{api_url}/api/v1/analyze", data=form_data) as response:
            if response.status == 400:
                error = await response.json()
                if "exceeds maximum" in error.get('detail', ''):
                    print("   ✅ Правильно отвергает большой файл")
                else:
                    print(f"   ⚠️  Неожиданная ошибка: {error}")
            else:
                print(f"   ❌ Ожидалась ошибка 400, получили {response.status}")

        # Тест 2: Неподдерживаемый формат
        print("2. Тест неподдерживаемого формата...")
        form_data = aiohttp.FormData()
        form_data.add_field('file', b'test content', filename='test.pdf')

        async with session.post(f"{api_url}/api/v1/analyze", data=form_data) as response:
            if response.status == 400:
                error = await response.json()
                if "not supported" in error.get('detail', ''):
                    print("   ✅ Правильно отвергает неподдерживаемый формат")
                else:
                    print(f"   ⚠️  Неожиданная ошибка: {error}")
            else:
                print(f"   ❌ Ожидалась ошибка 400, получили {response.status}")


async def main():
    """Основная функция тестового клиента"""
    api_url = "http://127.0.0.1:8000"

    print("=" * 60)
    print("Speech Coach API - Тестовый клиент")
    print("=" * 60)

    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "health":
            await test_health(api_url)
            return

        elif command == "test":
            # Тестируем различные сценарии
            if not await test_health(api_url):
                return

            await test_invalid_file(api_url)
            return

        elif command == "help":
            print("\n📖 Использование:")
            print(
                f"  {sys.argv[0]} health              - Проверка доступности сервера")
            print(
                f"  {sys.argv[0]} test               - Тестирование валидации файлов")
            print(f"  {sys.argv[0]} <путь_к_файлу>     - Анализ видеофайла")
            print(f"  {sys.argv[0]} help               - Эта справка")
            print("\nПримеры:")
            print(f"  {sys.argv[0]} health")
            print(f"  {sys.argv[0]} test")
            print(f"  {sys.argv[0]} my_speech.mp4")
            return

        else:
            # Предполагаем, что это путь к файлу
            video_path = command
            if Path(video_path).exists():
                if not await test_health(api_url):
                    return
                await test_analysis(api_url, video_path)
            else:
                print(f"❌ Файл не найден: {video_path}")
                print(f"Используйте: {sys.argv[0]} help для справки")
    else:
        # Интерактивный режим
        if not await test_health(api_url):
            return

        print("\n📂 Введите путь к видеофайлу для анализа")
        print("   Или команду: test, health, help")
        print("   Или нажмите Enter для выхода")

        while True:
            try:
                user_input = input("\n> ").strip()

                if not user_input:
                    print("Выход...")
                    break

                elif user_input.lower() == "health":
                    await test_health(api_url)

                elif user_input.lower() == "test":
                    await test_invalid_file(api_url)

                elif user_input.lower() == "help":
                    print("\nДоступные команды:")
                    print("  health - Проверка доступности сервера")
                    print("  test   - Тестирование валидации файлов")
                    print("  help   - Эта справка")
                    print("  <путь> - Анализ видеофайла")
                    print("  Enter  - Выход")

                else:
                    # Предполагаем, что это путь к файлу
                    if Path(user_input).exists():
                        await test_analysis(api_url, user_input)
                    else:
                        print(f"❌ Файл не найден: {user_input}")

            except KeyboardInterrupt:
                print("\n\nВыход...")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
