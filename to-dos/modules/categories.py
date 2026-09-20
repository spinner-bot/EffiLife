"""
    ============ modules/categories.py ============
    分类管理：独立的分类操作工具
        by spinner-bot
"""

from . import storage


# ==========================================
# 预定义颜色方案
# ==========================================

CATEGORY_COLORS = {
    "work": "#3B82F6",      # 蓝
    "study": "#10B981",     # 绿
    "life": "#F59E0B",      # 橙
    "other": "#6B7280",     # 灰
    "health": "#EF4444",    # 红
    "finance": "#8B5CF6",   # 紫
    "social": "#EC4899",    # 粉
    "hobby": "#14B8A6",     # 青
}

CATEGORY_ICONS = {
    "work": "briefcase",
    "study": "book",
    "life": "home",
    "other": "tag",
    "health": "heart",
    "finance": "dollar",
    "social": "users",
    "hobby": "star",
}


def get_all(data_dir=None) -> list[dict]:
    """获取所有分类"""
    return storage.load_categories(data_dir)["categories"]


def get_by_name(name: str, data_dir=None) -> dict | None:
    """按名称获取分类"""
    for cat in get_all(data_dir):
        if cat["name"] == name:
            return cat
    return None


def add(name: str, color: str = None, icon: str = None, data_dir=None) -> dict:
    """添加分类"""
    categories_data = storage.load_categories(data_dir)

    # 检查重复
    for cat in categories_data["categories"]:
        if cat["name"] == name:
            raise ValueError(f"Category already exists: {name}")

    new_cat = {
        "name": name,
        "color": color or CATEGORY_COLORS.get(name, "#6B7280"),
        "icon": icon or CATEGORY_ICONS.get(name, "tag"),
    }
    categories_data["categories"].append(new_cat)
    storage.save_categories(categories_data, data_dir)
    return new_cat


def remove(name: str, data_dir=None) -> bool:
    """删除分类"""
    categories_data = storage.load_categories(data_dir)
    original_count = len(categories_data["categories"])
    categories_data["categories"] = [
        c for c in categories_data["categories"] if c["name"] != name
    ]
    if len(categories_data["categories"]) < original_count:
        storage.save_categories(categories_data, data_dir)
        return True
    return False


def rename(old_name: str, new_name: str, data_dir=None) -> dict:
    """重命名分类"""
    categories_data = storage.load_categories(data_dir)
    for cat in categories_data["categories"]:
        if cat["name"] == old_name:
            cat["name"] = new_name
            storage.save_categories(categories_data, data_dir)
            return cat
    raise ValueError(f"Category not found: {old_name}")


def update_color(name: str, color: str, data_dir=None) -> dict:
    """更新分类颜色"""
    categories_data = storage.load_categories(data_dir)
    for cat in categories_data["categories"]:
        if cat["name"] == name:
            cat["color"] = color
            storage.save_categories(categories_data, data_dir)
            return cat
    raise ValueError(f"Category not found: {name}")


def names(data_dir=None) -> list[str]:
    """获取所有分类名称"""
    return [c["name"] for c in get_all(data_dir)]
