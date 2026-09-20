"""
    ============ modules/storage.py ============
    持久化存储层：管理 Todo 的文件读写与注册表
        by spinner-bot
"""

import json
import os
from datetime import datetime
from pathlib import Path

from .todo import Todo, now_iso

# ==========================================
# 默认路径
# ==========================================

DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"
TODOS_DIR = "todos"
ARCHIVE_DIR = "archive"
SYSTEM_DIR = "system"

REGISTRY_FILE = "registry.json"
CONFIG_FILE = "config.json"
CATEGORIES_FILE = "categories.json"


# ==========================================
# Registry（注册表）
# ==========================================

def _empty_registry() -> dict:
    return {
        "next_id": 1,
        "active_ids": [],
        "archived_ids": [],
        "stats": {
            "total_created": 0,
            "total_completed": 0,
            "total_cancelled": 0,
        },
    }


def load_registry(data_dir: str | Path = None) -> dict:
    """加载注册表"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    reg_path = data_dir / SYSTEM_DIR / REGISTRY_FILE
    if not reg_path.exists():
        return _empty_registry()
    with open(reg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry: dict, data_dir: str | Path = None) -> None:
    """保存注册表"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    reg_path = data_dir / SYSTEM_DIR / REGISTRY_FILE
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def generate_id(registry: dict) -> str:
    """生成下一个 ID"""
    next_num = registry.get("next_id", 1)
    return f"td_{next_num:04d}"


def increment_id(registry: dict) -> None:
    """递增 ID 计数器"""
    registry["next_id"] = registry.get("next_id", 1) + 1


# ==========================================
# Todo 文件操作
# ==========================================

def _todo_path(todo_id: str, data_dir: str | Path = None) -> Path:
    """获取 todo 文件路径"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    return data_dir / TODOS_DIR / f"{todo_id}.json"


def save_todo(todo: Todo, data_dir: str | Path = None) -> str:
    """保存单个 todo 到文件"""
    path = _todo_path(todo.id, data_dir)
    todo.save(path)
    return todo.id


def load_todo(todo_id: str, data_dir: str | Path = None) -> Todo | None:
    """从文件加载单个 todo"""
    path = _todo_path(todo_id, data_dir)
    if not path.exists():
        return None
    return Todo.load(path)


def delete_todo_file(todo_id: str, data_dir: str | Path = None) -> bool:
    """删除 todo 文件"""
    path = _todo_path(todo_id, data_dir)
    if path.exists():
        os.remove(path)
        return True
    return False


def list_all_todo_files(data_dir: str | Path = None) -> list[str]:
    """列出所有 todo 文件，返回 id 列表"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    todos_dir = data_dir / TODOS_DIR
    if not todos_dir.exists():
        return []
    return [
        f.stem for f in todos_dir.iterdir()
        if f.is_file() and f.suffix == ".json" and f.stem.startswith("td_")
    ]


def load_all_todos(data_dir: str | Path = None) -> list[Todo]:
    """加载所有 todo"""
    result = []
    for todo_id in list_all_todo_files(data_dir):
        todo = load_todo(todo_id, data_dir)
        if todo:
            result.append(todo)
    return result


# ==========================================
# 归档操作
# ==========================================

def archive_todo(todo: Todo, data_dir: str | Path = None) -> str:
    """将 todo 移入归档目录（按完成月份）"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    # 确定归档子目录
    if todo.completed_at:
        month_dir = datetime.fromisoformat(todo.completed_at).strftime("%Y-%m")
    else:
        month_dir = datetime.now().strftime("%Y-%m")

    archive_path = data_dir / ARCHIVE_DIR / month_dir / f"{todo.id}.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    todo.archived = True
    todo.save(archive_path)

    # 删除原文件
    delete_todo_file(todo.id, data_dir)

    return todo.id


def load_archived_todos(month: str = None, data_dir: str | Path = None) -> list[Todo]:
    """加载归档的 todo（可选按月筛选，格式 YYYY-MM）"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    archive_dir = data_dir / ARCHIVE_DIR

    if not archive_dir.exists():
        return []

    result = []
    if month:
        month_path = archive_dir / month
        if month_path.exists():
            for f in month_path.iterdir():
                if f.is_file() and f.suffix == ".json":
                    result.append(Todo.load(f))
    else:
        for month_path in archive_dir.iterdir():
            if month_path.is_dir():
                for f in month_path.iterdir():
                    if f.is_file() and f.suffix == ".json":
                        result.append(Todo.load(f))
    return result


# ==========================================
# 配置与分类
# ==========================================

def load_config(data_dir: str | Path = None) -> dict:
    """加载模块配置"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    config_path = data_dir / SYSTEM_DIR / CONFIG_FILE
    if not config_path.exists():
        return _default_config()
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, data_dir: str | Path = None) -> None:
    """保存模块配置"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    config_path = data_dir / SYSTEM_DIR / CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _default_config() -> dict:
    return {
        "version": "0.1.0",
        "default_priority": 2,
        "default_category": "",
        "auto_archive_on_complete": False,
        "sort_by": "created_at",
        "sort_order": "desc",
    }


def load_categories(data_dir: str | Path = None) -> dict:
    """加载分类定义"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    cat_path = data_dir / SYSTEM_DIR / CATEGORIES_FILE
    if not cat_path.exists():
        return _default_categories()
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_categories(categories: dict, data_dir: str | Path = None) -> None:
    """保存分类定义"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    cat_path = data_dir / SYSTEM_DIR / CATEGORIES_FILE
    cat_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)


def _default_categories() -> dict:
    return {
        "categories": [
            {"name": "work", "color": "#3B82F6", "icon": "briefcase"},
            {"name": "study", "color": "#10B981", "icon": "book"},
            {"name": "life", "color": "#F59E0B", "icon": "home"},
            {"name": "other", "color": "#6B7280", "icon": "tag"},
        ]
    }


# ==========================================
# 初始化
# ==========================================

def init_data_dir(data_dir: str | Path = None) -> dict:
    """初始化数据目录，返回各文件创建状态"""
    data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    status = {}

    dirs = [
        data_dir / TODOS_DIR,
        data_dir / ARCHIVE_DIR,
        data_dir / SYSTEM_DIR,
    ]

    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            status[str(d)] = "created"
        except Exception as e:
            status[str(d)] = f"error: {e}"

    # 初始化默认文件（如不存在）
    reg_path = data_dir / SYSTEM_DIR / REGISTRY_FILE
    if not reg_path.exists():
        save_registry(_empty_registry(), data_dir)
        status[str(reg_path)] = "created"
    else:
        status[str(reg_path)] = "existing"

    config_path = data_dir / SYSTEM_DIR / CONFIG_FILE
    if not config_path.exists():
        save_config(_default_config(), data_dir)
        status[str(config_path)] = "created"
    else:
        status[str(config_path)] = "existing"

    cat_path = data_dir / SYSTEM_DIR / CATEGORIES_FILE
    if not cat_path.exists():
        save_categories(_default_categories(), data_dir)
        status[str(cat_path)] = "created"
    else:
        status[str(cat_path)] = "existing"

    return status
