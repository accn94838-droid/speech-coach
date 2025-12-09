#!/usr/bin/env python3
"""
Создает тестовое видео для проверки работы приложения.
"""

import subprocess
import tempfile
from pathlib import Path
import wave
import sys


def create_test_video(duration_sec: int = 10, output_path: Path = Path("test_video.mp4")):
    """Создает тестовое видео с тишиной"""

    temp_dir = tempfile.mkdtemp()

    try:
        # 1. Создаем аудио файл с тишиной
        audio_path = Path(temp_dir) / "audio.wav"

        with wave.open(str(audio_path), 'wb') as wav:
            wav.setnchannels(1)  # Моно
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(16000)  # 16kHz
            # Тишина
            wav.writeframes(b'\x00' * 16000 * 2 * duration_sec)

        print(f"Created audio file: {audio_path}")

        # 2. Создаем видео из цветного фона и аудио
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s=640x480:d={duration_sec}',
            '-i', str(audio_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-shortest',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]

        print(f"Creating video with command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Test video created: {output_path}")
            print(f"File size: {
                  output_path.stat().st_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return False
    finally:
        # Очистка временных файлов
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_video_with_voice():
    """Создает видео с тестовой речью (требует текст в речь)"""
    print("Этот метод требует TTS систему. Используйте простой метод выше.")
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])
    else:
        output_path = Path("test_video.mp4")

    success = create_test_video(output_path=output_path)

    if success:
        print(f"\n🎬 Тестовое видео готово: {output_path}")
        print("Используйте его для тестирования API:")
        print(f"curl -X POST http://127.0.0.1:8000/api/v1/analyze \\")
        print(f"  -F \"file=@{output_path}\" \\")
        print(f"  -H \"accept: application/json\"")
    else:
        print("\n❌ Не удалось создать тестовое видео")
        print("Убедитесь, что ffmpeg установлен и доступен в PATH")
