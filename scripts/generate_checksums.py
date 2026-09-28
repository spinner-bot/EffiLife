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


def generate(directory: Path, output: Path) -> list[Path]:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path != output)
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
    args = parser.parse_args()
    generate(args.directory, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
