"""Report whether the local toolchain can build EffiLife for a target platform."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


TARGET_REQUIREMENTS = {
    "desktop": ("node", "npm", "cargo", "rustc"),
    "android": ("node", "npm", "cargo", "rustc", "java", "adb"),
    "ios": ("node", "npm", "cargo", "rustc", "xcodebuild"),
}


def executable_path(name: str) -> str | None:
    return shutil.which(name)


def build_report(target: str) -> dict[str, object]:
    requirements = TARGET_REQUIREMENTS[target]
    tools = {name: executable_path(name) for name in requirements}
    sdk_roots = {
        "ANDROID_HOME": os.environ.get("ANDROID_HOME"),
        "ANDROID_SDK_ROOT": os.environ.get("ANDROID_SDK_ROOT"),
    }
    missing = [name for name, path in tools.items() if not path]
    if target == "android" and not any(sdk_roots.values()):
        missing.append("ANDROID_HOME or ANDROID_SDK_ROOT")
    return {
        "target": target,
        "ready": not missing,
        "tools": tools,
        "sdk_roots": sdk_roots,
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
