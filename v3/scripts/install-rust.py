#!/usr/bin/env python3
"""Install pinned Rust components locally, verifying official manifest hashes."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def fetch(url, path):
    temporary = path.with_suffix(path.suffix + ".part")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=45) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(path)
            return
        except Exception:
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise

def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("Automatic bootstrap currently supports Linux x86_64. Install the pinned Rust version on other platforms.")
    settings = json.loads((ROOT / "toolchain.json").read_text())["rust"]
    destination = ROOT / ".tools" / ("rust-" + settings["version"])
    if (destination / "bin" / "cargo").is_file() and (destination / "bin" / "rustc").is_file():
        print(destination, flush=True)
        return
    cache = ROOT / ".cache" / "rust"
    cache.mkdir(parents=True, exist_ok=True)
    base = settings["source"] + "/dist/" + settings["date"]
    manifest = cache / "channel-rust-stable.toml"
    print("Reading official pinned Rust manifest", flush=True)
    fetch(base + "/" + manifest.name, manifest)
    checksum = manifest.with_suffix(".toml.sha256")
    fetch(base + "/" + checksum.name, checksum)
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != checksum.read_text().split()[0]:
        raise SystemExit("Rust manifest checksum mismatch")
    text = manifest.read_text()

    def component(name):
        section = re.search(r"(?m)^\\[pkg\\." + name + r"\\.target\\.x86_64-unknown-linux-gnu\\]\\n(.*?)(?=\\n\\[|\\Z)", text, re.S)
        if not section:
            raise SystemExit("Rust component is unavailable: " + name)
        fields = dict(re.findall(r'(?m)^(xz_url|xz_hash) = "([^"]+)"$', section.group(1)))
        archive = cache / fields["xz_url"].rsplit("/", 1)[-1]
        if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != fields["xz_hash"]:
            print("Downloading " + archive.name, flush=True)
            fetch(fields["xz_url"], archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != fields["xz_hash"]:
            raise SystemExit("Rust component checksum mismatch: " + name)
        return archive

    with ThreadPoolExecutor(max_workers=3) as pool:
        archives = list(pool.map(component, ["rustc", "rust-std", "cargo"]))
    for archive in archives:
        extraction = cache / archive.name.removesuffix(".tar.xz")
        if not extraction.is_dir():
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    target = (cache / member.name).resolve()
                    if not target.is_relative_to(extraction):
                        raise SystemExit("Unsafe Rust archive path")
                    if member.issym() or member.islnk():
                        link = ((target.parent if member.issym() else cache) / member.linkname).resolve()
                        if not link.is_relative_to(extraction):
                            raise SystemExit("Unsafe Rust archive link")
                bundle.extractall(cache)
        subprocess.run(["bash", str(extraction / "install.sh"), "--prefix=" + str(destination), "--disable-ldconfig"], check=True, cwd=extraction)
    subprocess.run([str(destination / "bin/rustc"), "--version"], check=True)
    subprocess.run([str(destination / "bin/cargo"), "--version"], check=True)

if __name__ == "__main__":
    main()

