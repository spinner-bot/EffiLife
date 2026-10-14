"""Run a bounded Windows NSIS install/uninstall smoke test in an isolated directory.

The script deliberately refuses to operate on an existing target by default.
It is intended for release validation, not for managing a user's installation.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path


EXPECTED_FILES = (
    "efflife-desk.exe",
    "efflife-plan-helper.exe",
    "uninstall.exe",
)
# Accept the current product name and the historical Chinese product name so
# a real pre-rebrand installer can be used as the previous upgrade endpoint.
# The version capture remains mandatory; this does not weaken version checks.
# Keep the historical brand explicit; this file is also used by upgrade smoke
# tests against installers produced before the rebrand.
INSTALLER_VERSION_PATTERN = re.compile(r"^(?:EffiLife|\u6d6a\u516e\u6548\u7387\u65f6\u949f)_(?P<version>[^_]+)_x64-setup\.exe$", re.IGNORECASE)
# Historical pre-rebrand builds used the repository's published desk label
# instead of the Tauri NSIS suffix. Keep this as a second explicit convention.
INSTALLER_VERSION_PATTERN = re.compile(
    r"^(?:EffiLife|\u6d6a\u516e\u6548\u7387\u65f6\u949f)_(?P<version>[^_（]+)(?:_x64-setup|（desk_发布版）)\.exe$",
    re.IGNORECASE,
)
INSTALLER_VERSION_PATTERN = re.compile(r"^(?:EffiLife|浪兮效率时钟)_(?P<version>[^_]+)_x64-setup\.exe$", re.IGNORECASE)


INSTALLER_VERSION_PATTERN = re.compile(
    r"^(?:EffiLife|\u6d6a\u516e\u6548\u7387\u65f6\u949f)_(?P<version>[^_\uff08]+)(?:_x64-setup|\uff08desk_\u53d1\u5e03\u7248\uff09)\.exe$",
    re.IGNORECASE,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", type=Path, required=True, help="Path to the NSIS installer")
    parser.add_argument("--target", type=Path, required=True, help="New isolated installation directory")
    parser.add_argument("--version-file", type=Path, help="Optional file containing the expected installer version")
    parser.add_argument("--timeout", type=float, default=90.0, help="Timeout per installer process")
    return parser


def _ensure_safe_target(target: Path) -> Path:
    resolved = target.expanduser().resolve()
    if resolved == resolved.anchor or len(resolved.parts) < 3:
        raise ValueError("Refusing to use a filesystem root or broad directory as the smoke-test target")
    if resolved.exists():
        raise FileExistsError(f"Smoke-test target already exists: {resolved}")
    return resolved


def _run(command: list[str], timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def _wait_removed(path: Path, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not path.exists():
            return True
        time.sleep(0.25)
    return not path.exists()


def run_smoke(installer: Path, target: Path, timeout: float, version_file: Path | None = None) -> dict[str, object]:
    if os.name != "nt":
        raise RuntimeError("Windows installer smoke test requires Windows")
    installer = installer.expanduser().resolve()
    if not installer.is_file():
        raise FileNotFoundError(f"Installer not found: {installer}")
    artifact_match = INSTALLER_VERSION_PATTERN.match(installer.name)
    if artifact_match is None:
        raise ValueError(f"Installer filename does not match a supported EffiLife NSIS convention: {installer.name}")
    artifact_version = artifact_match.group("version")
    if version_file is not None:
        expected_version = version_file.expanduser().resolve().read_text(encoding="utf-8").strip()
        if artifact_version != expected_version:
            raise ValueError(f"Installer version mismatch: expected {expected_version}, got {artifact_version}")
    target = _ensure_safe_target(target)

    install = _run([str(installer), "/S", f"/D={target}"], timeout)
    if install.returncode != 0:
        raise RuntimeError(f"Installer failed with exit code {install.returncode}: {install.stderr.strip()}")

    present = {name: (target / name).is_file() for name in EXPECTED_FILES}
    missing = [name for name, exists in present.items() if not exists]
    if missing:
        raise RuntimeError(f"Installation is incomplete; missing: {', '.join(missing)}")

    uninstall = target / "uninstall.exe"
    remove = _run([str(uninstall), "/S"], timeout)
    removed = _wait_removed(target, timeout)
    if remove.returncode != 0:
        raise RuntimeError(f"Uninstaller failed with exit code {remove.returncode}: {remove.stderr.strip()}")
    if not removed:
        raise RuntimeError(f"Installation directory was not removed: {target}")

    return {
        "ok": True,
        "installer": str(installer),
        "target": str(target),
        "artifact_version": artifact_version,
        "installed_files": present,
        "install_returncode": install.returncode,
        "uninstall_returncode": remove.returncode,
        "removed": removed,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        import json

        print(json.dumps(run_smoke(args.installer, args.target, args.timeout, args.version_file), ensure_ascii=False, indent=2))
    except (FileNotFoundError, FileExistsError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Windows installer smoke test failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
