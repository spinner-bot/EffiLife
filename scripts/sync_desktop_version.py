"""Synchronize desktop release metadata from the repository VERSION file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def sync(root: Path) -> str:
    version = (root / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"invalid release version: {version!r}")

    package_path = root / "time-helper" / "desk" / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["version"] = version
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Keep npm's lock metadata aligned as well. This is intentionally handled
    # here instead of invoking npm: release runners already install from the
    # committed lockfile before synchronization, and a version-only update
    # must not rewrite dependency resolution or integrity data.
    lock_path = package_path.with_name("package-lock.json")
    if lock_path.exists():
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["version"] = version
        root_package = lock.get("packages", {}).get("")
        if isinstance(root_package, dict):
            root_package["version"] = version
        lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tauri_path = root / "time-helper" / "desk" / "src-tauri" / "tauri.conf.json"
    tauri = json.loads(tauri_path.read_text(encoding="utf-8"))
    tauri["version"] = version
    tauri_path.write_text(json.dumps(tauri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cargo_path = root / "time-helper" / "desk" / "src-tauri" / "Cargo.toml"
    cargo_text = cargo_path.read_text(encoding="utf-8")
    updated, count = re.subn(r'(?m)^(version\s*=\s*)"[^"]+"', rf'\1"{version}"', cargo_text, count=1)
    if count != 1:
        raise ValueError("Cargo.toml package version was not found")
    cargo_path.write_text(updated, encoding="utf-8")
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(f"Synchronized desktop release metadata to {sync(args.root.resolve())}")


if __name__ == "__main__":
    main()
