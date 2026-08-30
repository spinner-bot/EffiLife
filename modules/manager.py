"""
    ====== modules/manager.py ======
    No description.
        by spinner-bot
"""

from . import plan

class Plans:
    def __init__(self, name):
        self.name = str(name)
        self.registry = Plans.get_registry()

    @staticmethod
    def get_registry():
        # 仅获取（plan层：data）
        return plan.Plan.registry

    def update(self):
        # plan层 to plans层
        self.registry = Plans.get_registry()

    def switch(self):
        # plans层 to plan层
        plan.Plan.registry = self.registry

    def load(self):
        # 本地存储 to plans层
        temp = plan.Plan.registry
        plan.Plan.registry = {}


if __name__ == "__main__":
    test = Plans("test_0")