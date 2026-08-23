# modules/__init__.py

import pkgutil
import importlib

# ==========================================
# 1.             别名映射字典
# ==========================================
MODULE_ALIASES = \
{
    "wizard": "wz",
    "plan": "p",
    "text": "tx",
    "local": "lc"
}
# ==========================================


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