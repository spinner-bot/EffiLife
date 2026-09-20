"""
统一身份认证模块

提供本地存储的简单用户系统，三个模块共享用户数据。
"""

from .manager import AuthManager, User

__all__ = ['AuthManager', 'User']
