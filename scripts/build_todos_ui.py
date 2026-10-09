"""Build the legacy to-dos compatibility UI with the launcher Node toolchain."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODOS_UI = ROOT / "to-dos" / "ui"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launcher import start  # noqa: E402  (repository root is added above)


def main() -> int:
    npm = start.find_npm()
    if not npm:
        print(
            "EffiLife to-dos compatibility UI build requires Node.js/npm. "
            "Set EFFILIFE_NODE_DIR or install Node.js on PATH.",
            file=sys.stderr,
        )
        return 1

    command = [npm, "run", "build"]
    print(f"Building to-dos compatibility UI with: {' '.join(command)}")
    print(f"Working directory: {TODOS_UI}")
    completed = subprocess.run(command, cwd=TODOS_UI, env=start.node_environment(), check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
