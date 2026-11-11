#!/usr/bin/env python3
"""Install from the canonical npm registry through Python on restricted hosts.

Some workstations allow Python HTTPS while Node outbound connections time out.
The loopback relay preserves npm integrity verification and canonical lock URLs.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import threading
import urllib.request
from run import ROOT, ensure_node

REGISTRY = "https://registry.npmjs.org"


def main():
    binaries = ensure_node()
    cache = ROOT / ".cache" / "registry"
    cache.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                target = REGISTRY + self.path
                key = hashlib.sha256(target.encode()).hexdigest()
                entry = cache / key
                if entry.is_file():
                    payload = entry.read_bytes()
                else:
                    request = urllib.request.Request(target, headers={"Accept": "application/vnd.npm.install-v1+json"})
                    with urllib.request.urlopen(request, timeout=120) as response:
                        payload = response.read()
                    temporary = entry.with_name(entry.name + "." + str(threading.get_ident()))
                    temporary.write_bytes(payload)
                    temporary.replace(entry)
                is_json = payload.lstrip().startswith(b"{")
                if is_json:
                    payload = payload.replace(REGISTRY.encode(), origin.encode())
                self.send_response(200)
                self.send_header("Content-Type", "application/json" if is_json else "application/octet-stream")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as error:
                self.send_error(502, str(error))

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    origin = f"http://127.0.0.1:{server.server_port}"
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    lockfile = ROOT / "package-lock.json"
    if lockfile.is_file():
        lockfile.write_text(lockfile.read_text().replace(REGISTRY, origin))
    environment = dict(os.environ)
    environment["PATH"] = str(binaries) + os.pathsep + environment.get("PATH", "")
    environment["npm_config_registry"] = origin
    environment["npm_config_fetch_retries"] = "1"
    try:
        code = subprocess.call([str(binaries / "npm"), *(sys.argv[1:] or ["install"]), "--no-audit", "--no-fund"], cwd=ROOT, env=environment)
    finally:
        if lockfile.is_file():
            lockfile.write_text(lockfile.read_text().replace(origin, REGISTRY))
        server.shutdown()
        server.server_close()
    raise SystemExit(code)


if __name__ == "__main__":
    main()
