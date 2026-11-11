"""Resumable ranged HTTPS download used by large local toolchains."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib.request

def download(url: str, destination: Path, workers: int = 4):
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=45) as response:
        total = int(response.headers["Content-Length"])
    prefix = destination.with_suffix(destination.suffix + ".part")
    start = prefix.stat().st_size if prefix.is_file() else 0
    if start > total:
        prefix.unlink()
        start = 0
    chunk_size = 2 * 1024 * 1024
    ranges = [(offset, min(total, offset + chunk_size)) for offset in range(start, total, chunk_size)]
    def chunk(bounds):
        begin, end = bounds
        path = destination.with_name(destination.name + ".chunk-" + str(begin))
        if path.is_file() and path.stat().st_size == end - begin:
            return path
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"Range": f"bytes={begin}-{end - 1}"})
                with urllib.request.urlopen(request, timeout=90) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {begin}-{end - 1}/{total}":
                        raise RuntimeError("Toolchain server did not honor the requested range")
                    data = response.read()
                if len(data) != end - begin:
                    raise RuntimeError("Incomplete toolchain download chunk")
                path.write_bytes(data)
                return path
            except Exception:
                if attempt == 2:
                    raise
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parts = list(pool.map(chunk, ranges))
    assembled = destination.with_suffix(destination.suffix + ".assembling")
    with assembled.open("wb") as output:
        if prefix.is_file():
            with prefix.open("rb") as source:
                while data := source.read(1024 * 1024):
                    output.write(data)
        for path in parts:
            output.write(path.read_bytes())
    assembled.replace(destination)
    prefix.unlink(missing_ok=True)
    for path in parts:
        path.unlink()

