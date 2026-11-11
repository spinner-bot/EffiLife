#!/usr/bin/env python3
"""Install the pinned native test driver without changing the system toolchain."""
import json
import subprocess
from native import environment, ROOT

settings = json.loads((ROOT / "toolchain.json").read_text())
subprocess.run([
    "cargo", "install", "tauri-driver", "--version", settings["rust"]["webdriverVersion"],
    "--locked", "--root", str(ROOT / ".tools/tauri-driver"),
], cwd=ROOT, env=environment(), check=True)
