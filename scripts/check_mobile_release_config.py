"""Validate the Tauri Mobile build boundary without requiring mobile SDKs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(root: Path) -> list[str]:
    desk = root / "time-helper" / "desk" / "src-tauri"
    desktop = json.loads((desk / "tauri.conf.json").read_text(encoding="utf-8"))
    mobile = json.loads((desk / "tauri.mobile.conf.json").read_text(encoding="utf-8"))
    version = (root / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    errors: list[str] = []

    desktop_external = desktop.get("bundle", {}).get("externalBin", [])
    if "binaries/efflife-plan-helper" not in desktop_external:
        errors.append("desktop configuration lost the Plan Helper sidecar")
    if mobile.get("build", {}).get("beforeBuildCommand") != "npm run build":
        errors.append("mobile configuration must build the frontend without a sidecar")
    if mobile.get("bundle", {}).get("externalBin") != []:
        errors.append("mobile configuration must not declare desktop externalBin entries")
    if "build:sidecar" in str(mobile.get("build", {}).get("beforeBuildCommand", "")):
        errors.append("mobile configuration must not invoke build:sidecar")
    for key in ("productName", "version", "identifier"):
        expected = version if key == "version" else desktop.get(key)
        if mobile.get(key) != expected:
            errors.append(f"mobile configuration {key} is not synchronized with the desktop release metadata")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
