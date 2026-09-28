import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_checksums.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("efflife_checksums", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_checksums_writes_sha256_and_relative_names(tmp_path):
    generator = load_generator()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "EffiLife-test.exe"
    artifact.write_bytes(b"release artifact")
    nested = bundle / "nested"
    nested.mkdir()
    second = nested / "payload.bin"
    second.write_bytes(b"sidecar")
    output = tmp_path / "checksums" / "test.sha256"

    files = generator.generate(bundle, output)

    assert files == [artifact, second]
    lines = output.read_text(encoding="utf-8").splitlines()
    assert lines == [
        f"{hashlib.sha256(artifact.read_bytes()).hexdigest()}  EffiLife-test.exe",
        f"{hashlib.sha256(second.read_bytes()).hexdigest()}  nested/payload.bin",
    ]


def test_release_workflow_uploads_checksum_next_to_each_installer():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")
    assert "scripts/generate_checksums.py" in workflow
    assert "release-checksums/EffiLife-${{ matrix.name }}.sha256" in workflow
    assert "${{ matrix.artifact }}" in workflow
