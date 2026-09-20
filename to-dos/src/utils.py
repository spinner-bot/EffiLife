"""
to-dos 工具函数
ID 生成、时间处理等通用工具
"""

import uuid
import time
from datetime import datetime
from typing import Optional


class IdGenerator:
    """ID 生成器"""

    # 计数器，防止同日内 ID 冲突
    _daily_counter = 0
    _last_date = None

    @classmethod
    def reset_counter(cls):
        """重置计数器"""
        cls._daily_counter = 0
        cls._last_date = None

    @classmethod
    def generate_todo_id(cls, date: Optional[datetime] = None) -> str:
        """
        生成待办事项 ID
        格式：TODO-YYYYMMDD-XXXX
        示例：TODO-20260920-0001
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime('%Y%m%d')

        # 检查是否需要重置计数器
        if cls._last_date != date_str:
            cls._daily_counter = 0
            cls._last_date = date_str

        cls._daily_counter += 1
        seq = str(cls._daily_counter).zfill(4)
        return f"TODO-{date_str}-{seq}"

    @classmethod
    def generate_category_id(cls) -> str:
        """生成分类 ID"""
        return f"CAT-{uuid.uuid4().hex[:8].upper()}"

    @classmethod
    def generate_subtask_id(cls) -> str:
        """生成子任务 ID"""
        return f"SUB-{uuid.uuid4().hex[:8].upper()}"


class TimeHelper:
    """时间处理工具

    v0.5.0: 统一使用 yyyy/mm/dd 格式
    """

    # 日期格式常量
    DATE_FORMAT = '%Y/%m/%d'
    DATETIME_FORMAT = '%Y/%m/%d %H:%M'

    @staticmethod
    def now_iso() -> str:
        """返回当前 ISO 格式时间（内部存储仍用 ISO）"""
        return datetime.now().isoformat()

    @staticmethod
    def now_display() -> str:
        """返回当前显示格式时间 (yyyy/mm/dd HH:MM)"""
        return datetime.now().strftime(TimeHelper.DATETIME_FORMAT)

    @staticmethod
    def today_str() -> str:
        """返回今天日期字符串 (yyyy/mm/dd)"""
        return datetime.now().strftime(TimeHelper.DATE_FORMAT)

    @staticmethod
    def format_date(dt: datetime) -> str:
        """格式化日期为 yyyy/mm/dd"""
        return dt.strftime(TimeHelper.DATE_FORMAT)

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """格式化日期时间为 yyyy/mm/dd HH:MM"""
        return dt.strftime(TimeHelper.DATETIME_FORMAT)

    @staticmethod
    def parse_iso(iso_str: str) -> Optional[datetime]:
        """解析 ISO 格式时间（兼容旧数据）"""
        try:
            return datetime.fromisoformat(iso_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_display(display_str: str) -> Optional[datetime]:
        """解析显示格式时间 (yyyy/mm/dd 或 yyyy/mm/dd HH:MM)"""
        try:
            # 尝试完整格式
            return datetime.strptime(display_str, TimeHelper.DATETIME_FORMAT)
        except (ValueError, TypeError):
            try:
                # 尝试仅日期格式
                return datetime.strptime(display_str, TimeHelper.DATE_FORMAT)
            except (ValueError, TypeError):
                return None

    @staticmethod
    def iso_to_display(iso_str: str) -> str:
        """将 ISO 格式转换为显示格式"""
        dt = TimeHelper.parse_iso(iso_str)
        if dt:
            return TimeHelper.format_datetime(dt)
        return iso_str

    @staticmethod
    def display_to_iso(display_str: str) -> Optional[str]:
        """将显示格式转换为 ISO 格式"""
        dt = TimeHelper.parse_display(display_str)
        if dt:
            return dt.isoformat()
        return None

    @staticmethod
    def format_relative(iso_str: str) -> str:
        """
        返回相对时间描述
        如：'刚刚', '5分钟前', '2小时前', '昨天', '3天前'
        """
        dt = TimeHelper.parse_iso(iso_str)
        if not dt:
            return iso_str

        now = datetime.now()
        diff = (now - dt).total_seconds()

        if diff < 0:
            # 未来时间
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
            # 使用 yyyy/mm/dd 格式
            return dt.strftime(TimeHelper.DATE_FORMAT)

    @staticmethod
    def days_until_deadline(deadline: str) -> Optional[int]:
        """计算距离截止日期的天数"""
        dt = TimeHelper.parse_iso(deadline)
        if not dt:
            return None
        now = datetime.now()
        diff = dt - now
        return diff.days

    @staticmethod
    def deadline_status(deadline: str) -> str:
        """
        截止日期状态
        返回：'overdue', 'today', 'tomorrow', 'this_week', 'upcoming'
        """
        days = TimeHelper.days_until_deadline(deadline)
        if days is None:
            return 'unknown'
        if days < 0:
            return 'overdue'
        elif days == 0:
            return 'today'
        elif days == 1:
            return 'tomorrow'
        elif days <= 7:
            return 'this_week'
        else:
            return 'upcoming'


def format_duration(minutes: int) -> str:
    """将分钟数格式化为可读时间"""
    if minutes < 60:
        return f'{minutes}分钟'
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f'{hours}小时'
    return f'{hours}小时{mins}分钟'
