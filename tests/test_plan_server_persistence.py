from pathlib import Path
import sys


PLAN_HELPER_DIR = Path(__file__).resolve().parents[1] / "plan-helper"
sys.path.insert(0, str(PLAN_HELPER_DIR))

from modules import api  # noqa: E402
from modules.plan import Plan  # noqa: E402
from web.server import PlanHelperHandler  # noqa: E402


def test_successful_plan_mutation_survives_registry_reload(tmp_path, monkeypatch):
    """The web persistence boundary must preserve raw plan data across restarts."""
    monkeypatch.chdir(tmp_path)
    Plan.registry.clear()

    created = api.create_plan(
        name="Persistent plan",
        date_tuple=(2026, 9, 27),
        sections=[{
            "name": "Section A",
            "tasks": [{"content": "Task A1", "time_minutes": 30}],
        }],
    )
    assert created.success

    persisted = PlanHelperHandler._persist_mutation(created)
    assert persisted.success
    assert (tmp_path / "data/system/registry/registry.json").exists()
    assert (tmp_path / "plan/1.json").exists()

    Plan.registry.clear()
    loaded = api.load_registry()
    assert loaded.success
    restored = api.get_plan_full(created.data["id"])
    assert restored.success
    assert restored.data["name"] == "Persistent plan"
    assert restored.data["sections"][0]["tasks"][0]["content"] == "Task A1"

    Plan.registry.clear()
