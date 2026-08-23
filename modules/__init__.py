# modules/__init__.py

import pkgutil
import importlib

# ==========================================
# 1. 在这里定义你的“别名映射字典”
# 格式: "原始文件名(不带.py)": "你想用的别名"
# ==========================================
MODULE_ALIASES = {
    "wizard": "wiz",  # wizard.py 将被别名为 wiz
    "plan": "p",  # plan.py 将被别名为 p
    # 如果某个模块不需要别名，就不要把它写进这个字典里（比如 text.py）
}

__all__ = []

# 自动扫描并导入
for _, module_name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f".{module_name}", package=__name__)

    # 2. 决定最终暴露的名字：查字典，有别名就用别名，没别名就用原名
    exposed_name = MODULE_ALIASES.get(module_name, module_name)

    # 3. 将模块挂载到包上
    globals()[exposed_name] = module

    # 4. 加入 __all__ 列表
    __all__.append(exposed_name)
