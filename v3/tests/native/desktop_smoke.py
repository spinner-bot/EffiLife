#!/usr/bin/env python3
"""Exercise the compiled Tauri app through the real platform WebDriver."""
from contextlib import ExitStack
from pathlib import Path
import json
import hashlib
import os
import select
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from native import environment, ROOT
from webdriver import Driver
from webkit_smoke import port, stop
from sdk_paths import relocate_webkit

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
    env.update({"GDK_BACKEND": "x11", "LIBGL_ALWAYS_SOFTWARE": "1", "WEBKIT_DISABLE_DMABUF_RENDERER": "1", "WEBKIT_DISABLE_COMPOSITING_MODE": "1", "XKB_CONFIG_ROOT": str(sdk / "usr/share/X11/xkb"), "WEBKIT_INJECTED_BUNDLE_PATH": str(sdk / "usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/injected-bundle"), "TAURI_WEBVIEW_AUTOMATION": "true"})
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
        def snapshot(name):
            subprocess.run([sys.executable, str(ROOT / "scripts/capture-display.py"), str(output / name), "0", "0", "1440", "1000"], env=env, check=True)
        driver_port, native_port = port(), port()
        relocate_webkit(ROOT, env)
        command = [str(sdk / "usr/bin/dbus-run-session"), "--", str(ROOT / ".tools/tauri-driver/bin/tauri-driver"), "--port", str(driver_port), "--native-port", str(native_port), "--native-driver", str(sdk / "usr/bin/WebKitWebDriver")]
        process = subprocess.Popen(command, stdout=log, stderr=log, env=env, cwd=output, start_new_session=True)
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
        sessions = [driver]
        def close_sessions():
            for session in sessions:
                try:
                    session.close()
                except RuntimeError:
                    pass
        cleanup.callback(close_sessions)
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
        driver.script("location.hash='/settings'")
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('input[aria-label=\"导入存档\"]'))"))
        forbidden = output / "unselected-path.d3el"
        forbidden.unlink(missing_ok=True)
        driver.script("window.fsProbe=null;window.__TAURI_INTERNALS__.invoke('plugin:fs|write_file',new Uint8Array([1,2,3]),{headers:{path:encodeURIComponent(arguments[0])}}).then(()=>window.fsProbe='unexpected').catch(e=>window.fsProbe=String(e));", str(forbidden))
        rejection = driver.wait(lambda: driver.script("return window.fsProbe"), "unselected native path rejection")
        assert "forbidden" in rejection.lower() and not forbidden.exists(), rejection
        driver.button("导出存档")
        xdotool = str(sdk / "usr/bin/xdotool")
        def save_window():
            result = subprocess.run([xdotool, "search", "--onlyvisible", "--name", "Save|保存"], env=env, capture_output=True, text=True)
            return result.stdout.strip().splitlines()[-1] if result.returncode == 0 and result.stdout.strip() else None
        window = driver.wait(save_window, "native GTK save dialog")
        snapshot("save-dialog.png")
        destination = output / "native-export.d3el"
        destination.unlink(missing_ok=True)
        subprocess.run([xdotool, "windowfocus", "--sync", window, "key", "--clearmodifiers", "ctrl+a"], env=env, check=True)
        subprocess.run([xdotool, "type", "--clearmodifiers", "--delay", "1", destination.name], env=env, check=True)
        subprocess.run([xdotool, "key", "--clearmodifiers", "Return"], env=env, check=True)
        # GTK may first accept the location entry before activating Save.
        time.sleep(0.3)
        if not destination.exists():
            subprocess.run([xdotool, "key", "--clearmodifiers", "alt+s"], env=env, check=True)
        snapshot("save-confirmation.png")
        driver.wait(lambda: destination.is_file() and destination.stat().st_size > 0, "native file write")
        with zipfile.ZipFile(destination) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            payload = archive.read("payload/workspace.json")
            assert hashlib.sha256(payload).hexdigest() == manifest["checksums"]["payload/workspace.json"]
            exported = json.loads(payload)
            assert exported["todos"][0]["title"] == "原生桌面真实待办"
        driver.script("location.hash='/todos'")
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('.quick-capture'))"))
        driver.fill(driver.element(".quick-capture input"), "导出之后添加的事项")
        driver.button("添加待办", "document.querySelector('.quick-capture')")
        driver.wait(lambda: driver.script("return document.querySelectorAll('.list-row').length===2"))
        driver.script("location.hash='/settings'")
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('input[aria-label=\"导入存档\"]'))"))
        driver.file(driver.element('input[aria-label="导入存档"]'), destination)
        dialog = "Array.from(document.querySelectorAll('[role=dialog]')).find(e=>e.getAttribute('aria-hidden')!=='true')"
        driver.button("确认替换并导入", dialog)
        driver.wait(lambda: driver.script("return !document.querySelector('[role=dialog]')"), "native archive import")
        driver.script("location.hash='/todos'")
        driver.wait(lambda: driver.script("return document.querySelectorAll('.list-row').length===1 && document.querySelector('.list-row').textContent.includes('原生桌面真实待办')"))
        driver.script("location.hash='/settings'")
        driver.button("恢复上一份有效备份")
        driver.button("确认", dialog)
        driver.wait(lambda: driver.script("return !document.querySelector('[role=dialog]')"))
        driver.button("北欧极夜")
        driver.wait(lambda: driver.script("return document.querySelector('.theme-decoration iframe')?.dataset.ready==='true'"), "native decorative worker")
        driver.close()
        sessions.clear()
        driver = Driver(endpoint, {"tauri:options": {"application": str(application)}})
        sessions.append(driver)
        driver.wait(lambda: driver.script("return Boolean(document.querySelector('h1'))"), "native restart")
        driver.script("location.hash='/todos'")
        driver.wait(lambda: driver.script("return document.querySelectorAll('.list-row').length===2"), "durable backup restore after process restart")
        rect = driver.call("GET", "/window/rect")
        subprocess.run([sys.executable, str(ROOT / "scripts/capture-display.py"), str(output / "desktop.png"), *[str(rect[key]) for key in ["x", "y", "width", "height"]]], env=env, check=True)
        report = {"application": str(application.relative_to(ROOT)), "features": features, "deniedWrite": rejection, "checks": ["actual Tauri startup", "native origin capabilities", "IndexedDB capture and reload", "unselected path write denied", "real GTK save dialog and scoped file write", "export payload and SHA-256", "native archive import", "backup restore", "native decorative worker", "durability across native process restart"]}
        (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("Tauri desktop smoke passed:", ", ".join(report["checks"]), flush=True)

if __name__ == "__main__":
    main()
