import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_desktop_release_versions_are_aligned():
    package = json.loads((ROOT / "time-helper" / "desk" / "package.json").read_text(encoding="utf-8"))
    tauri = json.loads((ROOT / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    cargo_text = (ROOT / "time-helper" / "desk" / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    cargo_version = re.search(r'^version\s*=\s*"([^"]+)"', cargo_text, re.MULTILINE)

    assert cargo_version is not None
    assert package["version"] == tauri["version"] == cargo_version.group(1)


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
    tauri_step = workflow.index("npm run tauri build")
    assert sidecar_dependency_step < tauri_step
