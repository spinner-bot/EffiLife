#!/usr/bin/env python3
"""Exercise the compiled Tauri app through the real platform WebDriver."""
from contextlib import ExitStack
from pathlib import Path
import json
import os
import select
import subprocess
import sys
import time
import urllib.request
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from native import environment, ROOT
from webdriver import Driver
from webkit_smoke import port, stop

def main():
    sdk = ROOT / ".tools/native-sdk"
    application = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / ".cache/native-target/debug/effilife-desktop"
    output = ROOT / "test-results/native-desktop"
    output.mkdir(parents=True, exist_ok=True)
    profile = ROOT / ".cache/native-desktop" / str(uuid.uuid4())
    env = environment()
    for key in ["data", "cache", "config", "run"]:
        directory = profile / key
        directory.mkdir(parents=True, mode=0o700)
        env["XDG_" + ("RUNTIME_DIR" if key == "run" else key.upper() + "_HOME")] = str(directory)
    env.update({"GDK_BACKEND": "x11", "LIBGL_ALWAYS_SOFTWARE": "1", "WEBKIT_DISABLE_DMABUF_RENDERER": "1", "XKB_CONFIG_ROOT": str(sdk / "usr/share/X11/xkb"), "TAURI_WEBVIEW_AUTOMATION": "true"})
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
        driver_port, native_port = port(), port()
        webkit = sdk / "usr/lib/x86_64-linux-gnu/webkit2gtk-4.1"
        command = [str(sdk / "usr/bin/proot"), "-b", str(webkit) + ":/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1", str(sdk / "usr/bin/dbus-run-session"), "--", str(ROOT / ".tools/tauri-driver/bin/tauri-driver"), "--port", str(driver_port), "--native-port", str(native_port), "--native-driver", str(sdk / "usr/bin/WebKitWebDriver")]
        process = subprocess.Popen(command, stdout=log, stderr=log, env=env, start_new_session=True)
        cleanup.callback(stop, process)
        endpoint = "http://127.0.0.1:" + str(driver_port)
        for attempt in range(100):
            try:
                with urllib.request.urlopen(endpoint + "/status", timeout=1):
                    break
            except Exception:
                time.sleep(0.1)
        print("Starting actual Tauri desktop smoke:", application, flush=True)
        driver = Driver(endpoint, {"tauri:options": {"application": str(application)}})
        cleanup.callback(driver.close)
        driver.wait(lambda: driver.script("return document.querySelector('h1')?.textContent === '让每一份投入，都有迹可循。'"), "native application startup")
        features = driver.script("return {native:!!window.__TAURI_INTERNALS__,origin:location.origin,secure:isSecureContext,uuid:typeof crypto.randomUUID}")
        assert features["native"] and features["uuid"] == "function", features
        driver.script("location.hash='/todos'")
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('.quick-capture'))"))
        driver.fill(driver.element(".quick-capture input"), "原生桌面真实待办")
        driver.button("添加待办", "document.querySelector('.quick-capture')")
        driver.wait(lambda: driver.script("return document.querySelector('.list-row')?.textContent.includes('原生桌面真实待办')"))
        driver.call("POST", "/refresh", {})
        driver.wait(lambda: driver.script("return document.querySelector('.list-row')?.textContent.includes('原生桌面真实待办')"), "native IndexedDB persistence")
        rect = driver.call("GET", "/window/rect")
        subprocess.run([sys.executable, str(ROOT / "scripts/capture-display.py"), str(output / "desktop.png"), *[str(rect[key]) for key in ["x", "y", "width", "height"]]], env=env, check=True)
        report = {"application": str(application.relative_to(ROOT)), "features": features, "checks": ["actual Tauri startup", "native origin capabilities", "IndexedDB capture and reload"]}
        (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Tauri desktop smoke passed:", ", ".join(report["checks"]), flush=True)

if __name__ == "__main__":
    main()
