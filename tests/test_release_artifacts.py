import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_release_artifacts.py"


@pytest.fixture()
def verifier():
    spec = importlib.util.spec_from_file_location("effilife_release_artifacts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_verifier_accepts_non_empty_expected_artifact(tmp_path, verifier):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "EffiLife.exe"
    artifact.write_bytes(b"installer")
    assert verifier.verify(bundle, ".exe") == [artifact]


def test_verifier_rejects_missing_or_empty_artifact(tmp_path, verifier):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "empty.exe").write_bytes(b"")
    with pytest.raises(FileNotFoundError):
        verifier.verify(bundle, ".exe")
