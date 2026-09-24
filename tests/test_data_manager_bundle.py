from common.data_manager import DataManager


def test_data_manager_bundle_includes_cross_refs(tmp_path):
    manager = DataManager(tmp_path / "data")
    manager.load()
    manager.link_entities("plan-helper", "plan-1", "to-dos", "todo-1", "generates")

    bundle = tmp_path / "backup.efl"
    manager.export_bundle(bundle, {"plans": [{"id": "plan-1"}]})
    _manifest, datasets = DataManager.read_bundle(bundle)

    assert datasets["plans"] == [{"id": "plan-1"}]
    assert datasets["cross_refs"][0]["source_id"] == "plan-1"
