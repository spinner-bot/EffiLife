"""Report whether the local toolchain can build EffiLife for a target platform."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CUSTOM_RUST_TOOLCHAIN_DIR = Path("F:/dev-tools/rustup/toolchains/stable-x86_64-pc-windows-msvc/bin")
CUSTOM_ANDROID_SDK_DIR = Path("F:/dev-tools/android-sdk")

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
    if name in {"cargo", "rustc"}:
        configured = os.environ.get("EFFILIFE_RUST_TOOLCHAIN_DIR", "").strip()
        toolchain_dir = Path(configured).expanduser() if configured else (
            CUSTOM_RUST_TOOLCHAIN_DIR if os.name == "nt" else None
        )
        if toolchain_dir is not None:
            candidate = toolchain_dir / (f"{name}.exe" if os.name == "nt" else name)
            if candidate.is_file():
                return str(candidate)
    if name == "adb":
        configured = os.environ.get("ANDROID_HOME", "").strip() or os.environ.get("ANDROID_SDK_ROOT", "").strip()
        sdk_dir = Path(configured).expanduser() if configured else (
            CUSTOM_ANDROID_SDK_DIR if os.name == "nt" else None
        )
        if sdk_dir is not None:
            candidate = sdk_dir / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
            if candidate.is_file():
                return str(candidate)
    return shutil.which(name) or (shutil.which(f"{name}.exe") if os.name == "nt" else None)


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


def required_android_components(sdk_root: Path, mobile_project: Path | None) -> list[str]:
    """Return missing SDK components declared by the generated Android project."""
    if mobile_project is None:
        return []
    gradle_file = mobile_project / "app" / "build.gradle.kts"
    if not gradle_file.is_file():
        return []
    try:
        source = gradle_file.read_text(encoding="utf-8")
    except OSError:
        return [f"Android project configuration: {gradle_file}"]

    missing: list[str] = []
    compile_sdk = re.search(r"compileSdk\s*=\s*(\d+)", source)
    if compile_sdk:
        platform = sdk_root / "platforms" / f"android-{compile_sdk.group(1)}"
        if not platform.is_dir():
            missing.append(f"Android platform: {platform}")
    return missing


def build_report(target: str, root: Path | None = None) -> dict[str, object]:
    requirements = TARGET_REQUIREMENTS[target]
    tools = {
        name: node_tool_path(name) if name in {"node", "npm"} else executable_path(name)
        for name in requirements
    }
    configured_sdk = os.environ.get("ANDROID_HOME", "").strip() or os.environ.get("ANDROID_SDK_ROOT", "").strip()
    managed_sdk = CUSTOM_ANDROID_SDK_DIR if os.name == "nt" and CUSTOM_ANDROID_SDK_DIR.is_dir() else None
    resolved_sdk = configured_sdk or (str(managed_sdk) if managed_sdk else None)
    sdk_roots = {
        "ANDROID_HOME": resolved_sdk,
        "ANDROID_SDK_ROOT": resolved_sdk,
    }
    missing = [name for name, path in tools.items() if not path]
    if target == "android":
        if not resolved_sdk:
            missing.append("ANDROID_HOME or ANDROID_SDK_ROOT")
        elif not Path(resolved_sdk).is_dir():
            missing.append(f"Android SDK directory: {resolved_sdk}")
    mobile_project = None
    if target in MOBILE_PROJECTS:
        mobile_project = (root or ROOT) / MOBILE_PROJECTS[target]
        if not mobile_project.is_dir():
            missing.append(f"Tauri {target} project (run tauri {target} init)")
        elif target == "android" and resolved_sdk:
            missing.extend(required_android_components(Path(resolved_sdk), mobile_project))
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
