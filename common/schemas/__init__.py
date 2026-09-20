"""
统一 JSON Schema 定义

所有模块共享的数据格式规范，确保跨模块数据互通。
"""

from .core import SchemaVersion, CrossReference, UnifiedTimestamp
from .models import (
    UnifiedPlan, UnifiedTodo, UnifiedTimeRecord,
    UnifiedUser, UnifiedCategory,
)

__all__ = [
    'SchemaVersion', 'CrossReference', 'UnifiedTimestamp',
    'UnifiedPlan', 'UnifiedTodo', 'UnifiedTimeRecord',
    'UnifiedUser', 'UnifiedCategory',
]
