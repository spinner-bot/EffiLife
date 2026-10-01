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


def _is_selected(path: Path, extensions: tuple[str, ...], bundle_extensions: tuple[str, ...]) -> bool:
    if not extensions and not bundle_extensions:
        return True
    if path.suffix.lower() in extensions:
        return True
    return any(part.lower().endswith(bundle_extension) for part in path.parts for bundle_extension in bundle_extensions)


def generate(
    directory: Path,
    output: Path,
    version: str,
    target: str,
    extensions: tuple[str, ...] = (),
    bundle_extensions: tuple[str, ...] = (),
) -> dict:
    if not directory.is_dir():
        raise FileNotFoundError(f"Release directory does not exist: {directory}")
    files = sorted(
        path for path in directory.rglob("*")
        if path.is_file() and _is_selected(path, extensions, bundle_extensions)
    )
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
    parser.add_argument("--extension", action="append", default=[], help="Include files with this extension")
    parser.add_argument("--bundle-extension", action="append", default=[], help="Include files inside bundles with this extension")
    args = parser.parse_args()
    extensions = tuple(value.lower() if value.startswith(".") else f".{value.lower()}" for value in args.extension)
    bundle_extensions = tuple(value.lower() if value.startswith(".") else f".{value.lower()}" for value in args.bundle_extension)
    generate(args.directory, args.output, args.version_file.read_text(encoding="utf-8").strip(), args.target, extensions, bundle_extensions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
