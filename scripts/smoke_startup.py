"""Run a bounded, read-only smoke check for the unified development workspace."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def endpoint_is_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def wait_for_endpoint(url: str, predicate, process: subprocess.Popen[bytes], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(url, timeout=1) as response:
                body = response.read(65536).decode("utf-8", errors="replace")
                if response.status < 500 and predicate(body):
                    return True
        except (OSError, URLError):
            pass
        time.sleep(0.25)
    return False


def stop_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (AttributeError, OSError):
            process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, OSError):
                process.kill()
        else:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        process.wait(timeout=5)


def wait_for_ports_to_close(ports: tuple[int, ...], timeout: float = 5) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(endpoint_is_listening("127.0.0.1", port) for port in ports):
            return True
        time.sleep(0.25)
    return False


def run_smoke_check(timeout: float = 45) -> dict[str, object]:
    # Import launcher configuration without starting any module.
    sys.path.insert(0, str(ROOT))
    import launcher.start as launcher

    host = "127.0.0.1"
    frontend_port = launcher.workspace_port()
    plan_port = launcher.plan_helper_port()
    ports = (frontend_port, plan_port)
    frontend_url = f"http://{host}:{frontend_port}/"
    health_url = f"http://{host}:{plan_port}/api/health"
    result: dict[str, object] = {
        "ok": False,
        "frontend_url": frontend_url,
        "plan_health_url": health_url,
        "ports_released": False,
    }

    occupied = [port for port in ports if endpoint_is_listening(host, port)]
    if occupied:
        result["error"] = f"configured smoke-test ports are already in use: {occupied}"
        return result

    command = [sys.executable, str(ROOT / "launcher" / "start.py"), "--no-browser"]
    options: dict[str, object] = {}
    if os.name == "nt":
        options["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(command, cwd=ROOT, **options)
    try:
        frontend_ready = wait_for_endpoint(
            frontend_url,
            lambda body: 'name="application-name" content="EffiLife"' in body,
            process,
            timeout,
        )
        plan_ready = wait_for_endpoint(
            health_url,
            lambda body: '"service":"plan-helper"' in "".join(body.split())
            and '"status":"ok"' in "".join(body.split()),
            process,
            timeout,
        )
        result["frontend_ready"] = frontend_ready
        result["plan_helper_ready"] = plan_ready
        result["ok"] = frontend_ready and plan_ready
        if not result["ok"]:
            result["error"] = "unified workspace did not pass both HTTP identity checks"
    finally:
        stop_process_tree(process)
        result["ports_released"] = wait_for_ports_to_close(ports)
        if not result["ports_released"]:
            result["ok"] = False
            result["error"] = "one or more smoke-test ports remained occupied after cleanup"
    return result


def main() -> int:
    raw_timeout = os.environ.get("EFFILIFE_SMOKE_TIMEOUT", "45")
    try:
        timeout = max(5.0, min(180.0, float(raw_timeout)))
    except ValueError:
        timeout = 45.0
    result = run_smoke_check(timeout)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
