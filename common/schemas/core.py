"""
核心 Schema 定义 - 跨模块共享的基础类型

定义统一的版本管理、交叉引用和时间戳格式。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SchemaVersion(str, Enum):
    """Schema 版本号"""
    V1 = '1.0.0'
    CURRENT = '1.0.0'


@dataclass
class CrossReference:
    """
    跨模块引用结构

    用于建立模块之间的关联关系：
    - todo -> plan (待办关联到计划)
    - time_record -> todo (时间记录关联到待办)
    - time_record -> plan (时间记录关联到计划)
    """
    source_module: str           # 来源模块: 'time-helper' | 'plan-helper' | 'to-dos'
    target_module: str           # 目标模块
    source_id: str               # 来源 ID
    target_id: str               # 目标 ID
    relation_type: str           # 关系类型: 'belongs_to' | 'tracks' | 'generates'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'source_module': self.source_module,
            'target_module': self.target_module,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type,
            'created_at': self.created_at,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CrossReference':
        return cls(
            source_module=data.get('source_module', ''),
            target_module=data.get('target_module', ''),
            source_id=data.get('source_id', ''),
            target_id=data.get('target_id', ''),
            relation_type=data.get('relation_type', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            metadata=data.get('metadata', {}),
        )


class UnifiedTimestamp:
    """统一时间戳工具"""

    @staticmethod
    def now() -> str:
        return datetime.now().isoformat()

    @staticmethod
    def today() -> str:
        return datetime.now().strftime('%Y-%m-%d')

    @staticmethod
    def parse(ts: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def format_relative(ts: str) -> str:
        dt = UnifiedTimestamp.parse(ts)
        if not dt:
            return ts
        now = datetime.now()
        diff = (now - dt).total_seconds()
        if diff < 0:
            abs_diff = abs(diff)
            if abs_diff < 60:
                return '即将到来'
            elif abs_diff < 3600:
                return f'{int(abs_diff // 60)}分钟后'
            elif abs_diff < 86400:
                return f'{int(abs_diff // 3600)}小时后'
            else:
                return f'{int(abs_diff // 86400)}天后'
        if diff < 60:
            return '刚刚'
        elif diff < 3600:
            return f'{int(diff // 60)}分钟前'
        elif diff < 86400:
            return f'{int(diff // 3600)}小时前'
        elif diff < 172800:
            return '昨天'
        elif diff < 604800:
            return f'{int(diff // 86400)}天前'
        else:
            return dt.strftime('%Y-%m-%d')
