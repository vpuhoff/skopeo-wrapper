"""
Skopeo Wrapper - Python библиотека-обертка для утилиты skopeo
"""

from .skopeo_wrapper import (
    SkopeoWrapper,
    SkopeoProgressParser,
    ProgressInfo,
    BlobInfo,
    SkopeoOperation,
    create_progress_callback,
    get_progress_percentage
)
from .metrics import (
    SkopeoMetrics,
    OperationTracker,
    get_metrics,
    reset_metrics
)
from .metrics_server import (
    MetricsServer,
    start_metrics_server,
    start_global_metrics_server,
    stop_global_metrics_server,
    get_metrics_server
)

__version__ = "1.0.0"
__author__ = "Skopeo Wrapper Team"
__email__ = "skopeo-wrapper@example.com"
__description__ = "Python библиотека-обертка для утилиты skopeo с поддержкой парсинга прогресса"

__all__ = [
    "SkopeoWrapper",
    "SkopeoProgressParser", 
    "ProgressInfo",
    "BlobInfo",
    "SkopeoOperation",
    "create_progress_callback",
    "get_progress_percentage",
    "SkopeoMetrics",
    "OperationTracker",
    "get_metrics",
    "reset_metrics",
    "MetricsServer",
    "start_metrics_server",
    "start_global_metrics_server",
    "stop_global_metrics_server",
    "get_metrics_server",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]