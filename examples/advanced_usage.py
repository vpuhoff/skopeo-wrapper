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
    import sys
    
    timestamp = time.strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 📊 Прогресс операции:")
    print(f"   🔄 Операция: {progress.operation}")
    print(f"   📍 Текущий этап: {progress.current_step}")
    
    if progress.parser:
        print(f"   📦 Blob'ов обработано: {len(progress.parser.blobs)}")
        if progress.parser.blobs:
            print(f"   📋 Последние blob'ы:")
            for sha256, blob in list(progress.parser.blobs.items())[-3:]:  # Показываем последние 3
                status_emoji = "✅" if blob.status == "completed" else "🔄" if blob.status == "in_progress" else "⏳"
                size_mb = blob.size / 1024 / 1024 if blob.size else 0
                print(f"     {status_emoji} {sha256[:16]}... ({blob.status}) {size_mb:.1f}MB")
    
    print(f"   📄 Манифест записан: {'✅' if progress.manifest_written else '❌'}")
    print(f"   🔐 Подписи сохранены: {'✅' if progress.signatures_stored else '❌'}")
    
    if progress.current_blob:
        size_mb = progress.current_blob.size / 1024 / 1024 if progress.current_blob.size else 0
        print(f"   🎯 Текущий blob: {progress.current_blob.sha256[:16]}... ({size_mb:.1f}MB)")
    
    if progress.error:
        print(f"   ❌ Ошибка: {progress.error}")
    elif progress.completed:
        print(f"   🎉 Завершено!")
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
        
        # Создаем прогресс-бар
        bar_length = 20
        filled_length = int(bar_length * percentage / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"   📈 Прогресс: {bar} {percentage:.1f}%")
    
    # Принудительно сбрасываем буфер
    sys.stdout.flush()


def main():
    """Основная функция продвинутого примера"""
    print("🚀 Продвинутый пример использования skopeo-wrapper")
    print("=" * 60)
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Создаем директорию для тестов
    test_dir = "/tmp/skopeo_advanced_example"
    os.makedirs(test_dir, exist_ok=True)
    
    # Пример 1: Копирование с детальным мониторингом (используем локальный образ)
    print("\n1️⃣ Копирование alpine с детальным мониторингом...")
    print("   📥 Источник: dir:/tmp/skopeo_example/alpine")
    print("   📤 Назначение: dir:/tmp/skopeo_advanced_example/alpine_copy")
    print("   ⏱️  Начинаем копирование...")
    
    start_time = time.time()
    success, stdout, stderr = skopeo.copy(
        source="dir:/tmp/skopeo_example/alpine",
        destination=f"dir:{test_dir}/alpine_copy",
        progress_callback=detailed_progress_callback
    )
    end_time = time.time()
    duration = end_time - start_time
    
    if success:
        print(f"✅ Копирование alpine завершено за {duration:.1f} секунд!")
    else:
        print(f"❌ Ошибка копирования alpine: {stderr}")
    
    # Пример 2: Копирование с таймаутом (используем локальный образ)
    print("\n2️⃣ Копирование nginx с таймаутом...")
    print("   📥 Источник: dir:/tmp/skopeo_example/nginx_alpine")
    print("   📤 Назначение: dir:/tmp/skopeo_advanced_example/nginx_copy")
    print("   ⏰ Таймаут: 60 секунд")
    print("   ⏱️  Начинаем копирование...")
    
    start_time = time.time()
    success, stdout, stderr = skopeo.copy(
        source="dir:/tmp/skopeo_example/nginx_alpine",
        destination=f"dir:{test_dir}/nginx_copy",
        progress_callback=detailed_progress_callback,
        timeout=60  # 60 секунд таймаут
    )
    end_time = time.time()
    duration = end_time - start_time
    
    if success:
        print(f"✅ Копирование nginx завершено за {duration:.1f} секунд!")
    else:
        print(f"❌ Ошибка копирования nginx: {stderr}")
    
    # Пример 3: Массовое копирование образов (используем локальные образы)
    print("\n3️⃣ Массовое копирование образов...")
    images = [
        "dir:/tmp/skopeo_example/alpine",
        "dir:/tmp/skopeo_example/nginx_alpine",
        "dir:/tmp/skopeo_example/redis_alpine"
    ]
    
    print(f"   📋 Всего образов для копирования: {len(images)}")
    print("   🚀 Начинаем массовое копирование...")
    
    successful_copies = 0
    total_start_time = time.time()
    
    for i, image in enumerate(images, 1):
        image_name = image.split('/')[-1].replace(':', '_')
        print(f"\n   [{i}/{len(images)}] 📦 Копирование {image}...")
        print(f"   📥 Источник: {image}")
        print(f"   📤 Назначение: dir:{test_dir}/{image_name}")
        
        start_time = time.time()
        success, stdout, stderr = skopeo.copy(
            source=image,
            destination=f"dir:{test_dir}/{image_name}",
            progress_callback=detailed_progress_callback
        )
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            print(f"   ✅ {image_name} скопирован успешно за {duration:.1f} секунд!")
            successful_copies += 1
        else:
            print(f"   ❌ Ошибка копирования {image_name}: {stderr}")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    print(f"\n   📊 Результаты массового копирования:")
    print(f"   ✅ Успешно: {successful_copies}/{len(images)}")
    print(f"   ⏱️  Общее время: {total_duration:.1f} секунд")
    print(f"   📈 Среднее время на образ: {total_duration/len(images):.1f} секунд")
    
    # Пример 4: Анализ метаданных образов (используем локальные образы)
    print("\n4️⃣ Анализ метаданных образов...")
    print("   🔍 Начинаем анализ метаданных...")
    
    # Используем скопированные образы для анализа
    local_images = [
        f"dir:{test_dir}/alpine_copy",
        f"dir:{test_dir}/nginx_copy"
    ]
    
    successful_inspects = 0
    total_layers = 0
    total_size = 0
    
    for i, image in enumerate(local_images, 1):
        print(f"\n   [{i}/{len(local_images)}] 🔍 Анализ {image}...")
        print(f"   📥 Запрашиваем метаданные...")
        
        start_time = time.time()
        success, image_info, stderr = skopeo.inspect(image=image)
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            try:
                info = json.loads(image_info)
                print(f"   ✅ Метаданные получены за {duration:.2f} секунд")
                print(f"   📋 Детали образа:")
                print(f"     🏗️  Архитектура: {info.get('Architecture', 'N/A')}")
                print(f"     💻 ОС: {info.get('Os', 'N/A')}")
                
                size = info.get('Size', 0)
                if size:
                    size_mb = size / 1024 / 1024
                    print(f"     📦 Размер: {size_mb:.1f} MB ({size:,} bytes)")
                    total_size += size
                else:
                    print(f"     📦 Размер: N/A")
                
                layers = info.get('Layers', [])
                print(f"     🗂️  Слоев: {len(layers)}")
                total_layers += len(layers)
                
                if layers:
                    print(f"     📋 Слои:")
                    for j, layer in enumerate(layers[:3], 1):  # Показываем первые 3 слоя
                        print(f"       {j}. {layer[:64]}...")
                    if len(layers) > 3:
                        print(f"       ... и еще {len(layers) - 3} слоев")
                
                successful_inspects += 1
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Ошибка парсинга JSON: {e}")
        else:
            print(f"   ❌ Ошибка получения метаданных: {stderr}")
    
    print(f"\n   📊 Результаты анализа:")
    print(f"   ✅ Успешно проанализировано: {successful_inspects}/{len(images)}")
    print(f"   🗂️  Общее количество слоев: {total_layers}")
    if total_size > 0:
        print(f"   📦 Общий размер: {total_size / 1024 / 1024:.1f} MB")
    
    print("\n" + "=" * 60)
    print("🏁 Продвинутый пример завершен!")
    print(f"📁 Результаты сохранены в: {test_dir}")
    
    # Показываем размер результатов
    print("\n📊 Финальная статистика:")
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_count += 1
    
    print(f"   📦 Общий размер скопированных образов: {total_size / 1024 / 1024:.2f} MB")
    print(f"   📄 Количество файлов: {file_count}")
    print(f"   📁 Директорий создано: {len([d for d in os.listdir(test_dir) if os.path.isdir(os.path.join(test_dir, d))])}")
    
    # Показываем содержимое директории
    print(f"\n📋 Содержимое директории {test_dir}:")
    for item in sorted(os.listdir(test_dir)):
        item_path = os.path.join(test_dir, item)
        if os.path.isdir(item_path):
            item_size = sum(os.path.getsize(os.path.join(dirpath, filename)) 
                           for dirpath, dirnames, filenames in os.walk(item_path) 
                           for filename in filenames)
            print(f"   📁 {item}/ ({item_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"   📄 {item}")


if __name__ == "__main__":
    main()
