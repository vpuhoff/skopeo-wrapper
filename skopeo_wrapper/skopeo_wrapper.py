#!/usr/bin/env python3
"""
Python библиотека-обертка для утилиты skopeo с парсингом прогресса.
"""

import subprocess
import threading
import time
import re
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from .metrics import SkopeoMetrics, OperationTracker, get_metrics


class SkopeoOperation(Enum):
    """Типы операций skopeo"""
    COPY = "copy"
    INSPECT = "inspect"
    DELETE = "delete"
    MANIFEST_DIGEST = "manifest-digest"


@dataclass
class BlobInfo:
    """Информация о blob-объекте"""
    sha256: str
    size: Optional[int] = None
    status: str = "pending"  # pending, copying, copied, error


@dataclass
class ProgressInfo:
    """Информация о прогрессе операции"""
    operation: str
    current_step: str
    total_blobs: int = 0
    copied_blobs: int = 0
    current_blob: Optional[BlobInfo] = None
    manifest_written: bool = False
    signatures_stored: bool = False
    error: Optional[str] = None
    completed: bool = False
    parser: Optional['SkopeoProgressParser'] = None


class SkopeoProgressParser:
    """Парсер для извлечения информации о прогрессе из вывода skopeo"""
    
    def __init__(self):
        self.progress = ProgressInfo(operation="", current_step="")
        self.blobs: Dict[str, BlobInfo] = {}
        
        # Регулярные выражения для парсинга
        self.patterns = {
            'getting_signatures': re.compile(r'Getting image source signatures'),
            'copying_blob': re.compile(r'Copying blob sha256:([a-f0-9]{64})'),
            'copying_config': re.compile(r'Copying config sha256:([a-f0-9]{64})'),
            'writing_manifest': re.compile(r'Writing manifest to image destination'),
            'storing_signatures': re.compile(r'Storing signatures'),
            'error': re.compile(r'Error: (.+)'),
            'blob_size': re.compile(r'Copying blob sha256:([a-f0-9]{64}) \((\d+) bytes\)'),
        }
    
    def parse_line(self, line: str) -> Optional[ProgressInfo]:
        """Парсит строку вывода skopeo и обновляет информацию о прогрессе"""
        line = line.strip()
        
        if not line:
            return None
            
        # Получение подписей
        if self.patterns['getting_signatures'].match(line):
            self.progress.operation = "copy"
            self.progress.current_step = "getting_signatures"
            return self.progress
        
        # Копирование blob с размером
        blob_size_match = self.patterns['blob_size'].match(line)
        if blob_size_match:
            sha256 = blob_size_match.group(1)
            size = int(blob_size_match.group(2))
            self.blobs[sha256] = BlobInfo(sha256=sha256, size=size, status="copying")
            self.progress.current_blob = self.blobs[sha256]
            self.progress.current_step = "copying_blob"
            return self.progress
        
        # Копирование blob без размера
        blob_match = self.patterns['copying_blob'].match(line)
        if blob_match:
            sha256 = blob_match.group(1)
            if sha256 not in self.blobs:
                self.blobs[sha256] = BlobInfo(sha256=sha256, status="copying")
            self.progress.current_blob = self.blobs[sha256]
            self.progress.current_step = "copying_blob"
            return self.progress
        
        # Копирование config
        config_match = self.patterns['copying_config'].match(line)
        if config_match:
            sha256 = config_match.group(1)
            if sha256 not in self.blobs:
                self.blobs[sha256] = BlobInfo(sha256=sha256, status="copying")
            self.progress.current_blob = self.blobs[sha256]
            self.progress.current_step = "copying_config"
            return self.progress
        
        # Запись манифеста
        if self.patterns['writing_manifest'].match(line):
            self.progress.manifest_written = True
            self.progress.current_step = "writing_manifest"
            return self.progress
        
        # Сохранение подписей
        if self.patterns['storing_signatures'].match(line):
            self.progress.signatures_stored = True
            self.progress.current_step = "storing_signatures"
            return self.progress
        
        # Ошибка
        error_match = self.patterns['error'].match(line)
        if error_match:
            self.progress.error = error_match.group(1)
            self.progress.current_step = "error"
            return self.progress
        
        return None
    
    def get_progress_percentage(self) -> float:
        """Возвращает процент выполнения операции"""
        if self.progress.error:
            return 0.0
        
        if self.progress.completed:
            return 100.0
        
        # Примерная оценка прогресса на основе этапов
        if self.progress.current_step == "getting_signatures":
            return 10.0
        elif self.progress.current_step == "copying_blob":
            # Базовый прогресс + прогресс по blob'ам
            base_progress = 20.0
            blob_progress = (len(self.blobs) / max(1, len(self.blobs) + 1)) * 50.0
            return min(base_progress + blob_progress, 70.0)
        elif self.progress.current_step == "copying_config":
            return 75.0
        elif self.progress.current_step == "writing_manifest":
            return 90.0
        elif self.progress.current_step == "storing_signatures":
            return 95.0
        
        return 0.0


def get_progress_percentage(progress: ProgressInfo, parser: SkopeoProgressParser) -> float:
    """Возвращает процент выполнения операции"""
    if progress.error:
        return 0.0
    
    if progress.completed:
        return 100.0
    
    # Примерная оценка прогресса на основе этапов
    if progress.current_step == "getting_signatures":
        return 10.0
    elif progress.current_step == "copying_blob":
        # Базовый прогресс + прогресс по blob'ам
        base_progress = 20.0
        blob_progress = (len(parser.blobs) / max(1, len(parser.blobs) + 1)) * 50.0
        return min(base_progress + blob_progress, 70.0)
    elif progress.current_step == "copying_config":
        return 75.0
    elif progress.current_step == "writing_manifest":
        return 90.0
    elif progress.current_step == "storing_signatures":
        return 95.0
    
    return 0.0


class SkopeoWrapper:
    """Основной класс-обертка для skopeo"""
    
    def __init__(self, skopeo_path: str = "skopeo", metrics: Optional[SkopeoMetrics] = None, enable_metrics: bool = True):
        self.skopeo_path = skopeo_path
        self.parser = SkopeoProgressParser()
        self.enable_metrics = enable_metrics
        self.metrics = metrics if metrics is not None else (get_metrics() if enable_metrics else None)
    
    def _run_command(self, 
                    command: List[str], 
                    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
                    timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Выполняет команду skopeo с мониторингом прогресса"""
        
        # Сбрасываем состояние парсера
        self.parser = SkopeoProgressParser()
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            def monitor_stderr():
                """Мониторинг stderr для парсинга прогресса"""
                for line in iter(process.stderr.readline, ''):
                    if line.strip():
                        progress_info = self.parser.parse_line(line)
                        if progress_info and progress_callback:
                            # Добавляем ссылку на парсер для доступа к blob'ам
                            progress_info.parser = self.parser
                            progress_callback(progress_info)
            
            # Запускаем мониторинг в отдельном потоке
            stderr_thread = threading.Thread(target=monitor_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()
            
            # Ждем завершения процесса
            stdout, stderr = process.communicate(timeout=timeout)
            
            # Завершаем мониторинг
            stderr_thread.join(timeout=1)
            
            # Отмечаем операцию как завершенную
            if process.returncode == 0:
                self.parser.progress.completed = True
                self.parser.progress.current_step = "completed"
            else:
                self.parser.progress.error = f"Process exited with code {process.returncode}"
            
            if progress_callback:
                # Добавляем ссылку на парсер для финального callback
                self.parser.progress.parser = self.parser
                progress_callback(self.parser.progress)
            
            return process.returncode == 0, stdout, stderr
            
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "", "Operation timed out"
        except Exception as e:
            return False, "", str(e)
    
    def copy(self, 
             source: str, 
             destination: str,
             progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
             timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Копирует образ из source в destination"""
        
        if self.enable_metrics and self.metrics:
            with OperationTracker("copy", self.metrics, source, destination) as tracker:
                command = [self.skopeo_path, "copy", source, destination]
                
                # Создаем wrapper для progress_callback
                original_callback = progress_callback
                
                def wrapped_callback(progress_info):
                    if hasattr(progress_info, 'parser'):
                        progress_percent = progress_info.parser.get_progress_percentage()
                        tracker.update_progress(progress_info.current_step, progress_percent)
                    
                    if original_callback:
                        original_callback(progress_info)
                
                # Используем wrapped_callback вместо progress_callback
                success, stdout, stderr = self._run_command(command, wrapped_callback, timeout)
                
                # Обновляем статистику blob'ов из парсера
                if hasattr(self.parser, 'blobs'):
                    for blob in self.parser.blobs.values():
                        tracker.add_blob(blob.size)
                
                return success, stdout, stderr
        else:
            command = [self.skopeo_path, "copy", source, destination]
            return self._run_command(command, progress_callback, timeout)
    
    def inspect(self, 
                image: str,
                progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
                timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Получает информацию об образе"""
        
        if self.enable_metrics and self.metrics:
            with OperationTracker("inspect", self.metrics, source=image):
                command = [self.skopeo_path, "inspect", image]
                return self._run_command(command, progress_callback, timeout)
        else:
            command = [self.skopeo_path, "inspect", image]
            return self._run_command(command, progress_callback, timeout)
    
    def delete(self, 
               image: str,
               progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
               timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Удаляет образ"""
        
        if self.enable_metrics and self.metrics:
            with OperationTracker("delete", self.metrics, source=image):
                command = [self.skopeo_path, "delete", image]
                return self._run_command(command, progress_callback, timeout)
        else:
            command = [self.skopeo_path, "delete", image]
            return self._run_command(command, progress_callback, timeout)
    
    def get_manifest_digest(self, 
                           image: str,
                           progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
                           timeout: Optional[int] = None) -> Tuple[bool, str, str]:
        """Получает digest манифеста образа"""
        
        if self.enable_metrics and self.metrics:
            with OperationTracker("manifest_digest", self.metrics, source=image):
                command = [self.skopeo_path, "manifest-digest", image]
                return self._run_command(command, progress_callback, timeout)
        else:
            command = [self.skopeo_path, "manifest-digest", image]
            return self._run_command(command, progress_callback, timeout)
    
    def image_exists(self, 
                    image: str,
                    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
                    timeout: Optional[int] = None) -> Tuple[bool, bool, str]:
        """
        Проверяет существование образа в репозитории
        
        Args:
            image: URL образа для проверки
            progress_callback: Callback для отображения прогресса
            timeout: Таймаут операции в секундах
            
        Returns:
            Tuple[bool, bool, str]: (success, exists, error_message)
            - success: True если операция выполнена успешно
            - exists: True если образ существует, False если нет
            - error_message: Сообщение об ошибке или пустая строка
        """
        
        if self.enable_metrics and self.metrics:
            with OperationTracker("image_exists", self.metrics, source=image):
                command = [self.skopeo_path, "inspect", image]
                success, stdout, stderr = self._run_command(command, progress_callback, timeout)
                
                if success:
                    return True, True, ""
                else:
                    # Анализируем ошибки для определения существования образа
                    if "manifest unknown" in stderr.lower():
                        return True, False, ""
                    elif "error reading manifest" in stderr.lower():
                        return True, False, ""
                    elif "repository not found" in stderr.lower():
                        return True, False, ""
                    elif "unauthorized" in stderr.lower():
                        return False, False, f"Unauthorized access: {stderr}"
                    elif "forbidden" in stderr.lower():
                        return False, False, f"Access forbidden: {stderr}"
                    else:
                        # Если stderr пустой, но success=False, считаем что образ не существует
                        if not stderr.strip():
                            return True, False, ""
                        else:
                            return False, False, f"Unexpected error: {stderr}"
        else:
            command = [self.skopeo_path, "inspect", image]
            success, stdout, stderr = self._run_command(command, progress_callback, timeout)
            
            if success:
                return True, True, ""
            else:
                # Анализируем ошибки для определения существования образа
                if "manifest unknown" in stderr.lower():
                    return True, False, ""
                elif "error reading manifest" in stderr.lower():
                    return True, False, ""
                elif "repository not found" in stderr.lower():
                    return True, False, ""
                elif "unauthorized" in stderr.lower():
                    return False, False, f"Unauthorized access: {stderr}"
                elif "forbidden" in stderr.lower():
                    return False, False, f"Access forbidden: {stderr}"
                else:
                    # Если stderr пустой, но success=False, считаем что образ не существует
                    if not stderr.strip():
                        return True, False, ""
                    else:
                        return False, False, f"Unexpected error: {stderr}"
    
    def get_metrics(self) -> Optional[str]:
        """Возвращает метрики в формате Prometheus"""
        if self.metrics:
            return self.metrics.get_metrics()
        return None
    
    def get_metrics_dict(self) -> Optional[Dict[str, Any]]:
        """Возвращает метрики в виде словаря"""
        if self.metrics:
            return self.metrics.get_metrics_dict()
        return None
    
    def reset_metrics(self) -> None:
        """Сбрасывает метрики"""
        if self.metrics:
            from .metrics import reset_metrics
            reset_metrics()
            self.metrics = get_metrics() if self.enable_metrics else None


def create_progress_callback(show_progress: bool = True) -> Callable[[ProgressInfo], None]:
    """Создает callback для отображения прогресса"""
    
    def progress_callback(progress: ProgressInfo):
        if not show_progress:
            return
            
        percentage = progress.parser.get_progress_percentage() if hasattr(progress, 'parser') else 0.0
        
        if progress.error:
            print(f"❌ Ошибка: {progress.error}")
        elif progress.completed:
            print(f"✅ Операция завершена успешно")
        else:
            status_emoji = {
                "getting_signatures": "🔍",
                "copying_blob": "📦",
                "writing_manifest": "📝",
                "storing_signatures": "🔐"
            }.get(progress.current_step, "⏳")
            
            print(f"{status_emoji} {progress.current_step}: {percentage:.1f}%")
            
            if progress.current_blob:
                blob_info = f" (blob: {progress.current_blob.sha256[:12]}...)"
                if progress.current_blob.size:
                    blob_info += f" {progress.current_blob.size} bytes"
                print(f"   {blob_info}")
    
    return progress_callback


# Пример использования
if __name__ == "__main__":
    # Создаем экземпляр обертки
    skopeo = SkopeoWrapper()
    
    # Создаем callback для отображения прогресса
    progress_callback = create_progress_callback(show_progress=True)
    
    # Пример копирования образа
    print("Копирование образа alpine:latest...")
    success, stdout, stderr = skopeo.copy(
        source="docker://docker.io/library/alpine:latest",
        destination="dir:/tmp/skopeo_test/alpine_with_progress",
        progress_callback=progress_callback
    )
    
    if success:
        print("✅ Копирование завершено успешно!")
    else:
        print(f"❌ Ошибка копирования: {stderr}")
