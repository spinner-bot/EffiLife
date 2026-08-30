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
        return plan.Plan.registry

    def load(self):
        pass

if __name__ == "__main__":
    test = Plans("test_0")