"""Run the reproducible local checks for an EffiLife release candidate.

This command deliberately does not start servers, install packages, sign
artifacts, or mutate user data. Browser smoke and platform-specific signing
remain explicit follow-up gates because they require a running service or
external credentials/devices.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, command: list[str], *, cwd: Path = ROOT) -> dict[str, object]:
    print(f"\n== {name} ==", flush=True)
    print("$ " + " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=cwd, check=False)
    return {"name": name, "command": command, "returncode": completed.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true", help="skip the full Python regression suite")
    parser.add_argument("--skip-compatibility-build", action="store_true", help="skip the legacy to-dos compatibility UI build")
    parser.add_argument("--skip-build", action="store_true", help="skip the unified frontend production build")
    parser.add_argument(
        "--verify-artifact",
        nargs=2,
        action="append",
        metavar=("DIRECTORY", "EXTENSION"),
        help="verify an existing packaged artifact directory and extension (repeatable)",
    )
    parser.add_argument(
        "--verify-manifest",
        nargs=3,
        action="append",
        metavar=("MANIFEST", "DIRECTORY", "TARGET"),
        help="verify an existing release manifest against its directory and target (repeatable)",
    )
    parser.add_argument(
        "--verify-upgrade",
        nargs=4,
        action="append",
        metavar=("PREVIOUS", "CURRENT", "TARGET", "DATA_DIR"),
        help="run the isolated Windows installer upgrade smoke test (repeatable)",
    )
    args = parser.parse_args()

    steps: list[dict[str, object]] = []
    if not args.skip_tests:
        steps.append(run_step("Python regression", [sys.executable, "-m", "pytest", "-q"]))
    steps.append(run_step("Desktop release configuration", [sys.executable, "scripts/check_release_config.py"]))
    steps.append(run_step("Mobile release configuration", [sys.executable, "scripts/check_mobile_release_config.py"]))
    if not args.skip_compatibility_build:
        steps.append(run_step("Compatibility UI production build", [sys.executable, "scripts/build_todos_ui.py"]))
    if not args.skip_build:
        steps.append(run_step("Unified frontend production build", [sys.executable, "scripts/build_frontend.py"]))
    for directory, extension in args.verify_artifact or []:
        steps.append(run_step(
            f"Packaged artifact verification ({extension})",
            [
                sys.executable,
                "scripts/verify_release_artifacts.py",
                "--directory",
                directory,
                "--extension",
                extension,
                "--version-file",
                "time-helper/VERSION",
            ],
        ))
    for manifest, directory, target in args.verify_manifest or []:
        steps.append(run_step(
            f"Release manifest verification ({target})",
            [
                sys.executable,
                "scripts/verify_release_manifest.py",
                "--manifest",
                manifest,
                "--directory",
                directory,
                "--version-file",
                "time-helper/VERSION",
                "--target",
                target,
            ],
        ))
    for previous, current, target, data_dir in args.verify_upgrade or []:
        steps.append(run_step(
            f"Windows installer upgrade verification ({target})",
            [
                sys.executable,
                "scripts/smoke_windows_upgrade.py",
                "--previous-installer",
                previous,
                "--installer",
                current,
                "--target",
                target,
                "--version-file",
                "time-helper/VERSION",
                "--data-dir",
                data_dir,
            ],
        ))

    failed = [step for step in steps if step["returncode"] != 0]
    summary = {
        "ok": not failed,
        "steps": steps,
        "skipped": {
            "tests": args.skip_tests,
            "compatibility_build": args.skip_compatibility_build,
            "build": args.skip_build,
            "artifact_verification": not bool(args.verify_artifact),
            "manifest_verification": not bool(args.verify_manifest),
            "upgrade_verification": not bool(args.verify_upgrade),
        },
    }
    print("\n" + json.dumps(summary, ensure_ascii=True, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
