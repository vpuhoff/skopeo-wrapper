#!/usr/bin/env python3
"""
Примеры использования Prometheus метрик в skopeo-wrapper
"""

import time
import json
from skopeo_wrapper import SkopeoWrapper, SkopeoMetrics, OperationTracker
from prometheus_client import start_http_server
import os


def example_basic_metrics():
    """Базовый пример использования метрик"""
    print("🚀 Базовый пример использования метрик")
    print("=" * 50)
    
    # Создаем экземпляр с метриками
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Создаем тестовую директорию
    test_dir = "/tmp/skopeo_metrics_example"
    os.makedirs(test_dir, exist_ok=True)
    
    # Выполняем несколько операций
    print("\n📦 Копирование образа alpine:latest...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=f"dir:{test_dir}/alpine"
    )
    
    if success:
        print("✅ Копирование завершено!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    print("\n🔍 Инспекция образа ubuntu:22.04...")
    success, stdout, stderr = skopeo.inspect(
        image="docker://docker.io/library/ubuntu:22.04"
    )
    
    if success:
        print("✅ Инспекция завершена!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    # Показываем метрики
    print("\n📊 Текущие метрики:")
    metrics = skopeo.get_metrics()
    if metrics:
        print(metrics)
    else:
        print("Нет доступных метрик")


def example_custom_metrics():
    """Пример с кастомными метриками"""
    print("\n🚀 Пример с кастомными метриками")
    print("=" * 50)
    
    # Создаем кастомный экземпляр метрик
    custom_metrics = SkopeoMetrics()
    
    # Создаем обертку с кастомными метриками
    skopeo = SkopeoWrapper(metrics=custom_metrics, enable_metrics=True)
    
    # Создаем тестовую директорию
    test_dir = "/tmp/skopeo_custom_metrics"
    os.makedirs(test_dir, exist_ok=True)
    
    # Выполняем операции
    print("\n📦 Копирование нескольких образов...")
    images = [
        "docker://docker.io/library/nginx:alpine",
        "docker://docker.io/library/redis:alpine"
    ]
    
    for image in images:
        image_name = image.split('/')[-1].replace(':', '_')
        print(f"   Копирование {image}...")
        
        success, stdout, stderr = skopeo.copy(
            source=image,
            destination=f"dir:{test_dir}/{image_name}"
        )
        
        if success:
            print(f"   ✅ {image_name} скопирован!")
        else:
            print(f"   ❌ Ошибка копирования {image_name}: {stderr}")
    
    # Показываем метрики в JSON формате
    print("\n📊 Метрики в JSON формате:")
    metrics_dict = skopeo.get_metrics_dict()
    if metrics_dict:
        print(json.dumps(metrics_dict, indent=2, ensure_ascii=False))
    else:
        print("Нет доступных метрик")


def example_operation_tracker():
    """Пример использования OperationTracker"""
    print("\n🚀 Пример использования OperationTracker")
    print("=" * 50)
    
    # Создаем экземпляр метрик
    metrics = SkopeoMetrics()
    
    # Создаем тестовую директорию
    test_dir = "/tmp/skopeo_tracker_example"
    os.makedirs(test_dir, exist_ok=True)
    
    # Используем OperationTracker для детального отслеживания
    with OperationTracker("copy", metrics, 
                         source="docker://docker.io/library/alpine:latest",
                         destination=f"dir:{test_dir}/alpine_tracked") as tracker:
        
        print("📦 Копирование с детальным отслеживанием...")
        
        # Имитируем обработку blob'ов
        for i in range(3):
            blob_size = 1024 * 1024 * (i + 1)  # 1MB, 2MB, 3MB
            tracker.add_blob(blob_size)
            print(f"   Обработан blob {i+1}: {blob_size} bytes")
            time.sleep(0.1)  # Имитация обработки
        
        print("✅ Операция завершена!")
    
    # Показываем метрики
    print("\n📊 Метрики после отслеживания:")
    metrics_data = metrics.get_metrics()
    if metrics_data:
        print(metrics_data)
    else:
        print("Нет доступных метрик")


def example_metrics_server():
    """Пример запуска HTTP сервера для экспорта метрик"""
    print("\n🚀 Пример запуска HTTP сервера для экспорта метрик")
    print("=" * 50)
    
    # Создаем экземпляр с метриками
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Запускаем HTTP сервер для экспорта метрик
    print("🌐 Запуск HTTP сервера на localhost:8001...")
    start_http_server(8001)
    
    print("📊 Метрики доступны по адресу: http://localhost:8001/metrics")
    
    # Выполняем несколько операций для генерации метрик
    test_dir = "/tmp/skopeo_server_example"
    os.makedirs(test_dir, exist_ok=True)
    
    print("\n📦 Выполняем операции для генерации метрик...")
    
    # Копируем образ
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=f"dir:{test_dir}/alpine"
    )
    
    if success:
        print("✅ Копирование завершено!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    # Инспектируем образ
    success, stdout, stderr = skopeo.inspect(
        image="docker://docker.io/library/ubuntu:22.04"
    )
    
    if success:
        print("✅ Инспекция завершена!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    print("\n🌐 HTTP сервер работает на http://localhost:8001")
    print("📊 Откройте браузер и перейдите по адресу: http://localhost:8001/metrics")
    print("🛑 Нажмите Ctrl+C для остановки сервера")
    
    try:
        # Держим сервер запущенным
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка HTTP сервера...")


def example_error_metrics():
    """Пример отслеживания ошибок в метриках"""
    print("\n🚀 Пример отслеживания ошибок в метриках")
    print("=" * 50)
    
    # Создаем экземпляр с метриками
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Выполняем операцию с ошибкой
    print("❌ Попытка копирования несуществующего образа...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/nonexistent:latest",
        destination="dir:/tmp/nonexistent"
    )
    
    if not success:
        print(f"❌ Ошибка (ожидаемо): {stderr}")
    
    # Выполняем успешную операцию
    print("\n✅ Выполняем успешную операцию...")
    test_dir = "/tmp/skopeo_error_example"
    os.makedirs(test_dir, exist_ok=True)
    
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination=f"dir:{test_dir}/alpine"
    )
    
    if success:
        print("✅ Операция завершена успешно!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    # Показываем метрики с ошибками
    print("\n📊 Метрики с информацией об ошибках:")
    metrics = skopeo.get_metrics()
    if metrics:
        print(metrics)
    else:
        print("Нет доступных метрик")


def example_heartbeat_metrics():
    """Пример использования heartbeat метрик"""
    print("💓 Пример использования heartbeat метрик")
    print("=" * 50)
    
    # Создаем экземпляр с метриками
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Запускаем HTTP сервер для Prometheus
    print("\n🌐 Запуск HTTP сервера на порту 9090...")
    start_http_server(9090)
    print("📊 Метрики доступны по адресу: http://localhost:9090/metrics")
    
    test_dir = "/tmp/skopeo_heartbeat_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Создаем callback для обновления прогресса
    def progress_callback(progress_info):
        if hasattr(progress_info, 'parser'):
            progress_percent = progress_info.parser.get_progress_percentage()
            print(f"  📈 Прогресс: {progress_percent:.1f}% - {progress_info.current_step}")
    
    print("\n📦 Копирование большого образа с heartbeat метриками...")
    print("💡 Откройте http://localhost:9090/metrics в браузере")
    print("💡 Смотрите метрики:")
    print("   - skopeo_active_operation_duration_seconds - растет каждые 10 сек")
    print("   - skopeo_operation_speed_blobs_per_second - скорость обработки")
    print("   - skopeo_operation_stale_seconds - время без обновления")
    
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/ubuntu:22.04",
        destination=f"dir:{test_dir}/ubuntu",
        progress_callback=progress_callback,
        timeout=600
    )
    
    if success:
        print("✅ Копирование завершено!")
    else:
        print(f"❌ Ошибка: {stderr}")
    
    print("\n📊 Проверьте финальные метрики:")
    metrics_dict = skopeo.get_metrics_dict()
    
    print(f"  - Активные операции: {metrics_dict.get('skopeo_active_operations', {})}")
    print(f"  - Последняя скорость: см. skopeo_operation_speed_blobs_per_second")
    
    print("\n⏸️  Сервер продолжит работать. Нажмите Ctrl+C для остановки...")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n👋 Остановка...")


def main():
    """Основная функция с примерами"""
    print("🚀 Примеры использования Prometheus метрик в skopeo-wrapper")
    print("=" * 70)
    
    try:
        # Базовый пример
        example_basic_metrics()
        
        # Пример с кастомными метриками
        example_custom_metrics()
        
        # Пример с OperationTracker
        example_operation_tracker()
        
        # Пример с сервером метрик (закомментирован, так как блокирует выполнение)
        # example_metrics_server()
        
        # Пример с ошибками
        example_error_metrics()
        
        # Пример с heartbeat метриками
        example_heartbeat_metrics()
        
        print("\n" + "=" * 70)
        print("🏁 Все примеры завершены!")
        print("\n💡 Дополнительные возможности:")
        print("   - Интеграция с prometheus_client для экспорта метрик")
        print("   - Использование Grafana дашбордов для визуализации")
        print("   - Настройка алертинга в Prometheus")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
