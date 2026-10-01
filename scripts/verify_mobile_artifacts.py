#!/usr/bin/env python3
"""Verify that a Tauri mobile build produced non-empty platform artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path


def _non_empty_file(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def find_artifacts(directory: Path, target: str) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f"Mobile artifact directory does not exist: {directory}")

    if target == "android":
        return sorted(path for path in directory.rglob("*.apk") if _non_empty_file(path))

    # Xcode produces an .app bundle directory; some CI configurations also
    # export an .ipa file. Accept either, but require actual non-empty content.
    artifacts: list[Path] = [
        path for path in directory.rglob("*.ipa") if _non_empty_file(path)
    ]
    for bundle in directory.rglob("*.app"):
        if bundle.is_dir() and any(_non_empty_file(path) for path in bundle.rglob("*")):
            artifacts.append(bundle)
    return sorted(set(artifacts))


def verify(directory: Path, target: str) -> list[Path]:
    artifacts = find_artifacts(directory, target)
    if not artifacts:
        raise FileNotFoundError(f"No non-empty {target} mobile artifact found in {directory}")
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--target", required=True, choices=("android", "ios"))
    args = parser.parse_args()
    try:
        artifacts = verify(args.directory, args.target)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for artifact in artifacts:
        print(f"OK: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
