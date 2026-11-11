#!/usr/bin/env python3
"""Install Playwright's matching headless browser using the workstation HTTPS path."""
from pathlib import Path
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from run import ROOT

output = subprocess.check_output(
    [sys.executable, str(ROOT / "scripts/run.py"), "npx", "playwright", "install", "--dry-run", "chromium"],
    text=True,
)
block = next(part for part in output.split("\n\n") if "Chrome Headless Shell" in part)
destination = Path(re.search(r"Install location:\s+(.+)", block).group(1).strip())
url = re.search(r"Download url:\s+(.+)", block).group(1).strip()
if not destination.resolve().is_relative_to((ROOT / ".cache/playwright").resolve()):
    raise SystemExit("Unexpected browser installation path")
destination.mkdir(parents=True, exist_ok=True)
archive = destination / "download.zip"
print("Downloading matching Chrome Headless Shell", flush=True)
urllib.request.urlretrieve(url, archive)
with zipfile.ZipFile(archive) as bundle:
    if bundle.testzip() is not None:
        raise SystemExit("Browser archive failed integrity checking")
    for item in bundle.infolist():
        target = (destination / item.filename).resolve()
        if not target.is_relative_to(destination):
            raise SystemExit("Unexpected browser archive path")
        bundle.extract(item, destination)
        mode = item.external_attr >> 16
        if mode:
            os.chmod(target, mode & 0o777)
archive.unlink()
(destination / "INSTALLATION_COMPLETE").touch()
print("Browser installed:", destination)
