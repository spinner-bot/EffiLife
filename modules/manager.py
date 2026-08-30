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
        return self.registry

    def switch(self):
        # plans层 to plan层
        plan.Plan.registry = self.registry
        return plan.Plan.registry

    def load(self, anchor=""):
        # 本地存储 to plans层
        temp = plan.Plan.registry
        plan.Plan.load_registry(anchor)
        temp2 = self.update()
        plan.Plan.registry = temp
        return temp2

    def save(self, anchor=""):
        # plans层 to 本地存储
        temp = plan.Plan.registry
        temp2 = self.switch()
        plan.Plan.save_registry(anchor)
        plan.Plan.registry = temp
        return temp2


if __name__ == "__main__":
    test = Plans("test_0")