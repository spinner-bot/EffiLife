#!/usr/bin/env python3
"""Verify that a Tauri bundle produced the expected installer artifact."""

from __future__ import annotations

import argparse
from pathlib import Path


def find_artifacts(directory: Path, extension: str) -> list[Path]:
    normalized = extension if extension.startswith('.') else f'.{extension}'
    return sorted(
        path for path in directory.rglob(f'*{normalized}')
        if path.is_file() and path.stat().st_size > 0
    )


def verify(directory: Path, extension: str) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f'Bundle directory does not exist: {directory}')
    artifacts = find_artifacts(directory, extension)
    if not artifacts:
        raise FileNotFoundError(f'No non-empty {extension} installer found in {directory}')
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--extension', required=True, help='Expected installer extension, e.g. .exe')
    args = parser.parse_args()
    artifacts = verify(args.directory, args.extension)
    for artifact in artifacts:
        print(f'OK: {artifact} ({artifact.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
