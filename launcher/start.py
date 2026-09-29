#!/usr/bin/env python3
"""
EffiLife 效率工具集 - 统一启动器
"""

import os
import sys
import json
import subprocess
import webbrowser
import shutil
import signal
import socket
import threading
import time
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
VERSION_FILE = BASE_DIR / "time-helper" / "VERSION"

# Custom Node.js location (F drive)
CUSTOM_NODE_DIR = Path(os.environ.get("EFFILIFE_NODE_DIR", "F:/dev-tools/node"))


def configured_data_dir():
    """Return the optional unified runtime data directory.

    Development launches keep the historical plan-helper data location when
    this is unset. Packaged launchers can set ``EFFILIFE_DATA_DIR`` so every
    sidecar writes below the platform-specific application data root without
    hard-coding a path into the repository.
    """
    raw = os.environ.get("EFFILIFE_DATA_DIR", "").strip()
    return Path(raw).expanduser() if raw else None


def plan_helper_command():
    """Build the sidecar command, forwarding the unified data root if set."""
    command = [sys.executable, "web/server.py"]
    data_dir = configured_data_dir()
    if data_dir is not None:
        command.extend(["--data-dir", str(data_dir)])
    return command


def find_npm():
    """Find npm executable, checking custom location first"""
    # npm.cmd is only useful when the matching Node runtime is available.
    # A stale npm shim on PATH otherwise makes the launcher select dev mode
    # and fail later with a less actionable error.
    node_available = bool(find_node())
    if not node_available:
        return None

    # Check custom F drive location first
    if os.name == "nt":
        custom_npm = CUSTOM_NODE_DIR / "npm.cmd"
        if custom_npm.exists():
            return str(custom_npm)

    # Then check system PATH
    if os.name == "nt":
        for name in ["npm.cmd", "npm"]:
            path = shutil.which(name)
            if path:
                return path
    else:
        path = shutil.which("npm")
        if path:
            return path
    return None


def find_node():
    """Find the Node executable using the same rules as npm."""
    candidates = []
    if os.name == "nt":
        candidates.append(CUSTOM_NODE_DIR / "node.exe")
        system_node = shutil.which("node.exe") or shutil.which("node")
        if system_node:
            candidates.append(Path(system_node))
    else:
        system_node = shutil.which("node")
        if system_node:
            candidates.append(Path(system_node))
    return next((str(path) for path in candidates if path.exists()), None)


def find_rust_tool(name):
    """Find a Rust toolchain executable for release diagnostics."""
    return shutil.which(name) or shutil.which(f"{name}.exe")


def node_environment():
    """Build an environment that can run npm and its child processes."""
    env = os.environ.copy()
    if CUSTOM_NODE_DIR.exists():
        env["PATH"] = str(CUSTOM_NODE_DIR) + os.pathsep + env.get("PATH", "")
    return env


def process_group_options():
    """Keep launcher-owned child processes together for reliable shutdown."""
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def dependencies_ready(cwd):
    """Avoid running npm install on every launch."""
    module_dir = Path(cwd) / "node_modules"
    return module_dir.is_dir() and (module_dir / "vite").is_dir()


def startup_timeout(default=30):
    """Return a bounded startup timeout, configurable for slow machines."""
    raw = os.environ.get("EFFILIFE_STARTUP_TIMEOUT", str(default))
    try:
        return max(5, min(180, int(raw)))
    except ValueError:
        return default


def setup_timeout(default=300):
    """Return a bounded timeout for first-run dependency installation."""
    raw = os.environ.get("EFFILIFE_SETUP_TIMEOUT", str(default))
    try:
        return max(30, min(900, int(raw)))
    except ValueError:
        return default


def packaged_mode():
    """Return whether the launcher must use packaged artifacts only."""
    return "--packaged" in sys.argv or os.environ.get("EFFILIFE_LAUNCH_MODE", "").strip().lower() == "packaged"


def app_version():
    """Read the desktop version without importing frontend or build tooling."""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def launcher_log_path():
    """Return the per-user JSONL log path used for startup diagnostics."""
    override = os.environ.get("EFFILIFE_LOG_DIR")
    if override:
        return Path(override) / "launcher.log"
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "EffiLife" / "logs" / "launcher.log"


def record_launcher_event(event, **details):
    """Append a compact, best-effort startup event for later troubleshooting."""
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "version": app_version(),
        **details,
    }
    try:
        path = launcher_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 1024 * 1024:
            rotated = path.with_suffix(".log.1")
            try:
                rotated.unlink(missing_ok=True)
            except OSError:
                pass
            path.replace(rotated)
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        # Diagnostics must never make the launcher fail on read-only installs.
        return False
    return True


def bundle_argument():
    """Return the bundle path passed to the read-only verification command."""
    for index, argument in enumerate(sys.argv):
        if argument == "--verify-bundle":
            return sys.argv[index + 1] if index + 1 < len(sys.argv) else None
        if argument.startswith("--verify-bundle="):
            return argument.split("=", 1)[1] or None
    return None


def verify_bundle_command(bundle_path):
    """Print a machine-readable workspace bundle health report."""
    from common.data_exchange import verify_workspace_bundle

    try:
        report = verify_workspace_bundle(bundle_path)
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True))
        return False
    print(json.dumps({"ok": True, **report}, ensure_ascii=True, indent=2))
    return True


def release_check_command():
    """Print the read-only desktop release preflight as machine-readable JSON."""
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    from scripts.check_release_config import validate

    errors = validate(BASE_DIR)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=True, indent=2))
    return not errors


def get_time_helper_cmd():
    """Get command for time-helper, prefer dev mode for latest features"""
    exe_paths = time_helper_binary_paths()

    # Formal installers must never unexpectedly switch to a source checkout's
    # Vite server merely because Node happens to be installed on the machine.
    if packaged_mode():
        for exe_path in exe_paths:
            if exe_path.exists():
                return [str(exe_path)], None, None
        dist_path = BASE_DIR / "time-helper" / "desk" / "dist"
        if (dist_path / "index.html").exists():
            return [
                sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
                "--port", "1420", "--bind", "127.0.0.1", "--directory", str(dist_path),
            ], "http://127.0.0.1:1420", None
        return None, None, None

    npm = find_npm()
    if npm:
        # Dev mode - shows latest code changes
        return [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "1420", "--strictPort"], "http://127.0.0.1:1420", [npm, "install"]

    # Fall back to compiled exe
    for exe_path in exe_paths:
        if exe_path.exists():
            return [str(exe_path)], None, None  # cmd, url, setup

    # A checked-in/CI-produced static build remains usable on machines that
    # do not have Node.js. This is a test-launcher fallback; packaged Tauri
    # binaries still take precedence above it.
    dist_path = BASE_DIR / "time-helper" / "desk" / "dist"
    if (dist_path / "index.html").exists():
        return [
            sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
            "--port", "1420", "--bind", "127.0.0.1", "--directory", str(dist_path),
        ], "http://127.0.0.1:1420", None
    return None, None, None


def time_helper_binary_paths():
    """Return release/debug Tauri binaries for Windows and POSIX targets."""
    binary_names = ["efflife-desk.exe", "efflife-desk"] if os.name == "nt" else ["efflife-desk", "efflife-desk.exe"]
    return [
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / profile / name
        for profile in ("release", "debug")
        for name in binary_names
    ]


def get_todos_web_cmd():
    """Get command for to-dos web, checking for npm"""
    npm = find_npm()
    if npm:
        return [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "1421", "--strictPort"], "http://127.0.0.1:1421", [npm, "install"]
    dist_path = BASE_DIR / "to-dos" / "ui" / "dist"
    if (dist_path / "index.html").exists():
        return [
            sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
            "--port", "1421", "--bind", "127.0.0.1", "--directory", str(dist_path),
        ], "http://127.0.0.1:1421", None
    return None, None, None


def build_modules():
    """Build module list dynamically"""
    th_cmd, th_url, th_setup = get_time_helper_cmd()
    td_cmd, td_url, td_setup = get_todos_web_cmd()

    modules = {
        "1": {
            "name": "EffiLife 统一工作台",
            "desc": "计划、待办、时间记录与主题统一入口",
            "cmd": th_cmd,
            "cwd": BASE_DIR / "time-helper" / "desk",
            "url": th_url,
            "setup": th_setup,
            "companions": [{
                "name": "plan-helper API",
                "cmd": plan_helper_command(),
                "cwd": BASE_DIR / "plan-helper",
                "url": "http://127.0.0.1:8765",
                "health_url": "http://127.0.0.1:8765/api/health",
            }],
        },
        "2": {
            "name": "plan-helper（兼容入口）",
            "desc": "旧版计划编辑器，仅用于迁移与调试",
            "cmd": plan_helper_command(),
            "cwd": BASE_DIR / "plan-helper",
            "url": "http://127.0.0.1:8765",
            "setup": None,
        },
        "3": {
            "name": "to-dos（兼容 CLI）",
            "desc": "旧版待办命令行，仅用于迁移与调试",
            "cmd": [sys.executable, "main.py"],
            "cwd": BASE_DIR / "to-dos",
            "url": None,
            "setup": None,
        },
        "4": {
            "name": "to-dos（兼容 Web）",
            "desc": "旧版待办 Web 界面，统一工作台已提供替代入口",
            "cmd": td_cmd,
            "cwd": BASE_DIR / "to-dos" / "ui",
            "url": td_url,
            "setup": td_setup,
        },
        "5": {
            "name": "集成测试",
            "desc": "运行跨模块集成测试 (55 个用例)",
            "cmd": [sys.executable, "tests/test_integration.py"],
            "cwd": BASE_DIR,
            "url": None,
            "setup": None,
        },
        "6": {
            "name": "性能基准",
            "desc": "运行性能测试",
            "cmd": [sys.executable, "tests/test_benchmark.py"],
            "cwd": BASE_DIR,
            "url": None,
            "setup": None,
        },
    }

    # Keep the primary menu metadata ASCII-safe for legacy Windows code pages.
    labels = {
        "1": ("EffiLife unified workspace", "Plans, tasks, time records, and themes"),
        "2": ("plan-helper (compatibility)", "Legacy plan editor for migration and debugging"),
        "3": ("to-dos (compatibility CLI)", "Legacy task command line interface"),
        "4": ("to-dos (compatibility Web)", "Legacy task Web interface"),
        "5": ("Integration tests", "Run cross-module integration checks"),
        "6": ("Performance baseline", "Run performance checks"),
    }
    for key, (name, desc) in labels.items():
        modules[key]["name"] = name
        modules[key]["desc"] = desc

    node_available = bool(find_node() or find_npm())

    # Mark modules that aren't available
    for key, mod in modules.items():
        if mod["cmd"] is None:
            mod["available"] = False
            if key == "1":
                mod["unavailable_reason"] = (
                    "Packaged mode requires a Tauri binary or built dist/index.html"
                    if packaged_mode()
                    else "Unified workspace requires Node.js/npm, a built dist, or a Tauri binary"
                )
        else:
            mod["available"] = True
        if mod["setup"] and not node_available:
            mod["available"] = False
            mod["unavailable_reason"] = "未找到 Node.js/npm"
        mod["needs_setup"] = bool(mod["setup"] and not dependencies_ready(mod["cwd"]))

    return modules


def collect_diagnostics(modules):
    """Collect startup facts without starting or mutating any process."""
    node = find_node()
    npm = find_npm()
    cargo = find_rust_tool("cargo")
    rustc = find_rust_tool("rustc")
    module_status = {}
    for key, module in modules.items():
        url = module.get("url")
        module_status[key] = {
            "name": module.get("name"),
            "cwd": str(module.get("cwd")) if module.get("cwd") else None,
            "command": [str(item) for item in module.get("cmd") or []],
            "setup": [str(item) for item in module.get("setup") or []],
            "available": bool(module.get("available")),
            "unavailable_reason": module.get("unavailable_reason"),
            "url": url,
            "port_occupied": bool(url and local_port_is_occupied(url)),
            "service_ready": bool(url and service_is_ready(url)),
            "needs_setup": bool(module.get("needs_setup")),
        }
    return {
        "base_dir": str(BASE_DIR),
        "version": app_version(),
        "data_dir": str(configured_data_dir()) if configured_data_dir() else None,
        "python": sys.executable,
        "node": node,
        "npm": npm,
        "rust_toolchain": {
            "cargo": cargo,
            "rustc": rustc,
            "available": bool(cargo and rustc),
        },
        "launch_mode": "packaged" if packaged_mode() else "development",
        "time_helper_binaries": [
            {"path": str(path), "exists": path.exists()}
            for path in time_helper_binary_paths()
        ],
        "modules": module_status,
    }


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def _legacy_show_menu(modules):
    clear()
    print("=" * 50)
    print("  EffiLife 效率工具集 - 统一启动器")
    print("=" * 50)
    print()

    for key, module in modules.items():
        status = "" if module["available"] else " [未就绪]"
        print(f"  [{key}] {module['name']}{status}")
        print(f"      {module['desc']}")
        print()

    print("  [0] 退出")
    print()


def show_menu(modules):
    """Render a code-page-safe menu for direct terminal use."""
    clear()
    print("=" * 50)
    print("  EffiLife - Unified Launcher")
    print("=" * 50)
    print()
    for key, module in modules.items():
        status = "" if module["available"] else " [unavailable]"
        print(f"  [{key}] {module['name']}{status}")
        print(f"      {module['desc']}")
        print()
    print("  [0] Exit")
    print()


def run_module(choice, modules, open_browser=True):
    if choice == "0":
        print("再见！")
        sys.exit(0)

    if choice not in modules:
        print("无效选择，请重试")
        return

    module = modules[choice]
    record_launcher_event(
        "module_start",
        choice=choice,
        module=module.get("name"),
        url=module.get("url"),
        command=[str(item) for item in module.get("cmd") or []],
    )

    if not module["available"]:
        record_launcher_event("module_unavailable", choice=choice, module=module.get("name"), reason=module.get("unavailable_reason"))
        print(f"\n❌ {module['name']} 未就绪")
        if "npm" in str(module.get("setup", "")):
            print("请安装 Node.js: https://nodejs.org")
        return

    print(f"\n启动 {module['name']}...")

    env = node_environment()

    # Setup if needed
    if module.get("setup") and module.get("needs_setup"):
        print(f"首次运行，执行 setup: {' '.join(module['setup'])}")
        try:
            result = subprocess.run(
                module["setup"],
                cwd=module["cwd"],
                shell=False,
                env=env,
                timeout=setup_timeout(),
            )
        except subprocess.TimeoutExpired:
            record_launcher_event("dependency_setup_timeout", module=module.get("name"), timeout=setup_timeout())
            print(f"\nSetup timed out after {setup_timeout()} seconds.")
            print("Check the network/npm registry, then retry or install dependencies manually.")
            return
        except OSError as error:
            record_launcher_event("dependency_setup_error", module=module.get("name"), error=str(error))
            print(f"\nUnable to run dependency setup: {error}")
            print(f"Run manually in {module['cwd']}: {' '.join(module['setup'])}")
            return
        if result.returncode != 0:
            record_launcher_event("dependency_setup_failed", module=module.get("name"), returncode=result.returncode)
            print(f"\n❌ Setup 失败，请手动执行:")
            print(f"   cd {module['cwd']}")
            print(f"   {' '.join(module['setup'])}")
            return

    # Run the command
    print(f"执行: {' '.join(module['cmd'])}")
    print(f"工作目录: {module['cwd']}")
    print("-" * 50)
    print("按 Ctrl+C 停止\n")

    companion_processes = start_companions(module, env)
    if companion_processes is None:
        return

    # A separately started frontend may already occupy the configured port.
    # Reuse it instead of launching a second strict-port dev server that exits
    # immediately and is then reported as a startup failure.
    if module.get("url") and service_is_ready(module["url"]):
        record_launcher_event("reuse_existing_service", module=module.get("name"), url=module["url"])
        print(f"使用已运行的主服务: {module['url']}")
        try:
            if open_browser:
                webbrowser.open(module["url"])
            # Stop automatically when a reused frontend exits, instead of
            # leaving an orphan launcher process behind forever.
            while service_is_ready(module["url"]):
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n已停止")
        finally:
            for companion_process in companion_processes:
                terminate_process(companion_process)
        return

    if module.get("url") and local_port_is_occupied(module["url"]):
        record_launcher_event("port_conflict", module=module.get("name"), url=module["url"])
        print(f"\nPort conflict: {module['url']} is already occupied by another service.")
        print("Stop the conflicting process or choose another development port, then retry.")
        for companion_process in companion_processes:
            terminate_process(companion_process)
        return

    try:
        process = subprocess.Popen(
            module["cmd"],
            cwd=module["cwd"],
            shell=False,
            env=env,
            **process_group_options(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        output_thread = threading.Thread(target=stream_output, args=(process,), daemon=True)
        output_thread.start()

        if module.get("url"):
            if not wait_for_service(process, module["url"]):
                record_launcher_event(
                    "service_start_failed",
                    module=module.get("name"),
                    url=module["url"],
                    returncode=process.returncode,
                )
                # Do not block forever when a child stays alive but never
                # becomes reachable. The finally block cleans up companions.
                terminate_process(process)
                return
            print(f"\n>>> 打开浏览器: {module['url']}")
            if open_browser:
                webbrowser.open(module["url"])

        process.wait()
        record_launcher_event("module_exit", module=module.get("name"), returncode=process.returncode)
        output_thread.join(timeout=2)

    except KeyboardInterrupt:
        print("\n已停止")
    except FileNotFoundError as e:
        record_launcher_event("module_command_missing", module=module.get("name"), error=str(e))
        print(f"\n❌ 找不到命令: {e}")
        print(f"请确保已安装所需依赖")
    finally:
        for companion_process in companion_processes:
            terminate_process(companion_process)


def stream_output(process):
    """Forward child output without blocking service readiness checks."""
    if process.stdout is None:
        return
    for line in process.stdout:
        print(line, end="")


def service_is_ready(url):
    """Check whether a local companion service is already running."""
    try:
        with urlopen(url, timeout=1) as response:
            if response.status >= 500:
                return False
            if url.rstrip("/").endswith("/api/health"):
                body = response.read(8192).decode("utf-8", errors="replace")
                return "plan-helper" in body and '"status"' in body
            return True
    except (OSError, URLError):
        return False


def local_port_is_occupied(url):
    """Return whether a local TCP endpoint is already accepting connections."""
    parsed = urlparse(url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or not parsed.port:
        return False
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=0.25):
            return True
    except OSError:
        return False


def terminate_process(process):
    """Stop a process started by the launcher without affecting external services."""
    if process.poll() is None:
        # npm.cmd is a shim: terminating only its PID can leave the spawned
        # node/vite process listening on port 1420.  The PID is launcher-owned,
        # so taskkill's /T scope is limited to that process tree.
        if os.name == "nt" and getattr(process, "pid", None):
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.returncode != 0 and process.poll() is None:
                process.terminate()
        else:
            try:
                # POSIX children are launched in a new session, so terminate
                # the complete Vite/Python process group instead of leaving a
                # descendant behind on the configured port.
                os.killpg(process.pid, signal.SIGTERM)
            except (AttributeError, OSError):
                process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, OSError):
                process.kill()
            process.wait(timeout=5)


def start_companions(module, env):
    """Start only companion services not already provided by the user."""
    managed = []
    for companion in module.get("companions", []):
        health_url = companion.get("health_url", companion.get("url"))
        if health_url and service_is_ready(health_url):
            print(f"使用已运行的 {companion['name']}: {companion['url']}")
            continue

        print(f"启动配套服务: {companion['name']}")
        try:
            process = subprocess.Popen(
                companion["cmd"],
                cwd=companion["cwd"],
                shell=False,
                env=env,
                **process_group_options(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as error:
            print(f"\n无法启动配套服务: {error}")
            for started in managed:
                terminate_process(started)
            return None
        output_thread = threading.Thread(target=stream_output, args=(process,), daemon=True)
        output_thread.start()
        if health_url and not wait_for_service(process, health_url):
            record_launcher_event(
                "companion_start_failed",
                companion=companion.get("name"),
                url=health_url,
                returncode=process.returncode,
            )
            terminate_process(process)
            for started in managed:
                terminate_process(started)
            return None
        managed.append(process)
    return managed


def wait_for_service(process, url, timeout=None):
    """Wait for an HTTP service instead of trusting a particular log format."""
    timeout = startup_timeout() if timeout is None else timeout
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"\n❌ 服务提前退出，退出码: {process.returncode}")
            return False
        if service_is_ready(url):
            return True
        time.sleep(0.25)
    print(f"\n⚠️ 服务在 {timeout} 秒内未响应，请手动打开: {url}")
    return False


def _legacy_main():
    if "--unified" in sys.argv:
        run_module("1", build_modules())
        return

    modules = build_modules()
    while True:
        show_menu(modules)
        try:
            choice = input("请选择 [0-6]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            return
        run_module(choice, modules)
        input("\n按 Enter 继续...")


def main():
    """Launch the unified workspace by default.

    The old module menu remains available explicitly through
    ``--legacy-menu`` for migration and debugging.
    """
    if "--version" in sys.argv:
        print(app_version() or "unknown")
        return
    if "--verify-bundle" in sys.argv or any(argument.startswith("--verify-bundle=") for argument in sys.argv):
        bundle_path = bundle_argument()
        if not bundle_path:
            print(json.dumps({"ok": False, "error": "--verify-bundle requires a bundle path"}, ensure_ascii=True))
            raise SystemExit(2)
        if not verify_bundle_command(bundle_path):
            raise SystemExit(1)
        return
    if "--release-check" in sys.argv:
        if not release_check_command():
            raise SystemExit(1)
        return
    modules = build_modules()
    if "--diagnose" in sys.argv:
        # Keep diagnostics copyable across Windows code pages. JSON consumers
        # decode the escaped Unicode path back to its original value.
        print(json.dumps(collect_diagnostics(modules), ensure_ascii=True, indent=2))
        return
    if "--unified" in sys.argv or "--legacy-menu" not in sys.argv:
        run_module("1", modules, open_browser="--no-browser" not in sys.argv)
        return
    while True:
        show_menu(modules)
        try:
            choice = input("Select [0-6]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExit.")
            return
        run_module(choice, modules)
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
