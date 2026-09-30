from __future__ import annotations

import importlib
import sys
from pathlib import Path

from common.bootstrap import EffiLifeIntegration, reset_integration


TODO_ROOT = Path(__file__).resolve().parents[1] / "to-dos"
if str(TODO_ROOT) not in sys.path:
    sys.path.insert(0, str(TODO_ROOT))
TodoAPI = importlib.import_module("src.api").TodoAPI


class RecordingTimeAPI:
    def __init__(self):
        self.records: list[tuple[dict, str | None]] = []

    def save_record(self, record: dict, day: str | None = None):
        self.records.append((record, day))
        return True


def test_completed_todo_creates_one_linked_time_record(tmp_path):
    integration = EffiLifeIntegration(data_root=str(tmp_path / "integration"))
    integration.initialize()
    todo_api = TodoAPI(data_dir=str(tmp_path / "todos"))
    time_api = RecordingTimeAPI()

    try:
        integration.register_todo_api(todo_api)
        integration.register_time_api(time_api)
        created = todo_api.create_todo(title="完成集成测试", time_estimate=40)
        assert created["success"]
        todo_id = created["data"]["id"]

        completed = todo_api.complete_todo(todo_id, time_spent=25)
        assert completed["success"]
        assert len(time_api.records) == 1

        record, day = time_api.records[0]
        assert day == record["日期"]
        assert record["related_todo_id"] == todo_id
        assert record["时长"] == 0.42

        refreshed = todo_api.get_todo(todo_id)["data"]
        assert refreshed["time_spent"] == 25
    finally:
        reset_integration()
