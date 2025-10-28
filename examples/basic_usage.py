#!/usr/bin/env python3
"""
Базовый пример использования skopeo-wrapper
"""

from skopeo_wrapper import SkopeoWrapper, create_progress_callback
import json
import os


def main():
    """Основная функция примера"""
    print("🚀 Базовый пример использования skopeo-wrapper")
    print("=" * 50)
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Создаем директорию для тестов
    test_dir = "/tmp/skopeo_example"
    os.makedirs(test_dir, exist_ok=True)
    
    # Пример 1: Копирование образа с прогрессом
    print("\n📦 Копирование образа alpine:latest...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=f"dir:{test_dir}/alpine",
        progress_callback=create_progress_callback(show_progress=True)
    )
    
    if success:
        print("✅ Копирование завершено успешно!")
    else:
        print(f"❌ Ошибка копирования: {stderr}")
        return
    
    # Пример 2: Получение информации об образе
    print("\n🔍 Получение информации об образе...")
    success, image_info, stderr = skopeo.inspect(
        image="docker://docker.io/library/alpine:latest",
        progress_callback=create_progress_callback(show_progress=True)
    )
    
    if success:
        try:
            info = json.loads(image_info)
            print("📋 Информация об образе:")
            print(f"   Архитектура: {info.get('Architecture', 'N/A')}")
            print(f"   ОС: {info.get('Os', 'N/A')}")
            print(f"   Создан: {info.get('Created', 'N/A')}")
            print(f"   Размер: {info.get('Size', 'N/A')} bytes")
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
    else:
        print(f"❌ Ошибка получения информации: {stderr}")
    
    # Пример 3: Получение digest манифеста
    print("\n🔐 Получение digest манифеста...")
    success, digest, stderr = skopeo.get_manifest_digest(
        image="docker://docker.io/library/alpine:latest",
        progress_callback=create_progress_callback(show_progress=True)
    )
    
    if success:
        print(f"📄 Digest манифеста: {digest.strip()}")
    else:
        print(f"❌ Ошибка получения digest: {stderr}")
    
    print("\n" + "=" * 50)
    print("🏁 Пример завершен!")
    print(f"📁 Скопированные образы находятся в: {test_dir}")


if __name__ == "__main__":
    main()
