#!/usr/bin/env python3
"""Verify an EffiLife release manifest against the files on disk."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "effilife.release-manifest.v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(manifest_path: Path, directory: Path, version: str, target: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unsupported release manifest schema")
    if manifest.get("product") != "EffiLife":
        raise ValueError("release manifest product is not EffiLife")
    if manifest.get("version") != version:
        raise ValueError(f"release manifest version mismatch: expected {version}")
    if manifest.get("target") != target:
        raise ValueError(f"release manifest target mismatch: expected {target}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("release manifest has no artifacts")
    root = directory.resolve()
    for entry in artifacts:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("release manifest contains an invalid artifact entry")
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"release manifest contains an unsafe path: {relative}")
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise FileNotFoundError(f"release manifest artifact is missing: {relative}")
        if entry.get("bytes") != path.stat().st_size:
            raise ValueError(f"release manifest byte count mismatch: {relative}")
        if entry.get("sha256") != sha256(path):
            raise ValueError(f"release manifest checksum mismatch: {relative}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--version-file", required=True, type=Path)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        verify(
            args.manifest,
            args.directory,
            args.version_file.read_text(encoding="utf-8").strip(),
            args.target,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(f"OK: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
