import pkgutil
import importlib

# 初始化 __all__ 列表，用于支持 from components import *
__all__ = []

# __path__ 是 Python 包的内置属性，指向当前包所在的目录
# pkgutil.iter_modules 会扫描该目录下的所有 Python 模块（不包含子目录）
for _, module_name, _ in pkgutil.iter_modules(__path__):
    # 动态导入当前模块 (相当于 from . import module_name)
    module = importlib.import_module(f".{module_name}", package=__name__)

    # 将导入的模块注入到当前包的命名空间中
    # 这样在主程序中才能通过 components.module_name 的方式访问
    globals()[module_name] = module

    # 将模块名加入 __all__，使其对 import * 可见
    __all__.append(module_name)
