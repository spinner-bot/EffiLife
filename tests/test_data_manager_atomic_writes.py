from pathlib import Path

from common.data_manager import DataManager


SOURCE = Path("common/data_manager.py").read_text(encoding="utf-8")


def test_data_manager_json_outputs_share_atomic_writer():
    assert "def _atomic_write_json(path: Path, payload: Any)" in SOURCE
    assert "os.replace(temporary_path, path)" in SOURCE
    assert "_atomic_write_json(ref_file" in SOURCE
    assert "_atomic_write_json(backup_file" in SOURCE
    assert "_atomic_write_json(config_file" in SOURCE


def test_reference_write_round_trip_remains_compatible(tmp_path):
    manager = DataManager(tmp_path / "data")
    manager.link_entities("plan-helper", "plan-1", "to-dos", "todo-1", "generates")

    restored = DataManager(tmp_path / "data")
    restored.load()

    assert restored.find_linked_ids("plan-1", "to-dos", "generates") == ["todo-1"]
