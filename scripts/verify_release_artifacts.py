#!/usr/bin/env python3
"""Verify that a Tauri bundle produced the expected installer artifact."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def find_artifacts(directory: Path, extension: str) -> list[Path]:
    normalized = extension if extension.startswith('.') else f'.{extension}'
    return sorted(
        path for path in directory.rglob(f'*{normalized}')
        if path.is_file() and path.stat().st_size > 0
    )


def artifact_version(path: Path) -> str | None:
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)(?!\d)", path.name)
    return match.group(1) if match else None


def verify(directory: Path, extension: str, expected_version: str | None = None) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f'Bundle directory does not exist: {directory}')
    artifacts = find_artifacts(directory, extension)
    if not artifacts:
        raise FileNotFoundError(f'No non-empty {extension} installer found in {directory}')
    if expected_version:
        mismatched = [path for path in artifacts if artifact_version(path) != expected_version]
        if mismatched:
            names = ', '.join(path.name for path in mismatched)
            raise ValueError(f'Installer version mismatch: expected {expected_version}, got {names}')
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--extension', required=True, help='Expected installer extension, e.g. .exe')
    parser.add_argument('--version-file', type=Path, help='Read the expected semantic version from a repository file')
    args = parser.parse_args()
    try:
        expected_version = args.version_file.read_text(encoding='utf-8').strip() if args.version_file else None
        artifacts = verify(args.directory, args.extension, expected_version)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for artifact in artifacts:
        print(f'OK: {artifact} ({artifact.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
