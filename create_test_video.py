#!/usr/bin/env python3
"""
Создаёт минимальный тестовый видеофайл для демонстрации.
Требует установленного ffmpeg.
"""

import subprocess
import os
from pathlib import Path


def create_test_video(output_path: str = "test_video.mp4", duration: int = 5):
    """
    Создаёт тестовый видеофайл с чёрным экраном и синусоидальным тоном.

    Args:
        output_path: Путь для сохранения видео
        duration: Длительность в секундах
    """
    print(f"Создаю тестовое видео: {output_path} ({duration} секунд)")

    # Проверяем наличие ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg не найден. Установите ffmpeg для создания тестового видео.")
        print("   Ubuntu/Debian: sudo apt install ffmpeg")
        print("   macOS: brew install ffmpeg")
        print("   Windows: скачайте с ffmpeg.org")
        return False

    # Создаём тестовое видео с чёрным экраном и тоном 440 Гц
    cmd = [
        "ffmpeg",
        "-y",  # Перезаписать без подтверждения
        "-f", "lavfi",
        "-i", f"color=c=black:s=640x480:d={duration}",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    try:
        print("⏳ Генерирую видео...")
        result = subprocess.run(cmd,
                                capture_output=True,
                                text=True,
                                check=True)

        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"✅ Тестовое видео создано: {output_path}")
            print(f"   Размер: {file_size:.2f} MB")
            print(f"   Длительность: {duration} секунд")
            return True
        else:
            print("❌ Не удалось создать видео")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании видео: {e}")
        print(f"stderr: {e.stderr}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    else:
        output_path = "test_video.mp4"
        duration = 5

    create_test_video(output_path, duration)
