#!/usr/bin/env python3
"""
Тесты для модуля метрик skopeo-wrapper
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from skopeo_wrapper.metrics import (
    SkopeoMetrics, 
    OperationTracker, 
    get_metrics, 
    reset_metrics
)


@pytest.fixture
def metrics():
    """Фикстура для создания экземпляра метрик"""
    return SkopeoMetrics()


@pytest.fixture
def mock_skopeo_wrapper():
    """Фикстура для мок-объекта SkopeoWrapper"""
    wrapper = Mock()
    wrapper.enable_metrics = True
    wrapper.metrics = SkopeoMetrics()
    return wrapper


class TestSkopeoMetrics:
    """Тесты для класса SkopeoMetrics"""
    
    def test_metrics_creation(self, metrics):
        """Тест создания экземпляра метрик"""
        assert metrics is not None
        assert metrics.registry is not None
        assert metrics.operations_total is not None
        assert metrics.operation_errors_total is not None
        assert metrics.operation_duration_seconds is not None
        assert metrics.blobs_processed_total is not None
        assert metrics.blob_size_bytes is not None
        assert metrics.active_operations is not None
        assert metrics.version_info is not None
    
    def test_record_operation_start(self, metrics):
        """Тест записи начала операции"""
        start_time = metrics.record_operation_start("copy")
        assert isinstance(start_time, float)
        assert start_time > 0
        
        # Проверяем, что счетчик активных операций увеличился
        active_ops = metrics.active_operations.labels(operation="copy")._value._value
        assert active_ops == 1
    
    def test_record_operation_end(self, metrics):
        """Тест записи завершения операции"""
        start_time = metrics.record_operation_start("copy")
        time.sleep(0.01)  # Небольшая задержка
        
        metrics.record_operation_end(
            operation="copy",
            success=True,
            start_time=start_time,
            source="docker://alpine:latest",
            destination="dir:/tmp/alpine",
            blob_count=3,
            total_blob_size=1024000
        )
        
        # Проверяем, что счетчик активных операций уменьшился
        active_ops = metrics.active_operations.labels(operation="copy")._value._value
        assert active_ops == 0
        
        # Проверяем, что операция записана
        ops_total = metrics.operations_total.labels(operation="copy", status="success")._value._value
        assert ops_total == 1
        
        # Проверяем blob'ы
        blobs_total = metrics.blobs_processed_total.labels(operation="copy", status="success")._value._value
        assert blobs_total == 3
    
    def test_record_error(self, metrics):
        """Тест записи ошибки"""
        metrics.record_error("copy", "TimeoutError")
        
        errors_total = metrics.operation_errors_total.labels(operation="copy", error_type="TimeoutError")._value._value
        assert errors_total == 1
    
    def test_record_blob_processed(self, metrics):
        """Тест записи обработки blob'а"""
        metrics.record_blob_processed("copy", 1024000)
        
        blobs_total = metrics.blobs_processed_total.labels(operation="copy", status="success")._value._value
        assert blobs_total == 1
    
    def test_extract_type_from_url(self, metrics):
        """Тест извлечения типа из URL"""
        assert metrics._extract_type_from_url("docker://alpine:latest") == "docker"
        assert metrics._extract_type_from_url("dir:/tmp/alpine") == "dir"
        assert metrics._extract_type_from_url("oci://alpine:latest") == "oci"
        assert metrics._extract_type_from_url("containers-storage://alpine:latest") == "containers_storage"
        assert metrics._extract_type_from_url("unknown://alpine:latest") == "unknown"
    
    def test_get_metrics(self, metrics):
        """Тест получения метрик в формате Prometheus"""
        metrics_data = metrics.get_metrics()
        assert isinstance(metrics_data, str)
        assert "skopeo_operations_total" in metrics_data
        assert "skopeo_operation_duration_seconds" in metrics_data
    
    def test_get_metrics_dict(self, metrics):
        """Тест получения метрик в виде словаря"""
        metrics_dict = metrics.get_metrics_dict()
        assert isinstance(metrics_dict, dict)
        assert len(metrics_dict) > 0


class TestOperationTracker:
    """Тесты для класса OperationTracker"""
    
    def test_operation_tracker_success(self, metrics):
        """Тест успешной операции с трекером"""
        with OperationTracker("copy", metrics, 
                             source="docker://alpine:latest",
                             destination="dir:/tmp/alpine") as tracker:
            tracker.add_blob(1024000)
            tracker.add_blob(2048000)
        
        # Проверяем, что операция записана
        ops_total = metrics.operations_total.labels(operation="copy", status="success")._value._value
        assert ops_total == 1
        
        # Проверяем blob'ы
        blobs_total = metrics.blobs_processed_total.labels(operation="copy", status="success")._value._value
        assert blobs_total == 2
    
    def test_operation_tracker_error(self, metrics):
        """Тест операции с ошибкой"""
        try:
            with OperationTracker("copy", metrics):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Проверяем, что ошибка записана
        ops_total = metrics.operations_total.labels(operation="copy", status="error")._value._value
        assert ops_total == 1
        
        errors_total = metrics.operation_errors_total.labels(operation="copy", error_type="ValueError")._value._value
        assert errors_total == 1


class TestGlobalMetrics:
    """Тесты для глобальных функций метрик"""
    
    def test_get_metrics(self):
        """Тест получения глобальных метрик"""
        metrics = get_metrics()
        assert metrics is not None
        assert isinstance(metrics, SkopeoMetrics)
    
    def test_reset_metrics(self):
        """Тест сброса глобальных метрик"""
        # Получаем текущие метрики
        metrics1 = get_metrics()
        
        # Сбрасываем метрики
        reset_metrics()
        
        # Получаем новые метрики
        metrics2 = get_metrics()
        
        # Проверяем, что это разные объекты
        assert metrics1 is not metrics2




class TestIntegration:
    """Интеграционные тесты"""
    
    def test_skopeo_wrapper_with_metrics(self):
        """Тест интеграции SkopeoWrapper с метриками"""
        from skopeo_wrapper import SkopeoWrapper
        
        # Создаем обертку с метриками
        skopeo = SkopeoWrapper(enable_metrics=True)
        assert skopeo.enable_metrics
        assert skopeo.metrics is not None
        
        # Проверяем методы метрик
        metrics_data = skopeo.get_metrics()
        assert isinstance(metrics_data, str)
        
        metrics_dict = skopeo.get_metrics_dict()
        assert isinstance(metrics_dict, dict)
    
    def test_skopeo_wrapper_without_metrics(self):
        """Тест SkopeoWrapper без метрик"""
        from skopeo_wrapper import SkopeoWrapper
        
        # Создаем обертку без метрик
        skopeo = SkopeoWrapper(enable_metrics=False)
        assert not skopeo.enable_metrics
        assert skopeo.metrics is None
        
        # Проверяем, что методы возвращают None
        assert skopeo.get_metrics() is None
        assert skopeo.get_metrics_dict() is None
    


if __name__ == "__main__":
    pytest.main([__file__])
