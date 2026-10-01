#!/usr/bin/env python3
"""Generate deterministic SHA-256 checksums for release artifacts."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


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
    extensions: tuple[str, ...] = (),
    bundle_extensions: tuple[str, ...] = (),
) -> list[Path]:
    files = sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path != output and _is_selected(path, extensions, bundle_extensions)
    )
    if not files:
        raise FileNotFoundError(f"No release artifacts found in {directory}")

    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--extension", action="append", default=[], help="Include files with this extension")
    parser.add_argument("--bundle-extension", action="append", default=[], help="Include files inside bundles with this extension")
    args = parser.parse_args()
    extensions = tuple(value.lower() if value.startswith(".") else f".{value.lower()}" for value in args.extension)
    bundle_extensions = tuple(value.lower() if value.startswith(".") else f".{value.lower()}" for value in args.bundle_extension)
    generate(args.directory, args.output, extensions, bundle_extensions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
