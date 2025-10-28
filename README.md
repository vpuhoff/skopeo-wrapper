# Skopeo Wrapper

Python библиотека-обертка для утилиты skopeo с поддержкой парсинга прогресса операций.

## Возможности

- 🚀 **Парсинг прогресса**: Извлечение информации о ходе выполнения операций skopeo
- 📦 **Операции с образами**: Копирование, инспекция, удаление образов
- 🔄 **Callback-функции**: Возможность отслеживания прогресса в реальном времени
- ⚡ **Асинхронный мониторинг**: Неблокирующий мониторинг вывода skopeo
- 🛡️ **Обработка ошибок**: Корректная обработка ошибок и исключений
- 🖥️ **CLI интерфейс**: Консольный интерфейс для быстрого использования
- 📊 **Prometheus метрики**: Полная поддержка метрик для мониторинга
- 📈 **Grafana дашборды**: Готовые дашборды для визуализации

## Установка

### Требования

- Python 3.7+
- Утилита skopeo (установлена в системе)
- **Рекомендуется**: skopeo версии 1.18+ для лучшей совместимости

### Установка skopeo

#### Быстрая установка (рекомендуемая версия)
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install skopeo

# CentOS/RHEL
sudo yum install skopeo

# Fedora
sudo dnf install skopeo
```

#### Установка skopeo 1.18 из исходников
```bash
# Установка зависимостей
sudo apt install -y golang-go libgpgme-dev pkg-config

# Скачивание и сборка
wget https://github.com/containers/skopeo/archive/refs/tags/v1.18.0.tar.gz
tar -xzf v1.18.0.tar.gz
cd skopeo-1.18.0
make bin/skopeo
sudo cp bin/skopeo /usr/local/bin/skopeo
```

### Установка библиотеки

#### Из PyPI (когда будет опубликована)
```bash
pip install skopeo-wrapper
```

#### Из исходников
```bash
# Клонирование репозитория
git clone https://github.com/your-username/skopeo-wrapper.git
cd skopeo-wrapper

# Установка в режиме разработки
pip install -e .

# Или установка зависимостей
pip install -r requirements.txt
```

## Использование

### Python API

#### Базовое использование

```python
from skopeo_wrapper import SkopeoWrapper, create_progress_callback

# Создание экземпляра
skopeo = SkopeoWrapper()

# Копирование образа с отображением прогресса
success, stdout, stderr = skopeo.copy(
    source="docker://docker.io/library/alpine:latest",
    destination="dir:/tmp/alpine_image",
    progress_callback=create_progress_callback(show_progress=True)
)

if success:
    print("Копирование завершено успешно!")
else:
    print(f"Ошибка: {stderr}")
```

#### Детальный мониторинг прогресса

```python
from skopeo_wrapper import SkopeoWrapper, ProgressInfo

def detailed_progress_callback(progress: ProgressInfo):
    print(f"Этап: {progress.current_step}")
    print(f"Прогресс: {progress.parser.get_progress_percentage():.1f}%")
    
    if progress.current_blob:
        print(f"Текущий blob: {progress.current_blob.sha256[:12]}...")
        if progress.current_blob.size:
            print(f"Размер: {progress.current_blob.size} bytes")

skopeo = SkopeoWrapper()
success, stdout, stderr = skopeo.copy(
    source="docker://docker.io/library/ubuntu:22.04",
    destination="dir:/tmp/ubuntu_image",
    progress_callback=detailed_progress_callback
)
```

#### Операции с образами

```python
# Инспекция образа
success, image_info, stderr = skopeo.inspect(
    image="docker://docker.io/library/alpine:latest"
)

if success:
    import json
    info = json.loads(image_info)
    print(f"Архитектура: {info['Architecture']}")
    print(f"ОС: {info['Os']}")

# Получение digest манифеста
success, digest, stderr = skopeo.get_manifest_digest(
    image="docker://docker.io/library/alpine:latest"
)

if success:
    print(f"Digest: {digest.strip()}")
```

### CLI интерфейс

```bash
# Копирование образа
skopeo-wrapper copy docker://alpine:latest dir:/tmp/alpine --progress

# Инспекция образа
skopeo-wrapper inspect docker://ubuntu:22.04 --json

# Удаление образа
skopeo-wrapper delete docker://alpine:latest

# Получение digest манифеста
skopeo-wrapper manifest-digest docker://nginx:alpine


# Справка
skopeo-wrapper --help
```

### Prometheus метрики

#### Базовое использование метрик

```python
from skopeo_wrapper import SkopeoWrapper

# Создание с включенными метриками (по умолчанию)
skopeo = SkopeoWrapper(enable_metrics=True)

# Выполнение операций
success, stdout, stderr = skopeo.copy(
    source="docker://alpine:latest",
    destination="dir:/tmp/alpine"
)

# Получение метрик
metrics = skopeo.get_metrics()
print(metrics)
```


#### Детальное отслеживание операций

```python
from skopeo_wrapper import SkopeoWrapper, OperationTracker

skopeo = SkopeoWrapper(enable_metrics=True)

# Использование OperationTracker для детального отслеживания
with OperationTracker("copy", skopeo.metrics, 
                     source="docker://alpine:latest",
                     destination="dir:/tmp/alpine") as tracker:
    
    # Имитация обработки blob'ов
    tracker.add_blob(1024000)  # 1MB
    tracker.add_blob(2048000)  # 2MB
```

#### Доступные метрики

- `skopeo_operations_total` - Общее количество операций по типам и статусам
- `skopeo_operation_duration_seconds` - Время выполнения операций
- `skopeo_blobs_processed_total` - Количество обработанных blob'ов
- `skopeo_blob_size_bytes` - Размеры blob'ов
- `skopeo_active_operations` - Текущие активные операции
- `skopeo_operation_errors_total` - Количество ошибок по типам
- `skopeo_source_operations_total` - Операции по типам источников
- `skopeo_destination_operations_total` - Операции по типам назначений

## API Reference

### SkopeoWrapper

Основной класс для работы с skopeo.

#### Методы

- `copy(source, destination, progress_callback=None, timeout=None)` - Копирование образа
- `inspect(image, progress_callback=None, timeout=None)` - Получение информации об образе
- `delete(image, progress_callback=None, timeout=None)` - Удаление образа
- `get_manifest_digest(image, progress_callback=None, timeout=None)` - Получение digest манифеста

#### Параметры

- `source`/`destination`/`image` - URL образа или путь
- `progress_callback` - Функция для обработки прогресса
- `timeout` - Таймаут операции в секундах

### ProgressInfo

Информация о прогрессе операции.

#### Атрибуты

- `operation` - Тип операции
- `current_step` - Текущий этап выполнения
- `current_blob` - Информация о текущем blob
- `manifest_written` - Манифест записан
- `signatures_stored` - Подписи сохранены
- `error` - Сообщение об ошибке
- `completed` - Операция завершена

### BlobInfo

Информация о blob-объекте.

#### Атрибуты

- `sha256` - SHA256 хеш blob
- `size` - Размер в байтах
- `status` - Статус обработки

### SkopeoMetrics

Класс для управления Prometheus метриками.

#### Методы

- `record_operation_start(operation)` - Записывает начало операции
- `record_operation_end(operation, success, start_time, ...)` - Записывает завершение операции
- `record_error(operation, error_type)` - Записывает ошибку операции
- `record_blob_processed(operation, blob_size)` - Записывает обработку blob'а
- `get_metrics()` - Возвращает метрики в формате Prometheus
- `get_metrics_dict()` - Возвращает метрики в виде словаря

### OperationTracker

Контекстный менеджер для автоматического отслеживания операций.

#### Методы

- `add_blob(blob_size)` - Добавляет информацию о blob'е


## Примеры вывода

### Копирование образа (skopeo 1.18)

```
🔍 getting_signatures: 10.0%
📦 copying_blob: 50.0%
   (blob: af6eca94c810...)
📦 copying_config: 75.0%
   (config: 392fa14dddd0...)
📝 writing_manifest: 90.0%
✅ Операция завершена успешно
```

### Копирование образа (старые версии)

```
🔍 getting_signatures: 10.0%
📦 copying_blob: 50.0%
   (blob: 2d35ebdb57d9... 1234567 bytes)
📝 writing_manifest: 85.0%
🔐 storing_signatures: 95.0%
✅ Операция завершена успешно
```

### Инспекция образа

```
🔍 getting_signatures: 10.0%
✅ Операция завершена успешно
```

### Примеры метрик Prometheus

#### Базовые метрики операций

```
# HELP skopeo_operations_total Общее количество операций skopeo
# TYPE skopeo_operations_total counter
skopeo_operations_total{operation="copy",status="success"} 15
skopeo_operations_total{operation="copy",status="error"} 2
skopeo_operations_total{operation="inspect",status="success"} 8

# HELP skopeo_operation_duration_seconds Время выполнения операций skopeo в секундах
# TYPE skopeo_operation_duration_seconds histogram
skopeo_operation_duration_seconds_bucket{operation="copy",le="0.1"} 0
skopeo_operation_duration_seconds_bucket{operation="copy",le="0.5"} 2
skopeo_operation_duration_seconds_bucket{operation="copy",le="1.0"} 8
skopeo_operation_duration_seconds_bucket{operation="copy",le="+Inf"} 15
skopeo_operation_duration_seconds_sum{operation="copy"} 12.5
skopeo_operation_duration_seconds_count{operation="copy"} 15
```

#### Метрики blob'ов

```
# HELP skopeo_blobs_processed_total Общее количество обработанных blob'ов
# TYPE skopeo_blobs_processed_total counter
skopeo_blobs_processed_total{operation="copy",status="success"} 45
skopeo_blobs_processed_total{operation="copy",status="error"} 3

# HELP skopeo_blob_size_bytes Размер blob'ов в байтах
# TYPE skopeo_blob_size_bytes histogram
skopeo_blob_size_bytes_bucket{operation="copy",le="1024"} 5
skopeo_blob_size_bytes_bucket{operation="copy",le="10240"} 12
skopeo_blob_size_bytes_bucket{operation="copy",le="1048576"} 28
skopeo_blob_size_bytes_bucket{operation="copy",le="+Inf"} 45
skopeo_blob_size_bytes_sum{operation="copy"} 2.5e+08
skopeo_blob_size_bytes_count{operation="copy"} 45
```

#### Активные операции

```
# HELP skopeo_active_operations Количество активных операций skopeo
# TYPE skopeo_active_operations gauge
skopeo_active_operations{operation="copy"} 2
skopeo_active_operations{operation="inspect"} 0
```

## Мониторинг и визуализация

### Grafana дашборды

В проекте включен готовый дашборд Grafana для визуализации метрик skopeo-wrapper:

```bash
# Импорт дашборда в Grafana
# Файл: examples/grafana_dashboard.json
```

Дашборд включает:
- Общую статистику операций
- Время выполнения операций
- Количество обработанных blob'ов
- Размеры blob'ов
- Активные операции
- Типы источников и назначений
- Алерты и ошибки

### Интеграция с приложениями

Для экспорта метрик в приложении, использующем skopeo-wrapper:

```python
from skopeo_wrapper import SkopeoWrapper
from prometheus_client import start_http_server, generate_latest

# Создание обертки с метриками
skopeo = SkopeoWrapper(enable_metrics=True)

# Запуск HTTP сервера для экспорта метрик
start_http_server(8000)

# Получение метрик
metrics = skopeo.get_metrics()
print(metrics)
```

### Prometheus конфигурация

Пример конфигурации Prometheus для сбора метрик:

```yaml
# Файл: examples/prometheus.yml
scrape_configs:
  - job_name: 'skopeo-wrapper-app'
    static_configs:
      - targets: ['your-app:8000']  # Адрес вашего приложения
    scrape_interval: 5s
    metrics_path: /metrics
```

### Алертинг

Настроенные правила алертинга для мониторинга:

```yaml
# Файл: examples/skopeo-wrapper-alerts.yml
- alert: SkopeoHighErrorRate
  expr: rate(skopeo_operation_errors_total[5m]) > 0.1
  for: 2m
  labels:
    severity: warning
```

## Тестирование

### Базовые тесты

```bash
python -m pytest tests/
```

### Тесты метрик

```bash
python -m pytest tests/test_metrics.py -v
```

### Тесты для skopeo 1.18

```bash
python tests/test_skopeo_118.py
```

### Примеры использования

```bash
python examples/basic_usage.py
python examples/advanced_usage.py
python examples/metrics_usage.py
```

Тесты включают:
- Копирование образов с различными типами прогресса
- Инспекцию образов
- Обработку ошибок
- Специальные тесты для skopeo 1.18
- Полное покрытие метрик Prometheus

## Ограничения

- Skopeo не предоставляет детальную информацию о прогрессе загрузки blob'ов
- Прогресс рассчитывается приблизительно на основе этапов операции
- Размер blob'ов не всегда доступен в выводе skopeo
- В skopeo 1.18 отсутствует этап "Storing signatures"
- Парсинг прогресса основан на анализе stderr, что может быть нестабильным

## Разработка

### Установка в режиме разработки

```bash
git clone https://github.com/your-username/skopeo-wrapper.git
cd skopeo-wrapper
pip install -e ".[dev]"
```

### Запуск тестов

```bash
pytest tests/ -v
```

### Форматирование кода

```bash
black skopeo_wrapper/ tests/ examples/
flake8 skopeo_wrapper/ tests/ examples/
```

## Лицензия

MIT License

## Вклад в проект

Приветствуются pull request'ы и issue'ы для улучшения библиотеки.

## Changelog

### 1.0.0
- Первоначальный релиз
- Поддержка skopeo 1.18
- CLI интерфейс
- Парсинг прогресса операций
- Полная документация
# Test commit after tag
