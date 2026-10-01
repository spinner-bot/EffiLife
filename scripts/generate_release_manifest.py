#!/usr/bin/env python3
"""Generate a machine-readable manifest for one EffiLife release target."""

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


def generate(directory: Path, output: Path, version: str, target: str) -> dict:
    if not directory.is_dir():
        raise FileNotFoundError(f"Release directory does not exist: {directory}")
    files = sorted(path for path in directory.rglob("*") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No release artifacts found in {directory}")

    manifest = {
        "schema": SCHEMA,
        "product": "EffiLife",
        "version": version,
        "target": target,
        "artifacts": [
            {
                "path": path.relative_to(directory).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version-file", required=True, type=Path)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    generate(args.directory, args.output, args.version_file.read_text(encoding="utf-8").strip(), args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
