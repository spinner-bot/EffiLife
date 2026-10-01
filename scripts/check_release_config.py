"""Validate the repository's desktop release configuration without building it."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    version = (root / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    package = json.loads((root / "time-helper" / "desk" / "package.json").read_text(encoding="utf-8"))
    tauri = json.loads((root / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    cargo = (root / "time-helper" / "desk" / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "tauri-desktop-release.yml").read_text(encoding="utf-8")

    cargo_match = re.search(r'^version\s*=\s*"([^"]+)"', cargo, re.MULTILINE)
    versions = {version, str(package.get("version")), str(tauri.get("version")), cargo_match.group(1) if cargo_match else ""}
    if len(versions) != 1:
        errors.append(f"desktop versions are not aligned: {sorted(versions)}")
    if "binaries/efflife-plan-helper" not in tauri.get("bundle", {}).get("externalBin", []):
        errors.append("Tauri config does not declare the Plan Helper sidecar")
    if "nsis" not in tauri.get("bundle", {}).get("targets", []):
        errors.append("Tauri config does not include the Windows NSIS target")
    for icon in tauri.get("bundle", {}).get("icon", []):
        if not (root / "time-helper" / "desk" / "src-tauri" / icon).exists():
            errors.append(f"Tauri bundle icon is missing: {icon}")
    if "build:sidecar" not in str(tauri.get("build", {}).get("beforeBuildCommand", "")):
        errors.append("Tauri release build does not build the Plan Helper sidecar")
    if "python -m pytest -q" not in workflow:
        errors.append("release workflow has no Python contract-test step")
    if "scripts/check_build_environment.py --target desktop" not in workflow:
        errors.append("release workflow has no desktop toolchain preflight step")
    if "to-dos/ui/package-lock.json" not in workflow or "working-directory: to-dos/ui" not in workflow or "run: npm run build" not in workflow:
        errors.append("release workflow has no to-dos compatibility UI build job")
    if "scripts/generate_checksums.py" not in workflow:
        errors.append("release workflow has no installer checksum step")
    if "scripts/generate_release_manifest.py" not in workflow or ".manifest.json" not in workflow:
        errors.append("release workflow has no machine-readable installer manifest step")
    if "npm run tauri build -- --bundles ${{ matrix.bundle }}" not in workflow:
        errors.append("release workflow does not pass the matrix bundle target to Tauri")
    if "scripts/verify_release_artifacts.py" not in workflow:
        errors.append("release workflow has no packaged installer artifact verification step")
    if "actions/download-artifact@v4" not in workflow or "gh release create" not in workflow:
        errors.append("release workflow has no tagged GitHub Release publication step")
    if "needs:" not in workflow or "compatibility" not in workflow or "build" not in workflow:
        errors.append("release publication does not wait for compatibility and desktop builds")
    if "release-assets" not in workflow or "find release-assets -type f -print" not in workflow:
        errors.append("tagged release publication does not include downloaded release metadata")
    for runner, bundle, extension, artifact in (
        ("windows-latest", "nsis", ".exe", "bundle/nsis/*.exe"),
        ("ubuntu-22.04", "deb", ".deb", "bundle/deb/*.deb"),
        ("ubuntu-22.04", "appimage", ".AppImage", "bundle/appimage/*.AppImage"),
        ("macos-latest", "dmg", ".dmg", "bundle/dmg/*.dmg"),
    ):
        if (runner not in workflow or f"bundle: {bundle}" not in workflow
                or f"extension: {extension}" not in workflow or artifact not in workflow):
            errors.append(f"release matrix entry is incomplete: {runner}/{bundle}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("EffiLife desktop release configuration is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
