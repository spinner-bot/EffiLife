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
    parser.add_argument("--skip-build", action="store_true", help="skip the unified frontend production build")
    args = parser.parse_args()

    steps: list[dict[str, object]] = []
    if not args.skip_tests:
        steps.append(run_step("Python regression", [sys.executable, "-m", "pytest", "-q"]))
    steps.append(run_step("Desktop release configuration", [sys.executable, "scripts/check_release_config.py"]))
    steps.append(run_step("Mobile release configuration", [sys.executable, "scripts/check_mobile_release_config.py"]))
    if not args.skip_build:
        steps.append(run_step("Unified frontend production build", [sys.executable, "scripts/build_frontend.py"]))

    failed = [step for step in steps if step["returncode"] != 0]
    summary = {"ok": not failed, "steps": steps, "skipped": {"tests": args.skip_tests, "build": args.skip_build}}
    print("\n" + json.dumps(summary, ensure_ascii=True, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
