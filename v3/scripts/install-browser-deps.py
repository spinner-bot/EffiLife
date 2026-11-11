#!/usr/bin/env python3
"""Extract missing browser shared libraries locally, without changing OS packages."""
from pathlib import Path
import subprocess
from run import ROOT

cache = ROOT / ".cache/browser-system"
destination = ROOT / ".tools/browser-libs"
cache.mkdir(parents=True, exist_ok=True)
destination.mkdir(parents=True, exist_ok=True)
subprocess.check_call(["apt-get", "download", "libasound2"], cwd=cache)
package = max(cache.glob("libasound2_*.deb"), key=lambda path: path.stat().st_mtime)
subprocess.check_call(["dpkg-deb", "-x", str(package), str(destination)])
print("Browser shared library installed under", destination)
