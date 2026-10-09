import json
import zipfile
from unittest.mock import patch

import pytest

from common.data_exchange import (
    CANONICAL_WORKSPACE_DATASETS,
    export_bundle,
    export_workspace_bundle,
    import_bundle,
    inspect_bundle,
    read_bundle,
    read_workspace_bundle,
    verify_workspace_bundle,
)


def test_bundle_roundtrip(tmp_path):
    bundle = tmp_path / "effilife.efl"
    datasets = {
        "plans": {"head": {"index": 1}, "main": [], "log": []},
        "todos": [{"id": "todo-1", "status": "pending"}],
    }

    export_bundle(bundle, datasets, metadata={"app_version": "dev"})
    manifest = inspect_bundle(bundle)
    loaded_manifest, loaded = read_bundle(bundle)

    assert manifest["format"] == "effilife.bundle"
    assert loaded_manifest["datasets"] == ["plans", "todos"]
    assert loaded == datasets

    destination = tmp_path / "imported"
    written = import_bundle(bundle, destination)
    assert set(written) == {"plans", "todos"}
    assert json.loads((destination / "plans.json").read_text(encoding="utf-8")) == datasets["plans"]


def test_workspace_bundle_matches_unified_frontend_dataset_contract(tmp_path):
    bundle = tmp_path / "workspace.efl"
    export_workspace_bundle(
        bundle,
        app={"version": "2.1"},
        records={"2026-09-28": []},
        todos=[],
        todo_categories=[],
        plan_helper={"available": False, "plans": []},
    )
    manifest, datasets = read_workspace_bundle(bundle)
    assert manifest["format"] == "effilife.bundle"
    assert manifest["datasets"] == sorted(CANONICAL_WORKSPACE_DATASETS)
    assert set(datasets) == set(CANONICAL_WORKSPACE_DATASETS)


def test_workspace_bundle_roundtrip_preserves_cross_module_links(tmp_path):
    bundle = tmp_path / "linked-workspace.efl"
    records = {
        "2026-10-01": [{"id": "record-1", "todo_id": "todo-1", "plan_task_id": "A1"}],
    }
    todos = [{"id": "todo-1", "related_time_record_ids": ["record-1"], "plan_task_id": "A1"}]
    plan_helper = {
        "available": True,
        "plans": [{"id": "plan-1", "tasks": [{"id": "A1", "title": "Release"}]}],
    }

    export_workspace_bundle(
        bundle,
        app={"version": "e2e"},
        records=records,
        todos=todos,
        todo_categories=[{"id": "work", "name": "Work"}],
        plan_helper=plan_helper,
    )

    _manifest, datasets = read_workspace_bundle(bundle)

    assert datasets["records"] == records
    assert datasets["todos"] == todos
    assert datasets["plan_helper"] == plan_helper


def test_workspace_bundle_rejects_noncanonical_partial_data(tmp_path):
    bundle = tmp_path / "partial.efl"
    export_bundle(bundle, {"app": {}})
    with pytest.raises(ValueError, match="missing datasets"):
        read_workspace_bundle(bundle)


def test_workspace_export_rejects_invalid_shapes_before_writing(tmp_path):
    bundle = tmp_path / "invalid-export.efl"

    with pytest.raises(ValueError, match="invalid shape: app"):
        export_workspace_bundle(
            bundle,
            app=[],
            records={},
            todos=[],
            todo_categories=[],
            plan_helper={"plans": []},
        )

    assert not bundle.exists()


def test_workspace_bundle_rejects_invalid_core_dataset_shapes(tmp_path):
    bundle = tmp_path / "invalid-shapes.efl"
    export_bundle(bundle, {
        "app": [],
        "records": {},
        "todos": [],
        "todo_categories": [],
        "plan_helper": {"plans": []},
    })

    with pytest.raises(ValueError, match="invalid shape: app"):
        read_workspace_bundle(bundle)


def test_workspace_bundle_rejects_invalid_record_bucket_shape(tmp_path):
    bundle = tmp_path / "invalid-records.efl"
    export_bundle(bundle, {
        "app": {},
        "records": {"2026-09-29": {}},
        "todos": [],
        "todo_categories": [],
        "plan_helper": {"plans": []},
    })

    with pytest.raises(ValueError, match="2026-09-29"):
        read_workspace_bundle(bundle)


def test_workspace_bundle_rejects_invalid_plan_archive_shape(tmp_path):
    bundle = tmp_path / "invalid-plan-archives.efl"
    export_bundle(bundle, {
        "app": {},
        "records": {},
        "todos": [],
        "todo_categories": [],
        "plan_helper": {"plans": [], "archives": {}},
    })

    with pytest.raises(ValueError, match="plan_helper archives"):
        read_workspace_bundle(bundle)


def test_bundle_rejects_valid_json_dataset_tampering(tmp_path):
    bundle = tmp_path / "tampered.efl"
    export_bundle(bundle, {"app": {"version": "one"}})
    rewritten = tmp_path / "rewritten.efl"
    with zipfile.ZipFile(bundle, "r") as source, zipfile.ZipFile(rewritten, "w") as target:
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename == "data/app.json":
                content = b'{"version": "two"}'
            target.writestr(item, content)
    with pytest.raises(ValueError, match="checksum mismatch"):
        read_bundle(rewritten)


def test_workspace_bundle_verification_report_is_read_only(tmp_path):
    bundle = tmp_path / "workspace.efl"
    export_workspace_bundle(
        bundle,
        app={"version": "dev"},
        records={"2026-09-28": []},
        todos=[{"id": "TODO-1"}],
        todo_categories=[],
        plan_helper={"plans": []},
    )

    report = verify_workspace_bundle(bundle)

    assert report["integrity"] == "verified"
    assert report["datasets"] == sorted(CANONICAL_WORKSPACE_DATASETS)
    assert report["top_level_counts"]["todos"] == 1


def test_bundle_rejects_missing_manifest(tmp_path):
    bundle = tmp_path / "invalid.efl"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("data/plans.json", "{}")

    with pytest.raises(ValueError, match="manifest"):
        inspect_bundle(bundle)


def test_bundle_rejects_oversized_dataset_before_json_import(tmp_path):
    from common.data_exchange import MAX_DATASET_BYTES

    bundle = tmp_path / "oversized.efl"
    payload = b"x" * (MAX_DATASET_BYTES + 1)
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "1.0.0",
            "datasets": ["app"],
        }))
        archive.writestr("data/app.json", payload)
    with pytest.raises(ValueError, match="maximum supported size"):
        inspect_bundle(bundle)


def test_bundle_rejects_too_many_declared_datasets(tmp_path):
    from common.data_exchange import MAX_DATASET_COUNT

    bundle = tmp_path / "many-datasets.efl"
    names = [f"dataset-{index}" for index in range(MAX_DATASET_COUNT + 1)]
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "1.0.0",
            "datasets": names,
        }))
        for name in names:
            archive.writestr(f"data/{name}.json", "{}")
    with pytest.raises(ValueError, match="too many datasets"):
        inspect_bundle(bundle)


def test_bundle_rejects_unsupported_version(tmp_path):
    bundle = tmp_path / "future.efl"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "9.0.0",
            "datasets": [],
        }))

    with pytest.raises(ValueError, match="version"):
        inspect_bundle(bundle)


def test_bundle_does_not_overwrite_by_default(tmp_path):
    bundle = tmp_path / "effilife.efl"
    export_bundle(bundle, {"plans": []})
    destination = tmp_path / "imported"
    destination.mkdir()
    (destination / "plans.json").write_text("old", encoding="utf-8")

    with pytest.raises(FileExistsError):
        import_bundle(bundle, destination)


def test_bundle_import_preflights_all_targets_before_writing(tmp_path):
    bundle = tmp_path / "effilife.efl"
    export_bundle(bundle, {"first": {"value": 1}, "second": {"value": 2}})
    destination = tmp_path / "imported"
    destination.mkdir()
    (destination / "second.json").write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        import_bundle(bundle, destination)

    assert not (destination / "first.json").exists()
    assert (destination / "second.json").read_text(encoding="utf-8") == "existing"


def test_bundle_import_overwrite_uses_staging_and_cleans_up(tmp_path):
    bundle = tmp_path / "effilife.efl"
    export_bundle(bundle, {"first": {"value": 1}, "second": {"value": 2}})
    destination = tmp_path / "imported"
    destination.mkdir()
    (destination / "first.json").write_text("old", encoding="utf-8")
    import_bundle(bundle, destination, overwrite=True)

    assert json.loads((destination / "first.json").read_text(encoding="utf-8")) == {"value": 1}
    assert json.loads((destination / "second.json").read_text(encoding="utf-8")) == {"value": 2}
    assert not any(path.name.startswith(".effilife-import-") for path in destination.iterdir())


def test_bundle_import_rolls_back_when_install_fails(tmp_path):
    bundle = tmp_path / "effilife.efl"
    export_bundle(bundle, {"first": {"value": "new-1"}, "second": {"value": "new-2"}})
    destination = tmp_path / "imported"
    destination.mkdir()
    (destination / "first.json").write_text("old-1", encoding="utf-8")
    (destination / "second.json").write_text("old-2", encoding="utf-8")

    original_replace = __import__("common.data_exchange", fromlist=["os"]).os.replace
    calls = {"count": 0}

    def fail_on_second_install(source, target):
        source_path = str(source)
        if ".effilife-import-backup-" not in source_path and source_path.startswith(str(destination / ".effilife-import-")) and str(target).startswith(str(destination)):
            calls["count"] += 1
            if calls["count"] == 2:
                raise OSError("simulated install failure")
        return original_replace(source, target)

    with patch("common.data_exchange.os.replace", side_effect=fail_on_second_install):
        with pytest.raises(OSError, match="simulated install failure"):
            import_bundle(bundle, destination, overwrite=True)

    assert (destination / "first.json").read_text(encoding="utf-8") == "old-1"
    assert (destination / "second.json").read_text(encoding="utf-8") == "old-2"
    assert not any(path.name.startswith(".effilife-import-") for path in destination.iterdir())


def test_bundle_limits_are_exposed_for_cross_runtime_import_guards():
    from common.data_exchange import (
        MAX_ARCHIVE_ENTRIES,
        MAX_BUNDLE_BYTES,
        MAX_DATASET_BYTES,
        MAX_DATASET_COUNT,
        MAX_TOTAL_DATASET_BYTES,
    )

    assert MAX_BUNDLE_BYTES == 64 * 1024 * 1024
    assert MAX_DATASET_BYTES == 32 * 1024 * 1024
    assert MAX_TOTAL_DATASET_BYTES == 64 * 1024 * 1024
    assert MAX_DATASET_COUNT == 16
    assert MAX_ARCHIVE_ENTRIES == 64


def test_bundle_rejects_oversized_dataset_before_json_import(tmp_path):
    from common.data_exchange import MAX_DATASET_BYTES

    bundle = tmp_path / "oversized.efl"
    payload = b"x" * (MAX_DATASET_BYTES + 1)
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "1.0.0",
            "datasets": ["app"],
        }))
        archive.writestr("data/app.json", payload)
    with pytest.raises(ValueError, match="maximum supported size"):
        inspect_bundle(bundle)


def test_bundle_rejects_too_many_declared_datasets(tmp_path):
    from common.data_exchange import MAX_DATASET_COUNT

    bundle = tmp_path / "many-datasets.efl"
    names = [f"dataset-{index}" for index in range(MAX_DATASET_COUNT + 1)]
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "1.0.0",
            "datasets": names,
        }))
        for name in names:
            archive.writestr(f"data/{name}.json", "{}")
    with pytest.raises(ValueError, match="too many datasets"):
        inspect_bundle(bundle)


def test_bundle_rejects_too_many_zip_entries(tmp_path):
    from common.data_exchange import MAX_ARCHIVE_ENTRIES

    bundle = tmp_path / "many-entries.efl"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "format": "effilife.bundle",
            "format_version": "1.0.0",
            "datasets": ["app"],
        }))
        for index in range(MAX_ARCHIVE_ENTRIES):
            archive.writestr(f"extra/{index}.txt", "x")
    with pytest.raises(ValueError, match="too many archive entries"):
        inspect_bundle(bundle)
