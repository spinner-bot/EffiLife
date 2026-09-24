import json
import zipfile

import pytest

from common.data_exchange import export_bundle, import_bundle, inspect_bundle, read_bundle


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


def test_bundle_rejects_missing_manifest(tmp_path):
    bundle = tmp_path / "invalid.efl"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("data/plans.json", "{}")

    with pytest.raises(ValueError, match="manifest"):
        inspect_bundle(bundle)


def test_bundle_does_not_overwrite_by_default(tmp_path):
    bundle = tmp_path / "effilife.efl"
    export_bundle(bundle, {"plans": []})
    destination = tmp_path / "imported"
    destination.mkdir()
    (destination / "plans.json").write_text("old", encoding="utf-8")

    with pytest.raises(FileExistsError):
        import_bundle(bundle, destination)
