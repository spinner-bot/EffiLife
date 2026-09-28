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


def test_data_manager_workspace_bundle_uses_canonical_contract(tmp_path):
    manager = DataManager(tmp_path / "data")
    bundle = tmp_path / "workspace.efl"

    written = manager.export_workspace_bundle(
        str(bundle),
        app={"version": "dev"},
        records=[],
        todos=[],
        todo_categories=[],
        plan_helper={"plans": []},
    )

    assert written == str(bundle)
    manifest, datasets = manager.read_workspace_bundle(bundle)
    assert manifest["datasets"] == [
        "app",
        "plan_helper",
        "records",
        "todo_categories",
        "todos",
    ]
    assert datasets["app"] == {"version": "dev"}
    assert manager.verify_workspace_bundle(bundle)["integrity"] == "verified"
