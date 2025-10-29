#!/usr/bin/env python3
"""
Демонстрация реального прогресса с удаленными образами
ВНИМАНИЕ: Этот пример требует интернет-соединения и может быть ограничен лимитами Docker Hub
"""

from skopeo_wrapper import SkopeoWrapper, ProgressInfo, get_progress_percentage
import time
import sys


def real_progress_callback(progress: ProgressInfo):
    """Callback для отображения реального прогресса с удаленными образами"""
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
        else:
            print(f"   📋 Blob'ы: ожидание...")
    
    print(f"   📄 Манифест записан: {'✅' if progress.manifest_written else '❌'}")
    print(f"   🔐 Подписи сохранены: {'✅' if progress.signatures_stored else '❌'}")
    
    if progress.current_blob:
        size_mb = progress.current_blob.size / 1024 / 1024 if progress.current_blob.size else 0
        print(f"   🎯 Текущий blob: {progress.current_blob.sha256[:16]}... ({size_mb:.1f}MB)")
    
    if progress.error:
        print(f"   ❌ Ошибка: {progress.error}")
    elif progress.completed:
        print(f"   🎉 Завершено!")
        # Для завершенных операций показываем 100%
        bar = "█" * 20
        print(f"   📈 Прогресс: {bar} 100.0%")
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
            elif progress.current_step == "starting":
                percentage = 5.0
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
    """Демонстрация реального прогресса с удаленными образами"""
    print("🌐 Демонстрация реального прогресса с удаленными образами")
    print("=" * 60)
    print("⚠️  ВНИМАНИЕ: Этот пример требует интернет-соединения")
    print("⚠️  Может быть ограничен лимитами Docker Hub")
    print("=" * 60)
    
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Создаем директорию для тестов
    test_dir = "/tmp/skopeo_remote_demo"
    import os
    os.makedirs(test_dir, exist_ok=True)
    
    # Список небольших образов для демонстрации
    small_images = [
        "docker://docker.io/library/hello-world:latest",
        "docker://docker.io/library/alpine:latest"
    ]
    
    print(f"\n📋 Образы для демонстрации: {len(small_images)}")
    for i, image in enumerate(small_images, 1):
        print(f"   {i}. {image}")
    
    print("\n🚀 Начинаем демонстрацию...")
    print("💡 Обратите внимание на детальный прогресс с blob'ами!")
    
    successful_copies = 0
    
    for i, image in enumerate(small_images, 1):
        image_name = image.split('/')[-1].replace(':', '_')
        print(f"\n{'='*60}")
        print(f"📦 [{i}/{len(small_images)}] Копирование {image}")
        print(f"📥 Источник: {image}")
        print(f"📤 Назначение: dir:{test_dir}/{image_name}")
        print(f"⏱️  Начинаем копирование...")
        
        start_time = time.time()
        success, stdout, stderr = skopeo.copy(
            source=image,
            destination=f"dir:{test_dir}/{image_name}",
            progress_callback=real_progress_callback,
            timeout=120  # 2 минуты таймаут
        )
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            print(f"\n✅ {image_name} скопирован успешно за {duration:.1f} секунд!")
            successful_copies += 1
        else:
            print(f"\n❌ Ошибка копирования {image_name}: {stderr}")
            if "toomanyrequests" in stderr.lower():
                print("   💡 Это ошибка лимита запросов Docker Hub")
                print("   💡 Попробуйте позже или используйте локальные образы")
    
    print(f"\n{'='*60}")
    print("🏁 Демонстрация завершена!")
    print(f"📊 Результаты:")
    print(f"   ✅ Успешно: {successful_copies}/{len(small_images)}")
    print(f"   📁 Результаты сохранены в: {test_dir}")
    
    if successful_copies > 0:
        print(f"\n💡 Теперь вы можете использовать локальные образы:")
        for i, image in enumerate(small_images, 1):
            image_name = image.split('/')[-1].replace(':', '_')
            print(f"   {i}. dir:{test_dir}/{image_name}")


if __name__ == "__main__":
    main()
