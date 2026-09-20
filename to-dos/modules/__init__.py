"""
    ============ modules/__init__.py ============
    to-dos 模块包初始化
        by spinner-bot
"""

import pkgutil
import importlib

# ==========================================
# 别名映射
# ==========================================
MODULE_ALIASES = {
    "todo": "t",
    "manager": "mgr",
    "storage": "st",
    "categories": "cat",
}

__all__ = []
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f".{module_name}", package=__name__)
    exposed_name = MODULE_ALIASES.get(module_name, module_name)
    globals()[exposed_name] = module
    __all__.append(exposed_name)
