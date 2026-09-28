import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_desktop_release_versions_are_aligned():
    source_version = (ROOT / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    package = json.loads((ROOT / "time-helper" / "desk" / "package.json").read_text(encoding="utf-8"))
    tauri = json.loads((ROOT / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    cargo_text = (ROOT / "time-helper" / "desk" / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    cargo_version = re.search(r'^version\s*=\s*"([^"]+)"', cargo_text, re.MULTILINE)

    assert cargo_version is not None
    assert source_version == package["version"] == tauri["version"] == cargo_version.group(1)


def test_windows_workflow_matches_configured_bundle_target():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")
    tauri = json.loads((ROOT / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))

    assert "nsis" in tauri["bundle"]["targets"]
    assert "bundle/nsis/*.exe" in workflow
    assert "bundle/msi/*.msi" not in workflow


def test_desktop_workflow_covers_all_release_platforms():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")

    for runner, bundle, artifact in (
        ("windows-latest", "nsis", "bundle/nsis/*.exe"),
        ("ubuntu-22.04", "deb", "bundle/deb/*.deb"),
        ("macos-latest", "dmg", "bundle/dmg/*.dmg"),
    ):
        assert runner in workflow
        assert f"bundle: {bundle}" in workflow
        assert artifact in workflow


def test_desktop_workflow_installs_sidecar_builder_before_tauri():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")

    sidecar_dependency_step = workflow.index("python -m pip install pyinstaller")
    test_step = workflow.index("python -m pytest -q")
    tauri_step = workflow.index("npm run tauri build")
    assert sidecar_dependency_step < tauri_step
    assert sidecar_dependency_step < test_step < tauri_step


def test_release_workflow_syncs_repository_version_before_contract_tests():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")
    assert "python scripts/sync_desktop_version.py" in workflow
    assert workflow.index("python scripts/sync_desktop_version.py") < workflow.index("python -m pytest -q")


def test_release_version_sync_script_updates_all_desktop_manifests(tmp_path):
    import json
    import subprocess

    root = tmp_path / "repo"
    (root / "time-helper" / "desk" / "src-tauri").mkdir(parents=True)
    (root / "time-helper").mkdir(exist_ok=True)
    (root / "time-helper" / "VERSION").write_text("9.8.7\n", encoding="utf-8")
    (root / "time-helper" / "desk" / "package.json").write_text('{"name":"test","version":"0.0.1"}\n', encoding="utf-8")
    (root / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").write_text('{"version":"0.0.1"}\n', encoding="utf-8")
    (root / "time-helper" / "desk" / "src-tauri" / "Cargo.toml").write_text('[package]\nversion = "0.0.1"\n', encoding="utf-8")
    script = ROOT / "scripts" / "sync_desktop_version.py"
    subprocess.run(["python", str(script), "--root", str(root)], check=True)
    assert json.loads((root / "time-helper" / "desk" / "package.json").read_text(encoding="utf-8"))["version"] == "9.8.7"
    assert json.loads((root / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))["version"] == "9.8.7"
    assert 'version = "9.8.7"' in (root / "time-helper" / "desk" / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")


def test_release_preflight_passes_for_current_repository():
    import importlib.util

    script = ROOT / "scripts" / "check_release_config.py"
    spec = importlib.util.spec_from_file_location("effilife_release_preflight", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.validate(ROOT) == []


def test_release_workflow_passes_matrix_bundle_to_tauri():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")
    assert "npm run tauri build -- --bundles ${{ matrix.bundle }}" in workflow


def test_release_workflow_verifies_non_empty_platform_installer():
    workflow = (ROOT / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")
    assert "scripts/verify_release_artifacts.py" in workflow
    assert "extension: .exe" in workflow
    assert "extension: .deb" in workflow
    assert "extension: .dmg" in workflow
