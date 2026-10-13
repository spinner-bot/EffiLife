"""Run an isolated Windows installer upgrade smoke test."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from smoke_windows_installer import (
    EXPECTED_FILES,
    INSTALLER_VERSION_PATTERN,
    _ensure_safe_target,
    _run,
    _wait_removed,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-installer", type=Path, required=True)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--version-file", type=Path, required=True)
    parser.add_argument(
        "--data-dir",
        type=Path,
        help=(
            "Optional isolated EffiLife data directory. A probe is created before "
            "the upgrade and must remain byte-identical after upgrade and uninstall."
        ),
    )
    parser.add_argument("--timeout", type=float, default=90.0)
    return parser


def _resolve_installer(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Installer not found: {resolved}")
    return resolved


def _prepare_data_probe(data_dir: Path | None) -> tuple[Path, bytes] | None:
    """Create a deterministic user-data probe without touching existing data."""
    if data_dir is None:
        return None
    resolved = data_dir.expanduser().resolve()
    if resolved == resolved.anchor or len(resolved.parts) < 3:
        raise ValueError("Refusing to use a filesystem root or broad data directory")
    if resolved.exists():
        raise FileExistsError(f"Upgrade smoke data directory already exists: {resolved}")
    resolved.mkdir(parents=True)
    probe = resolved / "upgrade-preservation-probe.json"
    payload = json.dumps(
        {
            "purpose": "release-upgrade-preservation",
            "sentinel": "EffiLife-data-must-survive-install-lifecycle",
            "schema": 1,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
    probe.write_bytes(payload)
    return probe, payload


def _verify_data_probe(probe: tuple[Path, bytes] | None) -> dict[str, object] | None:
    if probe is None:
        return None
    path, expected = probe
    actual = path.read_bytes() if path.is_file() else None
    if actual != expected:
        expected_hash = hashlib.sha256(expected).hexdigest()
        actual_hash = hashlib.sha256(actual).hexdigest() if actual is not None else None
        raise RuntimeError(
            "User data probe changed or disappeared during upgrade/uninstall: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    return {
        "path": str(path),
        "sha256": hashlib.sha256(actual).hexdigest(),
        "preserved": True,
    }


def run_upgrade(
    previous: Path,
    installer: Path,
    target: Path,
    version_file: Path,
    timeout: float,
    data_dir: Path | None = None,
) -> dict[str, object]:
    if os.name != "nt":
        raise RuntimeError("Windows installer upgrade smoke test requires Windows")
    previous = _resolve_installer(previous)
    installer = _resolve_installer(installer)
    target = _ensure_safe_target(target)
    expected_version = version_file.expanduser().resolve().read_text(encoding="utf-8").strip()
    previous_match = INSTALLER_VERSION_PATTERN.match(previous.name)
    if previous_match is None:
        raise ValueError(
            "Previous installer filename does not match EffiLife NSIS convention: "
            f"{previous.name}"
        )
    previous_version = previous_match.group("version")
    if previous_version == expected_version:
        raise ValueError(
            "Previous installer must be a different EffiLife version for upgrade validation: "
            f"{previous.name}"
        )
    match = INSTALLER_VERSION_PATTERN.match(installer.name)
    if match is None or match.group("version") != expected_version:
        raise ValueError(f"Current installer version does not match {expected_version}: {installer.name}")

    data_probe = _prepare_data_probe(data_dir)

    old_result = _run([str(previous), "/S", f"/D={target}"], timeout)
    if old_result.returncode != 0:
        raise RuntimeError(f"Previous installer failed with exit code {old_result.returncode}: {old_result.stderr.strip()}")
    old_uninstaller = target / "uninstall.exe"
    if not old_uninstaller.is_file():
        raise RuntimeError("Previous installation did not produce an uninstaller")

    upgrade_result = _run([str(installer), "/S", f"/D={target}"], timeout)
    if upgrade_result.returncode != 0:
        raise RuntimeError(f"Upgrade installer failed with exit code {upgrade_result.returncode}: {upgrade_result.stderr.strip()}")
    installed_files = {name: (target / name).is_file() for name in EXPECTED_FILES}
    missing = [name for name, exists in installed_files.items() if not exists]
    if missing:
        raise RuntimeError(f"Upgrade installation is incomplete; missing: {', '.join(missing)}")

    current_uninstaller = target / "uninstall.exe"
    remove_result = _run([str(current_uninstaller), "/S"], timeout)
    removed = _wait_removed(target, timeout)
    if remove_result.returncode != 0:
        raise RuntimeError(f"Post-upgrade uninstaller failed with exit code {remove_result.returncode}: {remove_result.stderr.strip()}")
    if not removed:
        raise RuntimeError(f"Upgraded installation directory was not removed: {target}")
    data_report = _verify_data_probe(data_probe)
    return {
        "ok": True,
        "previous_installer": str(previous),
        "previous_version": previous_version,
        "installer": str(installer),
        "target": str(target),
        "target_version": expected_version,
        "installed_files": installed_files,
        "removed": removed,
        "data_probe": data_report,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        print(json.dumps(run_upgrade(args.previous_installer, args.installer, args.target, args.version_file, args.timeout, args.data_dir), ensure_ascii=False, indent=2))
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Windows installer upgrade smoke test failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
