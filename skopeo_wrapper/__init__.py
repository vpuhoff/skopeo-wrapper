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

try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"
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
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]