#!/usr/bin/env python3
"""Run v3 tooling with its own checksum-verified Node distribution."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def ensure_node():
    settings = json.loads((ROOT / "toolchain.json").read_text())
    machine = {"x86_64": "x64", "aarch64": "arm64"}.get(platform.machine())
    system = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if not machine or not system:
        raise SystemExit("Use the pinned Node version on this platform; automatic bootstrap supports Linux/macOS.")
    name = f"node-{settings['node']}-{system}-{machine}"
    destination = ROOT / ".tools" / name
    if (destination / "bin/node").is_file():
        return destination / "bin"
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive_name = name + ".tar.xz"
    base = f"{settings['source']}/{settings['node']}"
    checksums = urllib.request.urlopen(base + "/SHASUMS256.txt", timeout=60).read().decode()
    expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == archive_name)
    archive = destination.parent / archive_name
    print(f"Downloading {archive_name}", flush=True)
    urllib.request.urlretrieve(base + "/" + archive_name, archive)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        archive.unlink()
        raise SystemExit("Node archive checksum verification failed")
    with tarfile.open(archive) as bundle:
        for item in bundle.getmembers():
            target = (destination.parent / item.name).resolve()
            if not target.is_relative_to(destination):
                raise SystemExit("Unexpected path in Node archive")
            if item.issym() or item.islnk():
                link = ((target.parent if item.issym() else destination.parent) / item.linkname).resolve()
                if not link.is_relative_to(destination):
                    raise SystemExit("Unexpected link in Node archive")
        bundle.extractall(destination.parent)
    archive.unlink()
    return destination / "bin"

def main():
    binaries = ensure_node()
    arguments = sys.argv[1:] or ["node", "--version"]
    if arguments[0] not in {"node", "npm", "npx"}:
        raise SystemExit("Usage: python3 scripts/run.py node|npm|npx [arguments]")
    environment = dict(os.environ)
    environment["PATH"] = str(binaries) + os.pathsep + environment.get("PATH", "")
    raise SystemExit(subprocess.call([str(binaries / arguments[0]), *arguments[1:]], cwd=ROOT, env=environment))

if __name__ == "__main__":
    main()

