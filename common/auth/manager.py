"""
用户身份认证管理器

基于本地文件的简单用户系统，支持多用户、登录状态管理。
"""

import json
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    password_hash: str = ''
    display_name: str = ''
    avatar: str = ''
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    preferences: dict = field(default_factory=dict)

    def to_dict(self, include_password: bool = False) -> dict:
        d = {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'avatar': self.avatar,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'preferences': self.preferences,
        }
        if include_password:
            d['password_hash'] = self.password_hash
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            id=data.get('id', ''),
            username=data.get('username', ''),
            password_hash=data.get('password_hash', ''),
            display_name=data.get('display_name', ''),
            avatar=data.get('avatar', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            last_login=data.get('last_login'),
            preferences=data.get('preferences', {}),
        )

    def to_public_dict(self) -> dict:
        """返回公开信息（不含密码）"""
        return self.to_dict(include_password=False)


class AuthManager:
    """
    身份认证管理器

    提供用户注册、登录、会话管理功能。
    数据存储在本地 JSON 文件中。
    """

    _instance = None

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / 'common' / 'data' / 'user'
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.users_file = data_dir / 'users.json'
        self.session_file = data_dir / 'current_user.json'

        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._users: List[User] = []
        self._current_user: Optional[User] = None
        self._loaded = False

    @classmethod
    def get_instance(cls, data_dir: Optional[str] = None) -> 'AuthManager':
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls(data_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        cls._instance = None

    def load(self):
        """加载用户数据"""
        self._users = self._load_users()
        self._current_user = self._load_session()
        self._loaded = True

    def _load_users(self) -> List[User]:
        """从文件加载用户列表"""
        if not self.users_file.exists():
            return []
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [User.from_dict(u) for u in data]
        except (json.JSONDecodeError, IOError):
            return []

    def _save_users(self):
        """保存用户列表"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump([u.to_dict(include_password=True) for u in self._users], f,
                      ensure_ascii=False, indent=2)

    def _load_session(self) -> Optional[User]:
        """加载当前登录用户"""
        if not self.session_file.exists():
            return None
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            user_id = data.get('user_id')
            for u in self._users:
                if u.id == user_id:
                    return u
            return None
        except (json.JSONDecodeError, IOError):
            return None

    def _save_session(self, user: Optional[User]):
        """保存当前登录会话"""
        if user:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump({'user_id': user.id, 'login_time': datetime.now().isoformat()}, f,
                          ensure_ascii=False, indent=2)
        else:
            if self.session_file.exists():
                self.session_file.unlink()

    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    # ========== 用户管理 ==========

    def register(
        self,
        username: str,
        password: str,
        display_name: str = '',
    ) -> dict:
        """
        注册新用户

        Returns:
            {'success': bool, 'user': User or None, 'message': str}
        """
        if not self._loaded:
            self.load()

        if not username or not username.strip():
            return {'success': False, 'user': None, 'message': '用户名不能为空'}

        if not password or len(password) < 4:
            return {'success': False, 'user': None, 'message': '密码至少4位'}

        # 检查用户名唯一
        for u in self._users:
            if u.username == username.strip():
                return {'success': False, 'user': None, 'message': '用户名已存在'}

        user = User(
            id=f"USR-{uuid.uuid4().hex[:8].upper()}",
            username=username.strip(),
            password_hash=self._hash_password(password),
            display_name=display_name.strip() or username.strip(),
        )

        self._users.append(user)
        self._save_users()

        return {'success': True, 'user': user, 'message': '注册成功'}

    def login(self, username: str, password: str) -> dict:
        """
        用户登录

        Returns:
            {'success': bool, 'user': User or None, 'message': str}
        """
        if not self._loaded:
            self.load()

        password_hash = self._hash_password(password)

        for u in self._users:
            if u.username == username and u.password_hash == password_hash:
                u.last_login = datetime.now().isoformat()
                self._current_user = u
                self._save_users()
                self._save_session(u)
                return {'success': True, 'user': u, 'message': '登录成功'}

        return {'success': False, 'user': None, 'message': '用户名或密码错误'}

    def logout(self) -> dict:
        """登出当前用户"""
        if self._current_user:
            username = self._current_user.username
            self._current_user = None
            self._save_session(None)
            return {'success': True, 'message': f'{username} 已登出'}
        return {'success': False, 'message': '没有已登录用户'}

    def get_current_user(self) -> Optional[User]:
        """获取当前登录用户"""
        if not self._loaded:
            self.load()
        return self._current_user

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.get_current_user() is not None

    def get_all_users(self) -> List[dict]:
        """获取所有用户（公开信息）"""
        if not self._loaded:
            self.load()
        return [u.to_public_dict() for u in self._users]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """按 ID 获取用户"""
        if not self._loaded:
            self.load()
        for u in self._users:
            if u.id == user_id:
                return u
        return None

    def update_preferences(self, user_id: str, preferences: dict) -> dict:
        """更新用户偏好设置"""
        if not self._loaded:
            self.load()

        user = self.get_user_by_id(user_id)
        if not user:
            return {'success': False, 'message': '用户不存在'}

        user.preferences.update(preferences)
        self._save_users()
        return {'success': True, 'user': user, 'message': '偏好已更新'}

    def delete_user(self, user_id: str) -> dict:
        """删除用户"""
        if not self._loaded:
            self.load()

        original_len = len(self._users)
        self._users = [u for u in self._users if u.id != user_id]

        if len(self._users) < original_len:
            if self._current_user and self._current_user.id == user_id:
                self._current_user = None
                self._save_session(None)
            self._save_users()
            return {'success': True, 'message': '用户已删除'}
        return {'success': False, 'message': '用户不存在'}

    def get_stats(self) -> dict:
        """获取用户统计"""
        if not self._loaded:
            self.load()
        return {
            'total_users': len(self._users),
            'current_user': self._current_user.to_public_dict() if self._current_user else None,
            'is_logged_in': self._current_user is not None,
        }
