"""Report whether the local toolchain can build EffiLife for a target platform."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET_REQUIREMENTS = {
    "desktop": ("node", "npm", "cargo", "rustc"),
    "android": ("node", "npm", "cargo", "rustc", "java", "adb"),
    "ios": ("node", "npm", "cargo", "rustc", "xcodebuild"),
}

MOBILE_PROJECTS = {
    "android": Path("time-helper/desk/src-tauri/gen/android"),
    # Tauri calls the shared Apple native project `gen/apple` for iOS.
    "ios": Path("time-helper/desk/src-tauri/gen/apple"),
}


def executable_path(name: str) -> str | None:
    return shutil.which(name)


def node_tool_path(name: str) -> str | None:
    """Find Node/npm using the same custom-tool directory as the launcher."""
    configured = os.environ.get("EFFILIFE_NODE_DIR", "").strip()
    if configured:
        custom_dir = Path(configured).expanduser()
    elif os.name == "nt":
        custom_dir = Path("F:/dev-tools/node")
    else:
        custom_dir = None

    if custom_dir is not None:
        if os.name == "nt":
            filename = f"{name}.cmd" if name == "npm" else f"{name}.exe"
        else:
            filename = name
        candidate = custom_dir / filename
        if candidate.is_file():
            return str(candidate)
    return executable_path(name)


def build_report(target: str, root: Path | None = None) -> dict[str, object]:
    requirements = TARGET_REQUIREMENTS[target]
    tools = {
        name: node_tool_path(name) if name in {"node", "npm"} else executable_path(name)
        for name in requirements
    }
    sdk_roots = {
        "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
        "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
    }
    missing = [name for name, path in tools.items() if not path]
    if target == "android":
        sdk_candidates = [Path(value).expanduser() for value in sdk_roots.values() if value]
        if not sdk_candidates:
            missing.append("ANDROID_HOME or ANDROID_SDK_ROOT")
        elif not any(candidate.is_dir() for candidate in sdk_candidates):
            missing.append("Android SDK directory")
    mobile_project = None
    if target in MOBILE_PROJECTS:
        mobile_project = (root or ROOT) / MOBILE_PROJECTS[target]
        if not mobile_project.is_dir():
            missing.append(f"Tauri {target} project (run tauri {target} init)")
    return {
        "target": target,
        "ready": not missing,
        "tools": tools,
        "sdk_roots": sdk_roots,
        "mobile_project": str(mobile_project) if mobile_project else None,
        "mobile_project_exists": mobile_project.is_dir() if mobile_project else None,
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("desktop", "android", "ios", "all"), default="desktop")
    args = parser.parse_args()
    targets = tuple(TARGET_REQUIREMENTS) if args.target == "all" else (args.target,)
    reports = [build_report(target) for target in targets]
    print(json.dumps(reports[0] if len(reports) == 1 else {"targets": reports}, ensure_ascii=True, indent=2))
    return 0 if all(report["ready"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
