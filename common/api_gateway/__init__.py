"""
统一 API 网关

将三个模块的 API 注册到统一入口，提供跨模块查询接口。
"""

from .gateway import APIGateway
from .adapters import PlanAdapter, TodoAdapter, TimeAdapter

__all__ = ['APIGateway', 'PlanAdapter', 'TodoAdapter', 'TimeAdapter']
