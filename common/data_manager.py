"""
统一数据管理器

管理 EffiLife 共享的 data/ 目录结构，提供跨模块数据读写。

目录结构:
    data/
    ├── user/                  # 用户数据
    │   ├── current_user.json  # 当前用户
    │   └── users.json         # 用户列表
    ├── cross_refs/            # 跨模块引用
    │   └── references.json    # 引用关系表
    ├── events/                # 事件日志
    │   └── events.json        # 事件历史
    ├── backups/               # 全局备份
    ├── time-helper/           # time-helper 数据（符号链接或实际数据）
    ├── plan-helper/           # plan-helper 数据
    └── to-dos/                # to-dos 数据
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from .schemas.core import CrossReference, UnifiedTimestamp


class DataManager:
    """
    统一数据管理器

    提供跨模块的数据存储和检索功能。
    各模块保留自己的数据存储位置，DataManager 负责协调和索引。
    """

    _instance = None  # 单例

    def __init__(self, data_root: Optional[str] = None):
        if data_root is None:
            # 默认使用项目根目录下的 common/data
            project_root = Path(__file__).parent.parent
            data_root = project_root / 'common' / 'data'
        else:
            data_root = Path(data_root)

        self.data_root = data_root
        self.user_dir = data_root / 'user'
        self.cross_ref_dir = data_root / 'cross_refs'
        self.events_dir = data_root / 'events'
        self.backups_dir = data_root / 'backups'

        # 模块数据目录（指向各模块的实际数据位置）
        self.module_data_dir = data_root / 'modules'

        self._ensure_dirs()
        self._references: List[CrossReference] = []
        self._loaded = False

    @classmethod
    def get_instance(cls, data_root: Optional[str] = None) -> 'DataManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(data_root)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        cls._instance = None

    def _ensure_dirs(self):
        """确保所有目录存在"""
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.cross_ref_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.module_data_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        """加载所有共享数据"""
        self._references = self._load_references()
        self._loaded = True

    # ========== 跨模块引用管理 ==========

    def _load_references(self) -> List[CrossReference]:
        """加载跨模块引用"""
        ref_file = self.cross_ref_dir / 'references.json'
        if not ref_file.exists():
            return []
        try:
            with open(ref_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [CrossReference.from_dict(item) for item in data]
        except (json.JSONDecodeError, IOError):
            return []

    def _save_references(self):
        """保存跨模块引用"""
        ref_file = self.cross_ref_dir / 'references.json'
        with open(ref_file, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in self._references], f,
                      ensure_ascii=False, indent=2)

    def add_reference(self, ref: CrossReference):
        """添加跨模块引用"""
        if not self._loaded:
            self.load()
        self._references.append(ref)
        self._save_references()

    def remove_reference(self, source_id: str, target_id: str) -> bool:
        """删除跨模块引用"""
        if not self._loaded:
            self.load()
        original_len = len(self._references)
        self._references = [
            r for r in self._references
            if not (r.source_id == source_id and r.target_id == target_id)
        ]
        if len(self._references) < original_len:
            self._save_references()
            return True
        return False

    def get_references_by_source(self, source_id: str) -> List[CrossReference]:
        """获取某个实体作为来源的所有引用"""
        if not self._loaded:
            self.load()
        return [r for r in self._references if r.source_id == source_id]

    def get_references_by_target(self, target_id: str) -> List[CrossReference]:
        """获取某个实体作为目标的所有引用"""
        if not self._loaded:
            self.load()
        return [r for r in self._references if r.target_id == target_id]

    def get_references_by_type(self, relation_type: str) -> List[CrossReference]:
        """按关系类型获取引用"""
        if not self._loaded:
            self.load()
        return [r for r in self._references if r.relation_type == relation_type]

    def find_linked_ids(
        self,
        source_id: str,
        target_module: str,
        relation_type: Optional[str] = None,
    ) -> List[str]:
        """查找与 source_id 关联的 target_module 中的 ID 列表"""
        if not self._loaded:
            self.load()
        results = []
        for r in self._references:
            if r.source_id == source_id and r.target_module == target_module:
                if relation_type is None or r.relation_type == relation_type:
                    results.append(r.target_id)
        return results

    def link_entities(
        self,
        source_module: str,
        source_id: str,
        target_module: str,
        target_id: str,
        relation_type: str = 'belongs_to',
        metadata: Optional[dict] = None,
    ) -> CrossReference:
        """创建两个实体之间的关联"""
        ref = CrossReference(
            source_module=source_module,
            target_module=target_module,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            metadata=metadata or {},
        )
        self.add_reference(ref)
        return ref

    # ========== 全局备份 ==========

    def create_global_backup(self) -> str:
        """创建全局数据备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backups_dir / f'effilife_backup_{timestamp}.json'

        backup_data = {
            'backup_time': UnifiedTimestamp.now(),
            'references': [r.to_dict() for r in self._references],
        }

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        return str(backup_file)

    # ========== 模块数据目录注册 ==========

    def register_module_data_dir(self, module_name: str, path: str):
        """注册模块的数据目录路径"""
        config_file = self.module_data_dir / 'module_dirs.json'
        dirs = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    dirs = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        dirs[module_name] = str(path)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(dirs, f, ensure_ascii=False, indent=2)

    def get_module_data_dir(self, module_name: str) -> Optional[str]:
        """获取模块的数据目录路径"""
        config_file = self.module_data_dir / 'module_dirs.json'
        if not config_file.exists():
            return None
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                dirs = json.load(f)
            return dirs.get(module_name)
        except (json.JSONDecodeError, IOError):
            return None

    # ========== 统计 ==========

    def get_stats(self) -> dict:
        """获取共享数据统计"""
        if not self._loaded:
            self.load()

        by_type = {}
        by_module_pair = {}
        for r in self._references:
            by_type[r.relation_type] = by_type.get(r.relation_type, 0) + 1
            pair = f"{r.source_module}->{r.target_module}"
            by_module_pair[pair] = by_module_pair.get(pair, 0) + 1

        return {
            'total_references': len(self._references),
            'by_relation_type': by_type,
            'by_module_pair': by_module_pair,
        }
