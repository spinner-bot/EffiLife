#!/usr/bin/env python3
"""Build the Plan Helper HTTP service as a Tauri sidecar binary."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "plan-helper" / "web" / "server.py"
DESK_TAURI = ROOT / "time-helper" / "desk" / "src-tauri"
BUILD_ROOT = DESK_TAURI / "target" / "sidecar-build"
BINARIES_DIR = DESK_TAURI / "binaries"


def target_triple(explicit: str | None) -> str:
    if explicit:
        return explicit
    configured = os.environ.get("TAURI_TARGET_TRIPLE")
    if configured:
        return configured
    try:
        result = subprocess.run(
            ["rustc", "-vV"],
            check=True,
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("host:"):
                return line.split(":", 1)[1].strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    machine = platform.machine().lower()
    if os.name == "nt":
        return "aarch64-pc-windows-msvc" if machine in {"arm64", "aarch64"} else "x86_64-pc-windows-msvc"
    if sys.platform == "darwin":
        return "aarch64-apple-darwin" if machine in {"arm64", "aarch64"} else "x86_64-apple-darwin"
    return "aarch64-unknown-linux-gnu" if machine in {"arm64", "aarch64"} else "x86_64-unknown-linux-gnu"


def output_path(triple: str) -> Path:
    suffix = ".exe" if triple.endswith("windows-msvc") or triple.endswith("windows-gnu") else ""
    return BINARIES_DIR / f"efflife-plan-helper-{triple}{suffix}"


def is_non_empty_file(path: Path) -> bool:
    """Return whether a generated sidecar is a usable regular file."""
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def install_sidecar(generated: Path, destination: Path) -> None:
    """Install a generated sidecar without exposing a partial destination.

    Tauri may be running the previous sidecar during a development rebuild.
    Windows cannot replace an executable that is still open, so turn that
    low-level error into an actionable message instead of leaving a truncated
    or half-copied binary at the bundle path.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        shutil.copy2(generated, temporary)
        os.replace(temporary, destination)
    except PermissionError as error:
        raise RuntimeError(
            f"Cannot replace sidecar {destination}; close the running EffiLife "
            "or Plan Helper process and retry the build."
        ) from error
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def build(triple: str, dry_run: bool = False) -> Path:
    if not SERVER.exists():
        raise FileNotFoundError(f"Plan Helper server not found: {SERVER}")

    destination = output_path(triple)
    dist_dir = BUILD_ROOT / "dist"
    work_dir = BUILD_ROOT / "work"
    spec_dir = BUILD_ROOT / "spec"
    executable = "efflife-plan-helper.exe" if destination.suffix == ".exe" else "efflife-plan-helper"
    generated = dist_dir / executable
    add_data_separator = os.pathsep
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "efflife-plan-helper",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        "--paths",
        str(ROOT / "plan-helper"),
        "--add-data",
        f"{ROOT / 'plan-helper' / 'web'}{add_data_separator}web",
        str(SERVER),
    ]

    print(f"Target: {triple}")
    print(f"Output: {destination}")
    if dry_run:
        print("Command:", " ".join(command))
        return destination

    subprocess.run(command, cwd=ROOT, check=True)
    if not is_non_empty_file(generated):
        raise FileNotFoundError(f"PyInstaller output is missing or empty: {generated}")
    install_sidecar(generated, destination)
    if not is_non_empty_file(destination):
        raise FileNotFoundError(f"Sidecar copy is missing or empty: {destination}")
    print(f"Sidecar ready: {destination}")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="Tauri target triple")
    parser.add_argument("--dry-run", action="store_true", help="Print the build plan without building")
    args = parser.parse_args()
    build(target_triple(args.target), dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
