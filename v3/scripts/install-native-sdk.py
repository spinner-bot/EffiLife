#!/usr/bin/env python3
"""Download and unpack a local Ubuntu native SDK without installing system packages."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import subprocess
import urllib.request
import apt
import apt_pkg

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "native-debs"
SDK = ROOT / ".tools" / "native-sdk"
ROOTS = ["libwebkit2gtk-4.1-dev", "libgtk-3-dev", "libayatana-appindicator3-dev", "librsvg2-dev", "libssl-dev", "libglib2.0-bin", "patchelf", "xvfb", "xauth", "webkit2gtk-driver", "proot", "xdotool"]

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    # Installed workstation libraries may be newer than this Ubuntu mirror.
    # Resolve a self-contained SDK from downloadable versions, independently
    # of the server's package status and without changing that status.
    status = CACHE / "empty-status"
    status.write_text("")
    apt_pkg.config.set("Dir::State::status", str(status))
    cache = apt.Cache(memonly=True)
    selected = {}
    pending = [cache[name].candidate for name in ROOTS]
    while pending:
        version = pending.pop()
        if version is None:
            raise SystemExit("A required native package is unavailable")
        name = version.package.name
        if name in selected:
            if selected[name].version != version.version:
                raise SystemExit("Conflicting native SDK versions: " + name)
            continue
        selected[name] = version
        for dependency in version.dependencies:
            if dependency.rawtype not in {"Depends", "PreDepends"}:
                continue
            options = []
            for alternative in dependency.or_dependencies:
                for target in alternative.target_versions:
                    candidate = cache[target.package.name].candidate
                    if candidate and target.version == candidate.version:
                        options.append(target)
            if not options:
                raise SystemExit("Unresolved native SDK dependency: " + str(dependency))
            pending.append(options[0])
    # Keep the host loader and libc pair together. The SDK uses the same Ubuntu
    # baseline and does not need to shadow the host dynamic loader.
    selected.pop("libc6", None)
    selected.pop("libc-bin", None)
    CACHE.mkdir(parents=True, exist_ok=True)
    SDK.mkdir(parents=True, exist_ok=True)
    records = []
    for name, version in sorted(selected.items()):
        if not version.uri or not version.record.get("SHA256"):
            raise SystemExit("Native package lacks URI or integrity metadata: " + name)
        records.append({"name": name, "version": version.version, "uri": version.uri, "sha256": version.record["SHA256"], "size": version.size})
    print("Preparing local native SDK:", len(records), "packages,", round(sum(row["size"] for row in records) / 1024**2), "MiB", flush=True)
    def obtain(row):
        path = CACHE / row["uri"].rsplit("/", 1)[-1]
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]:
            return path
        temporary = path.with_suffix(".part")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(row["uri"], timeout=60) as response, temporary.open("wb") as output:
                    while data := response.read(1024 * 1024):
                        output.write(data)
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != row["sha256"]:
                    raise RuntimeError("Native package checksum mismatch: " + row["name"])
                temporary.replace(path)
                return path
            except Exception:
                temporary.unlink(missing_ok=True)
                if attempt == 2:
                    raise
    with ThreadPoolExecutor(max_workers=8) as pool:
        paths = list(pool.map(obtain, records))
    for index, path in enumerate(paths):
        subprocess.run(["dpkg-deb", "-x", str(path), str(SDK)], check=True)
        if index % 25 == 0:
            print("Unpacked", index + 1, "/", len(paths), flush=True)
    (SDK / "packages.json").write_text(json.dumps(records, indent=2) + "\n")
    print("Local native SDK prepared:", SDK, flush=True)

if __name__ == "__main__":
    main()

