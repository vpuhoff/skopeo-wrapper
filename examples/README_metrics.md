# Примеры использования Prometheus метрик

Этот каталог содержит примеры использования Prometheus метрик в skopeo-wrapper.

## Файлы

### `metrics_usage.py`
Основной пример использования метрик с различными сценариями:
- Базовое использование метрик
- Кастомные метрики
- OperationTracker для детального отслеживания
- Запуск сервера метрик
- Отслеживание ошибок

### `grafana_dashboard.json`
Готовый дашборд Grafana для визуализации метрик skopeo-wrapper:
- Общая статистика операций
- Время выполнения операций
- Количество и размеры blob'ов
- Активные операции
- Типы источников и назначений
- Алерты и ошибки

### `prometheus.yml`
Пример конфигурации Prometheus для сбора метрик:
- Настройка scrape конфигурации
- Обнаружение сервисов
- Правила алертинга

### `skopeo-wrapper-alerts.yml`
Правила алертинга для мониторинга:
- Высокий уровень ошибок
- Медленные операции
- Большое количество активных операций
- Отсутствие метрик
- Высокий объем данных

### `skopeo-wrapper-targets.json`
Файл целей для обнаружения сервисов Prometheus:
- Статические цели
- Лейблы для группировки
- Поддержка множественных экземпляров

## Быстрый старт

1. **Запуск примера с метриками:**
   ```bash
   python examples/metrics_usage.py
   ```

2. **Запуск сервера метрик:**
   ```bash
   skopeo-wrapper metrics-server --host localhost --port 8000
   ```

3. **Просмотр метрик:**
   ```bash
   curl http://localhost:8000/metrics
   ```

4. **Импорт дашборда в Grafana:**
   - Откройте Grafana
   - Перейдите в Dashboards → Import
   - Загрузите файл `grafana_dashboard.json`

5. **Настройка Prometheus:**
   - Скопируйте `prometheus.yml` в конфигурацию Prometheus
   - Перезапустите Prometheus

## Доступные метрики

- `skopeo_operations_total` - Общее количество операций
- `skopeo_operation_duration_seconds` - Время выполнения операций
- `skopeo_blobs_processed_total` - Количество обработанных blob'ов
- `skopeo_blob_size_bytes` - Размеры blob'ов
- `skopeo_active_operations` - Активные операции
- `skopeo_operation_errors_total` - Ошибки операций
- `skopeo_source_operations_total` - Операции по источникам
- `skopeo_destination_operations_total` - Операции по назначениям

## Мониторинг в production

1. **Настройте Prometheus** для сбора метрик
2. **Импортируйте дашборд** в Grafana
3. **Настройте алерты** для критических метрик
4. **Мониторьте производительность** операций skopeo
5. **Отслеживайте ошибки** и их типы
