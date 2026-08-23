# modules/__init__.py

import pkgutil
import importlib

# 初始化 __all__ 列表
__all__ = []

# 自动扫描 modules 文件夹下的所有 .py 文件
for _, module_name, _ in pkgutil.iter_modules(__path__):
    # 动态导入模块 (相当于 from . import plan, from . import text 等)
    module = importlib.import_module(f".{module_name}", package=__name__)

    # 将模块挂载到 modules 包上，这样主程序才能用 m.plan, m.text
    globals()[module_name] = module

    # 加入 __all__
    __all__.append(module_name)
