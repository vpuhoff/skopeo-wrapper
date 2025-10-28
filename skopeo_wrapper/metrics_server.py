#!/usr/bin/env python3
"""
HTTP сервер для экспорта Prometheus метрик
"""

import threading
import time
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .metrics import get_metrics, SkopeoMetrics


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для метрик Prometheus"""
    
    def __init__(self, metrics: SkopeoMetrics, *args, **kwargs):
        self.metrics = metrics
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            
            # Генерируем метрики
            metrics_data = generate_latest(self.metrics.registry)
            self.wfile.write(metrics_data)
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Skopeo Wrapper Metrics</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #333; }
                    .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                    code { background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <h1>Skopeo Wrapper Metrics Server</h1>
                <p>Доступные эндпоинты:</p>
                <div class="endpoint">
                    <strong>GET /metrics</strong> - Prometheus метрики
                </div>
                <div class="endpoint">
                    <strong>GET /health</strong> - Проверка здоровья сервера
                </div>
                <div class="endpoint">
                    <strong>GET /</strong> - Эта страница
                </div>
                <p>Пример использования:</p>
                <code>curl http://localhost:8000/metrics</code>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Отключаем логирование запросов"""
        pass


class MetricsServer:
    """HTTP сервер для экспорта метрик Prometheus"""
    
    def __init__(self, host: str = 'localhost', port: int = 8000, metrics: Optional[SkopeoMetrics] = None):
        self.host = host
        self.port = port
        self.metrics = metrics or get_metrics()
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self) -> None:
        """Запускает сервер метрик в отдельном потоке"""
        if self.running:
            return
        
        def handler(*args, **kwargs):
            return MetricsHandler(self.metrics, *args, **kwargs)
        
        try:
            self.server = HTTPServer((self.host, self.port), handler)
            self.running = True
            
            def run_server():
                print(f"🚀 Запуск сервера метрик на http://{self.host}:{self.port}")
                print(f"📊 Метрики доступны по адресу: http://{self.host}:{self.port}/metrics")
                print(f"❤️  Проверка здоровья: http://{self.host}:{self.port}/health")
                self.server.serve_forever()
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            print(f"❌ Ошибка запуска сервера метрик: {e}")
            self.running = False
            raise
    
    def stop(self) -> None:
        """Останавливает сервер метрик"""
        if not self.running or not self.server:
            return
        
        self.running = False
        self.server.shutdown()
        self.server.server_close()
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
        
        print("🛑 Сервер метрик остановлен")
    
    def is_running(self) -> bool:
        """Проверяет, запущен ли сервер"""
        return self.running and self.server_thread and self.server_thread.is_alive()
    
    def get_url(self) -> str:
        """Возвращает URL сервера метрик"""
        return f"http://{self.host}:{self.port}"


def start_metrics_server(host: str = 'localhost', port: int = 8000, metrics: Optional[SkopeoMetrics] = None) -> MetricsServer:
    """
    Запускает сервер метрик
    
    Args:
        host: Хост для сервера
        port: Порт для сервера
        metrics: Экземпляр метрик (по умолчанию используется глобальный)
    
    Returns:
        Экземпляр MetricsServer
    """
    server = MetricsServer(host, port, metrics)
    server.start()
    return server


# Глобальный экземпляр сервера
_global_server: Optional[MetricsServer] = None


def get_metrics_server() -> Optional[MetricsServer]:
    """Возвращает глобальный экземпляр сервера метрик"""
    return _global_server


def start_global_metrics_server(host: str = 'localhost', port: int = 8000) -> MetricsServer:
    """Запускает глобальный сервер метрик"""
    global _global_server
    if _global_server is None or not _global_server.is_running():
        _global_server = start_metrics_server(host, port)
    return _global_server


def stop_global_metrics_server() -> None:
    """Останавливает глобальный сервер метрик"""
    global _global_server
    if _global_server:
        _global_server.stop()
        _global_server = None


if __name__ == "__main__":
    # Пример использования
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n🛑 Получен сигнал завершения, останавливаем сервер...")
        stop_global_metrics_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем сервер
    server = start_global_metrics_server()
    
    try:
        # Держим программу запущенной
        while server.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_global_metrics_server()
