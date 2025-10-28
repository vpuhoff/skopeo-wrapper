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
                self.blob_size_bytes.labels(operation=operation).observe(total_blob_size)
        
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
        elif url.startswith('dir://'):
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
                        key += f"{{{','.join(f'{k}={v}' for k, v in sample.labels.items())}}"
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
                 destination: Optional[str] = None):
        self.operation = operation
        self.metrics = metrics or get_metrics()
        self.source = source
        self.destination = destination
        self.start_time = None
        self.success = False
        self.blob_count = 0
        self.total_blob_size = 0
    
    def __enter__(self):
        self.start_time = self.metrics.record_operation_start(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.success = exc_type is None
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
        self.metrics.record_blob_processed(self.operation, blob_size)
