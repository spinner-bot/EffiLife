#!/usr/bin/env python3
"""Install Playwright's matching headless browser using the workstation HTTPS path."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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
if (destination / "INSTALLATION_COMPLETE").is_file():
    print("Matching browser is already installed:", destination)
    raise SystemExit(0)
print("Downloading matching Chrome Headless Shell", flush=True)
with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30) as response:
    total = int(response.headers["Content-Length"])
prefix = destination / "download.prefix"
if archive.is_file() and not prefix.exists() and archive.stat().st_size < total:
    archive.replace(prefix)
start = prefix.stat().st_size if prefix.is_file() else 0
chunks = [(offset, min(offset + 4 * 1024 * 1024, total)) for offset in range(start, total, 4 * 1024 * 1024)]

def download_chunk(bounds):
    begin, end = bounds
    path = destination / f"download.part-{begin}"
    if path.is_file() and path.stat().st_size == end - begin:
        return path
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"Range": f"bytes={begin}-{end - 1}"})
            with urllib.request.urlopen(request, timeout=90) as response:
                if response.status != 206 or response.headers.get("Content-Range") != f"bytes {begin}-{end - 1}/{total}":
                    raise RuntimeError("Browser server did not honor the requested range")
                data = response.read()
            if len(data) != end - begin:
                raise RuntimeError("Incomplete browser download chunk")
            path.write_bytes(data)
            return path
        except Exception:
            if attempt == 2:
                raise

with ThreadPoolExecutor(max_workers=8) as pool:
    parts = list(pool.map(download_chunk, chunks))
with archive.open("wb") as output:
    if prefix.is_file():
        output.write(prefix.read_bytes())
    for part in parts:
        output.write(part.read_bytes())
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
if prefix.exists():
    prefix.unlink()
for part in parts:
    part.unlink()
(destination / "INSTALLATION_COMPLETE").touch()
print("Browser installed:", destination)
