import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_release_manifest.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("effilife_manifest_verifier", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_verifier_checks_bytes_and_hashes(tmp_path):
    verifier = load_verifier()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "release.apk"
    artifact.write_bytes(b"apk")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "schema": "effilife.release-manifest.v1",
        "product": "EffiLife",
        "version": "1.7.0",
        "target": "android",
        "artifacts": [{
            "path": "release.apk",
            "bytes": 3,
            "sha256": hashlib.sha256(b"apk").hexdigest(),
        }],
    }), encoding="utf-8")
    version = tmp_path / "VERSION"
    version.write_text("1.7.0\n", encoding="utf-8")

    assert verifier.verify(manifest, bundle, "1.7.0", "android")["target"] == "android"


def test_manifest_verifier_rejects_tampering_and_unsafe_paths(tmp_path):
    verifier = load_verifier()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "release.apk").write_bytes(b"changed")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "schema": "effilife.release-manifest.v1",
        "product": "EffiLife",
        "version": "1.7.0",
        "target": "android",
        "artifacts": [{"path": "../outside.apk", "bytes": 1, "sha256": "x"}],
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="unsafe path"):
        verifier.verify(manifest, bundle, "1.7.0", "android")
