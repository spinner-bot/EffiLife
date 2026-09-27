import json
import socket
import subprocess
import sys
import time
from urllib.error import URLError
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "plan-helper" / "web" / "server.py"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_plan_helper_health_endpoint_identifies_service(tmp_path):
    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, str(SERVER), "--host", "127.0.0.1", "--port", str(port), "--data-dir", str(tmp_path)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 8
        payload = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise AssertionError(f"plan-helper exited early: {process.returncode}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    break
            except (OSError, URLError):
                time.sleep(0.1)

        assert payload is not None
        assert payload["success"] is True
        assert payload["data"]["service"] == "plan-helper"
        assert payload["data"]["status"] == "ok"
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
