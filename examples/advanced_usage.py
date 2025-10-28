#!/usr/bin/env python3
"""
Продвинутый пример использования skopeo-wrapper
"""

from skopeo_wrapper import SkopeoWrapper, ProgressInfo, get_progress_percentage
import json
import os
import time


def detailed_progress_callback(progress: ProgressInfo):
    """Детальный callback для отображения прогресса"""
    print(f"\n📊 Прогресс операции:")
    print(f"   Операция: {progress.operation}")
    print(f"   Текущий этап: {progress.current_step}")
    
    if progress.parser:
        print(f"   Blob'ов обработано: {len(progress.parser.blobs)}")
        for sha256, blob in progress.parser.blobs.items():
            print(f"     - {sha256[:16]}... ({blob.status})")
    
    print(f"   Манифест записан: {'✅' if progress.manifest_written else '❌'}")
    print(f"   Подписи сохранены: {'✅' if progress.signatures_stored else '❌'}")
    
    if progress.current_blob:
        print(f"   Текущий blob: {progress.current_blob.sha256[:16]}...")
        if progress.current_blob.size:
            print(f"   Размер: {progress.current_blob.size} bytes")
    
    if progress.error:
        print(f"   ❌ Ошибка: {progress.error}")
    elif progress.completed:
        print(f"   ✅ Завершено!")
    else:
        # Используем функцию для расчета прогресса
        if progress.parser:
            percentage = get_progress_percentage(progress, progress.parser)
        else:
            # Fallback к базовой оценке
            if progress.current_step == "getting_signatures":
                percentage = 10.0
            elif progress.current_step == "copying_blob":
                percentage = 50.0
            elif progress.current_step == "copying_config":
                percentage = 75.0
            elif progress.current_step == "writing_manifest":
                percentage = 90.0
            elif progress.current_step == "storing_signatures":
                percentage = 95.0
            else:
                percentage = 0.0
        print(f"   📈 Прогресс: {percentage:.1f}%")


def main():
    """Основная функция продвинутого примера"""
    print("🚀 Продвинутый пример использования skopeo-wrapper")
    print("=" * 60)
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Создаем директорию для тестов
    test_dir = "/tmp/skopeo_advanced_example"
    os.makedirs(test_dir, exist_ok=True)
    
    # Пример 1: Копирование с детальным мониторингом
    print("\n1️⃣ Копирование ubuntu:22.04 с детальным мониторингом...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/ubuntu:22.04",
        destination=f"dir:{test_dir}/ubuntu",
        progress_callback=detailed_progress_callback
    )
    
    if success:
        print("✅ Копирование ubuntu завершено!")
    else:
        print(f"❌ Ошибка копирования ubuntu: {stderr}")
    
    # Пример 2: Копирование с таймаутом
    print("\n2️⃣ Копирование alpine:latest с таймаутом...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=f"dir:{test_dir}/alpine",
        timeout=60  # 60 секунд таймаут
    )
    
    if success:
        print("✅ Копирование alpine завершено!")
    else:
        print(f"❌ Ошибка копирования alpine: {stderr}")
    
    # Пример 3: Массовое копирование образов
    print("\n3️⃣ Массовое копирование образов...")
    images = [
        "docker://docker.io/library/nginx:alpine",
        "docker://docker.io/library/redis:alpine",
        "docker://docker.io/library/postgres:alpine"
    ]
    
    for i, image in enumerate(images, 1):
        image_name = image.split('/')[-1].replace(':', '_')
        print(f"\n   Копирование {image}...")
        
        success, stdout, stderr = skopeo.copy(
            source=image,
            destination=f"dir:{test_dir}/{image_name}"
        )
        
        if success:
            print(f"   ✅ {image_name} скопирован успешно!")
        else:
            print(f"   ❌ Ошибка копирования {image_name}: {stderr}")
    
    # Пример 4: Анализ метаданных образов
    print("\n4️⃣ Анализ метаданных образов...")
    for image in images:
        print(f"\n   Анализ {image}...")
        success, image_info, stderr = skopeo.inspect(image=image)
        
        if success:
            try:
                info = json.loads(image_info)
                print(f"   📋 {image}:")
                print(f"     Архитектура: {info.get('Architecture', 'N/A')}")
                print(f"     ОС: {info.get('Os', 'N/A')}")
                print(f"     Размер: {info.get('Size', 'N/A')} bytes")
                print(f"     Слоев: {len(info.get('Layers', []))}")
            except json.JSONDecodeError:
                print(f"   ❌ Ошибка парсинга метаданных для {image}")
        else:
            print(f"   ❌ Ошибка получения метаданных для {image}: {stderr}")
    
    print("\n" + "=" * 60)
    print("🏁 Продвинутый пример завершен!")
    print(f"📁 Результаты сохранены в: {test_dir}")
    
    # Показываем размер результатов
    total_size = 0
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    
    print(f"📊 Общий размер скопированных образов: {total_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
