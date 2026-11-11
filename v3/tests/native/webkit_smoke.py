#!/usr/bin/env python3
"""Run production UI smoke checks in the actual Linux WebKitGTK distribution."""
from contextlib import ExitStack
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import select
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from native import environment, ROOT
from webdriver import Driver

def port():
    with socket.socket() as connection:
        connection.bind(("127.0.0.1", 0))
        return connection.getsockname()[1]

def stop(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "dist"), **kwargs)
    def log_message(self, *args):
        pass

def main():
    sdk = ROOT / ".tools/native-sdk"
    output = ROOT / "test-results/native-webkit"
    output.mkdir(parents=True, exist_ok=True)
    profile = ROOT / ".cache/native-webkit" / str(uuid.uuid4())
    env = environment()
    for key in ["data", "cache", "config", "run"]:
        directory = profile / key
        directory.mkdir(parents=True, mode=0o700)
        env["XDG_" + ("RUNTIME_DIR" if key == "run" else key.upper() + "_HOME")] = str(directory)
    env.update({"GDK_BACKEND": "x11", "LIBGL_ALWAYS_SOFTWARE": "1", "WEBKIT_DISABLE_DMABUF_RENDERER": "1", "WEBKIT_DISABLE_COMPOSITING_MODE": "1", "XKB_CONFIG_ROOT": str(sdk / "usr/share/X11/xkb"), "WEBKIT_EXEC_PATH": str(sdk / "usr/lib/x86_64-linux-gnu/webkit2gtk-4.1"), "WEBKIT_INJECTED_BUNDLE_PATH": str(sdk / "usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/injected-bundle")})
    if os.geteuid() == 0:
        env["WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS"] = "1"
    with ExitStack() as cleanup:
        log = cleanup.enter_context((output / "process.log").open("w"))
        display = subprocess.Popen([str(sdk / "usr/bin/Xvfb"), "-displayfd", "1", "-screen", "0", "1440x1000x24", "-nolisten", "tcp"], stdout=subprocess.PIPE, stderr=log, env=env, start_new_session=True)
        cleanup.callback(stop, display)
        if not select.select([display.stdout], [], [], 15)[0]:
            raise RuntimeError("Xvfb did not allocate a display")
        number = display.stdout.readline().decode().strip()
        if not number:
            raise RuntimeError("Xvfb failed; see process.log")
        env["DISPLAY"] = ":" + number
        driver_port = port()
        process = subprocess.Popen([str(sdk / "usr/bin/dbus-run-session"), "--", str(sdk / "usr/bin/WebKitWebDriver"), "--port=" + str(driver_port)], stdout=log, stderr=log, env=env, start_new_session=True)
        cleanup.callback(stop, process)
        endpoint = "http://127.0.0.1:" + str(driver_port)
        for attempt in range(100):
            try:
                with urllib.request.urlopen(endpoint + "/status", timeout=1):
                    break
            except Exception:
                time.sleep(0.1)
        server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cleanup.callback(server.server_close)
        cleanup.callback(server.shutdown)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = "http://127.0.0.1:" + str(server.server_port)
        browser = sdk / "usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/MiniBrowser"
        print("Starting real WebKitGTK production smoke", flush=True)
        driver = Driver(endpoint, {"browserName": "MiniBrowser", "webkitgtk:browserOptions": {"binary": str(browser), "args": ["--automation"]}})
        cleanup.callback(driver.close)
        driver.call("POST", "/window/rect", {"width": 1440, "height": 1000})
        driver.navigate(base + "/")
        driver.wait(lambda: driver.script("return document.querySelector('h1')?.textContent === '让每一份投入，都有迹可循。'"), "production application startup")
        features = driver.script("return {secure:isSecureContext,randomUUID:typeof crypto.randomUUID,clone:typeof structuredClone,canvas:typeof HTMLCanvasElement.prototype.transferControlToOffscreen,locale:document.documentElement.lang}")
        assert features["randomUUID"] == "function" and features["clone"] == "function", features
        driver.navigate(base + "/#/todos")
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('.quick-capture'))"))
        driver.fill(driver.element(".quick-capture input"), "WebKit 真实待办")
        driver.button("添加待办", "document.querySelector('.quick-capture')")
        driver.wait(lambda: driver.script("return document.querySelector('.list-row')?.textContent.includes('WebKit 真实待办')"), "durable todo capture")
        driver.call("POST", "/refresh", {})
        driver.wait(lambda: driver.script("return document.querySelector('.list-row')?.textContent.includes('WebKit 真实待办')"), "IndexedDB persistence")
        driver.screenshot(output / "todos-1440.png")
        driver.navigate(base + "/#/settings")
        driver.button("北欧极夜")
        driver.wait(lambda: driver.script("return document.querySelector('.theme-decoration iframe')?.dataset.ready === 'true'"), "opaque Worker and OffscreenCanvas")
        driver.screenshot(output / "theme-1440.png")
        driver.call("POST", "/window/rect", {"width": 390, "height": 950})
        driver.navigate(base + "/#/todos")
        driver.wait(lambda: driver.script("return document.querySelector('h1')?.textContent.includes('把小事放下')"))
        overflow = driver.script("return document.documentElement.scrollWidth - innerWidth")
        assert overflow <= 1, overflow
        driver.screenshot(output / "todos-390.png")
        report = {"engine": "WebKitGTK 2.50.4", "features": features, "checks": ["production startup", "real IndexedDB capture and reload", "isolated decorative Worker ready", "390px layout"], "overflow": overflow}
        (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("WebKitGTK smoke passed:", ", ".join(report["checks"]), flush=True)

if __name__ == "__main__":
    main()

