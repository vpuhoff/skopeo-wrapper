#!/usr/bin/env python3
"""
Prometheus метрики для skopeo-wrapper
"""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from typing import Optional, Dict, Any
import time
from enum import Enum


class SkopeoOperation(Enum):
    """Типы операций skopeo для метрик"""
    COPY = "copy"
    INSPECT = "inspect"
    DELETE = "delete"
    MANIFEST_DIGEST = "manifest_digest"


class SkopeoMetrics:
    """Класс для управления Prometheus метриками skopeo-wrapper"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Инициализация метрик
        
        Args:
            registry: Реестр Prometheus (по умолчанию используется глобальный)
        """
        self.registry = registry or CollectorRegistry()
        
        # Счетчики операций
        self.operations_total = Counter(
            'skopeo_operations_total',
            'Общее количество операций skopeo',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # Счетчики ошибок
        self.operation_errors_total = Counter(
            'skopeo_operation_errors_total',
            'Общее количество ошибок операций skopeo',
            ['operation', 'error_type'],
            registry=self.registry
        )
        
        # Гистограммы времени выполнения
        self.operation_duration_seconds = Histogram(
            'skopeo_operation_duration_seconds',
            'Время выполнения операций skopeo в секундах',
            ['operation'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, float('inf')],
            registry=self.registry
        )
        
        # Счетчики blob'ов
        self.blobs_processed_total = Counter(
            'skopeo_blobs_processed_total',
            'Общее количество обработанных blob\'ов',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # Размеры blob'ов
        self.blob_size_bytes = Histogram(
            'skopeo_blob_size_bytes',
            'Размер blob\'ов в байтах',
            ['operation'],
            buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600, 1073741824, float('inf')],
            registry=self.registry
        )
        
        # Текущие активные операции
        self.active_operations = Gauge(
            'skopeo_active_operations',
            'Количество активных операций skopeo',
            ['operation'],
            registry=self.registry
        )
        
        # Информация о версии
        self.version_info = Info(
            'skopeo_wrapper_version',
            'Информация о версии skopeo-wrapper',
            registry=self.registry
        )
        self.version_info.info({
            'version': '1.0.0',
            'python_version': '3.7+'
        })
        
        # Счетчики по источникам и назначениям
        self.source_operations_total = Counter(
            'skopeo_source_operations_total',
            'Операции по источникам',
            ['source_type', 'operation'],
            registry=self.registry
        )
        
        self.destination_operations_total = Counter(
            'skopeo_destination_operations_total',
            'Операции по назначениям',
            ['destination_type', 'operation'],
            registry=self.registry
        )
        
        # Детальная информация об активных операциях
        self.active_operations_detailed = Gauge(
            'skopeo_active_operations_detailed',
            'Детальная информация об активных операциях',
            ['operation', 'source_short', 'destination_short', 'current_step'],
            registry=self.registry
        )
        
        # Текущая длительность активных операций
        self.active_operation_duration = Gauge(
            'skopeo_active_operation_duration_seconds',
            'Текущая длительность активных операций',
            ['operation', 'source_short', 'destination_short', 'current_step'],
            registry=self.registry
        )
        
        # Скорость обработки (blobs/сек)
        self.operation_speed = Gauge(
            'skopeo_operation_speed_blobs_per_second',
            'Скорость обработки blobs',
            ['operation', 'source_short', 'destination_short'],
            registry=self.registry
        )
        
        # Последний прогресс
        self.operation_last_progress = Gauge(
            'skopeo_operation_last_progress_percent',
            'Последний зафиксированный прогресс',
            ['operation', 'source_short', 'destination_short', 'current_step'],
            registry=self.registry
        )
        
        # Время с последнего обновления прогресса
        self.operation_stale_seconds = Gauge(
            'skopeo_operation_stale_seconds',
            'Время с последнего обновления прогресса',
            ['operation', 'source_short', 'destination_short', 'current_step'],
            registry=self.registry
        )
    
    def record_operation_start(self, operation: str) -> float:
        """
        Записывает начало операции
        
        Args:
            operation: Тип операции
            
        Returns:
            Время начала операции
        """
        self.active_operations.labels(operation=operation).inc()
        return time.time()
    
    def record_operation_end(self, 
                           operation: str, 
                           success: bool, 
                           start_time: float,
                           source: Optional[str] = None,
                           destination: Optional[str] = None,
                           blob_count: int = 0,
                           total_blob_size: int = 0) -> None:
        """
        Записывает завершение операции
        
        Args:
            operation: Тип операции
            success: Успешность операции
            start_time: Время начала операции
            source: Источник (для анализа типов)
            destination: Назначение (для анализа типов)
            blob_count: Количество обработанных blob'ов
            total_blob_size: Общий размер blob'ов в байтах
        """
        # Уменьшаем счетчик активных операций
        self.active_operations.labels(operation=operation).dec()
        
        # Записываем общую статистику операции
        status = 'success' if success else 'error'
        self.operations_total.labels(operation=operation, status=status).inc()
        
        # Записываем время выполнения
        duration = time.time() - start_time
        self.operation_duration_seconds.labels(operation=operation).observe(duration)
        
        # Записываем статистику blob'ов
        if blob_count > 0:
            self.blobs_processed_total.labels(
                operation=operation, 
                status=status
            ).inc(blob_count)
            
            if total_blob_size > 0:
                # Записываем средний размер blob'а
                avg_blob_size = total_blob_size / blob_count
                for _ in range(blob_count):
                    self.blob_size_bytes.labels(operation=operation).observe(avg_blob_size)
        
        # Анализируем типы источников и назначений
        if source:
            source_type = self._extract_type_from_url(source)
            self.source_operations_total.labels(
                source_type=source_type, 
                operation=operation
            ).inc()
        
        if destination:
            destination_type = self._extract_type_from_url(destination)
            self.destination_operations_total.labels(
                destination_type=destination_type, 
                operation=operation
            ).inc()
    
    def record_error(self, operation: str, error_type: str) -> None:
        """
        Записывает ошибку операции
        
        Args:
            operation: Тип операции
            error_type: Тип ошибки
        """
        self.operation_errors_total.labels(
            operation=operation, 
            error_type=error_type
        ).inc()
    
    def record_blob_processed(self, operation: str, blob_size: Optional[int] = None) -> None:
        """
        Записывает обработку blob'а
        
        Args:
            operation: Тип операции
            blob_size: Размер blob'а в байтах
        """
        self.blobs_processed_total.labels(operation=operation, status='success').inc()
        
        if blob_size and blob_size > 0:
            self.blob_size_bytes.labels(operation=operation).observe(blob_size)
    
    def _extract_type_from_url(self, url: str) -> str:
        """
        Извлекает тип из URL (docker, dir, oci, etc.)
        
        Args:
            url: URL для анализа
            
        Returns:
            Тип источника/назначения
        """
        if url.startswith('docker://'):
            return 'docker'
        elif url.startswith('dir:'):
            return 'dir'
        elif url.startswith('oci://'):
            return 'oci'
        elif url.startswith('containers-storage://'):
            return 'containers_storage'
        elif url.startswith('docker-archive://'):
            return 'docker_archive'
        elif url.startswith('oci-archive://'):
            return 'oci_archive'
        else:
            return 'unknown'
    
    def _get_short_name(self, url: Optional[str], max_length: int = 50) -> str:
        """
        Получает короткое имя из URL для label'ов метрик
        
        Args:
            url: URL для обработки
            max_length: Максимальная длина
            
        Returns:
            Короткое имя
        """
        if not url:
            return "unknown"
        
        # Убираем префикс протокола
        short = url.replace('docker://', '').replace('dir:', '').replace('oci://', '')
        
        # Обрезаем если слишком длинное
        if len(short) > max_length:
            short = short[:max_length-3] + '...'
        
        return short
    
    def get_metrics(self) -> str:
        """
        Возвращает метрики в формате Prometheus
        
        Returns:
            Строка с метриками в формате Prometheus
        """
        return generate_latest(self.registry).decode('utf-8')
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Возвращает метрики в виде словаря для отладки
        
        Returns:
            Словарь с метриками
        """
        metrics_data = {}
        
        # Собираем данные счетчиков
        for metric in self.registry.collect():
            if hasattr(metric, 'samples'):
                for sample in metric.samples:
                    key = f"{sample.name}"
                    if sample.labels:
                        labels_str = ','.join(f'{k}={v}' for k, v in sample.labels.items())
                        key += f"{{{labels_str}}}"
                    metrics_data[key] = sample.value
        
        return metrics_data


# Глобальный экземпляр метрик
_global_metrics: Optional[SkopeoMetrics] = None


def get_metrics() -> SkopeoMetrics:
    """
    Возвращает глобальный экземпляр метрик
    
    Returns:
        Экземпляр SkopeoMetrics
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = SkopeoMetrics()
    return _global_metrics


def reset_metrics() -> None:
    """Сбрасывает глобальные метрики"""
    global _global_metrics
    _global_metrics = None


# Контекстный менеджер для автоматического отслеживания операций
class OperationTracker:
    """Контекстный менеджер для отслеживания операций"""
    
    def __init__(self, 
                 operation: str, 
                 metrics: Optional[SkopeoMetrics] = None,
                 source: Optional[str] = None,
                 destination: Optional[str] = None,
                 heartbeat_interval: int = 10):
        self.operation = operation
        self.metrics = metrics or get_metrics()
        self.source = source
        self.destination = destination
        self.start_time = None
        self.success = False
        self.blob_count = 0
        self.total_blob_size = 0
        self.heartbeat_interval = heartbeat_interval
        self.current_step = "starting"
        self.last_progress_time = None
        self.last_progress_percent = 0.0
        self.heartbeat_thread = None
        self.heartbeat_running = False
    
    def __enter__(self):
        self.start_time = self.metrics.record_operation_start(self.operation)
        self.start_heartbeat()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_heartbeat()
        self.success = exc_type is None
        if self.start_time is not None:
            self.metrics.record_operation_end(
                operation=self.operation,
                success=self.success,
                start_time=self.start_time,
                source=self.source,
                destination=self.destination,
                blob_count=self.blob_count,
                total_blob_size=self.total_blob_size
            )
        
        if exc_type is not None:
            error_type = exc_type.__name__ if exc_type else 'Unknown'
            self.metrics.record_error(self.operation, error_type)
    
    def add_blob(self, blob_size: Optional[int] = None):
        """Добавляет информацию о blob'е"""
        self.blob_count += 1
        if blob_size:
            self.total_blob_size += blob_size
        # Не вызываем record_blob_processed здесь, чтобы избежать дублирования
        # Метрики будут записаны в record_operation_end
    
    def start_heartbeat(self):
        """Запускает периодическое обновление метрик"""
        import threading
        
        self.heartbeat_running = True
        self.last_progress_time = time.time()
        
        def heartbeat_loop():
            while self.heartbeat_running:
                time.sleep(self.heartbeat_interval)
                if self.heartbeat_running:
                    self.update_heartbeat_metrics()
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        """Останавливает heartbeat и очищает метрики"""
        self.heartbeat_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
        
        # Очищаем метрики для этой операции
        source_short = self.metrics._get_short_name(self.source)
        dest_short = self.metrics._get_short_name(self.destination)
        
        try:
            self.metrics.active_operations_detailed.remove(
                self.operation, source_short, dest_short, self.current_step
            )
            self.metrics.active_operation_duration.remove(
                self.operation, source_short, dest_short, self.current_step
            )
            self.metrics.operation_speed.remove(
                self.operation, source_short, dest_short
            )
            self.metrics.operation_last_progress.remove(
                self.operation, source_short, dest_short, self.current_step
            )
            self.metrics.operation_stale_seconds.remove(
                self.operation, source_short, dest_short, self.current_step
            )
        except Exception:
            pass

    def update_heartbeat_metrics(self):
        """Обновляет метрики независимо от прогресса"""
        if not self.start_time:
            return
        
        current_time = time.time()
        duration = current_time - self.start_time
        
        source_short = self.metrics._get_short_name(self.source)
        dest_short = self.metrics._get_short_name(self.destination)
        
        # Обновляем детальную информацию
        self.metrics.active_operations_detailed.labels(
            operation=self.operation,
            source_short=source_short,
            destination_short=dest_short,
            current_step=self.current_step
        ).set(1)
        
        # Обновляем длительность
        self.metrics.active_operation_duration.labels(
            operation=self.operation,
            source_short=source_short,
            destination_short=dest_short,
            current_step=self.current_step
        ).set(duration)
        
        # Вычисляем скорость (blobs/сек)
        if duration > 0 and self.blob_count > 0:
            speed = self.blob_count / duration
            self.metrics.operation_speed.labels(
                operation=self.operation,
                source_short=source_short,
                destination_short=dest_short
            ).set(speed)
        
        # Обновляем последний прогресс
        self.metrics.operation_last_progress.labels(
            operation=self.operation,
            source_short=source_short,
            destination_short=dest_short,
            current_step=self.current_step
        ).set(self.last_progress_percent)
        
        # Время с последнего обновления прогресса
        if self.last_progress_time:
            stale_time = current_time - self.last_progress_time
            self.metrics.operation_stale_seconds.labels(
                operation=self.operation,
                source_short=source_short,
                destination_short=dest_short,
                current_step=self.current_step
            ).set(stale_time)

    def update_progress(self, current_step: str, progress_percent: float):
        """Обновляется при каждом progress callback"""
        self.current_step = current_step
        self.last_progress_percent = progress_percent
        self.last_progress_time = time.time()
