#!/usr/bin/env python3
"""
Примеры использования Prometheus метрик в skopeo-wrapper
"""

import time
import json
from skopeo_wrapper import SkopeoWrapper, SkopeoMetrics, start_metrics_server, OperationTracker
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
    """Пример запуска сервера метрик"""
    print("\n🚀 Пример запуска сервера метрик")
    print("=" * 50)
    
    # Создаем экземпляр с метриками
    skopeo = SkopeoWrapper(enable_metrics=True)
    
    # Запускаем сервер метрик
    print("🌐 Запуск сервера метрик на localhost:8001...")
    server = start_metrics_server(host='localhost', port=8001)
    
    print(f"📊 Метрики доступны по адресу: {server.get_url()}/metrics")
    print("❤️  Проверка здоровья: {}/health".format(server.get_url()))
    
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
    
    print(f"\n🌐 Сервер метрик работает на {server.get_url()}")
    print("📊 Откройте браузер и перейдите по адресу: {}/metrics".format(server.get_url()))
    print("🛑 Нажмите Ctrl+C для остановки сервера")
    
    try:
        # Держим сервер запущенным
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера метрик...")
        server.stop()


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
        
        print("\n" + "=" * 70)
        print("🏁 Все примеры завершены!")
        print("\n💡 Дополнительные возможности:")
        print("   - Запуск сервера метрик: skopeo-wrapper metrics-server")
        print("   - Просмотр метрик: skopeo-wrapper metrics")
        print("   - Метрики в JSON: skopeo-wrapper metrics --format json")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
