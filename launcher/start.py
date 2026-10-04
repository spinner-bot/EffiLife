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
import re
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse
from pathlib import Path


def configure_console_encoding() -> None:
    """Keep launcher diagnostics readable on Windows consoles with CJK paths."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Embedded hosts and pytest capture streams may reject reconfigure;
            # their existing encoding is still safer than aborting the launcher.
            continue


configure_console_encoding()

BASE_DIR = Path(__file__).parent.parent
VERSION_FILE = BASE_DIR / "time-helper" / "VERSION"

# Default custom Node.js location (F drive). The environment override is read
# at call time so an embedded launcher and the build diagnostics observe the
# same runtime configuration.
CUSTOM_NODE_DIR = Path("F:/dev-tools/node")


def custom_node_dir() -> Path | None:
    """Return the configured Node directory using the current environment."""
    configured = os.environ.get("EFFILIFE_NODE_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    return CUSTOM_NODE_DIR if os.name == "nt" else None


def node_tool_filename(name: str) -> str:
    """Return the executable filename for the current platform."""
    return f"{name}.cmd" if os.name == "nt" and name == "npm" else (
        f"{name}.exe" if os.name == "nt" else name
    )


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
    command = [sys.executable, "web/server.py", "--port", str(plan_helper_port())]
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

    # Check the configured custom location before PATH on every platform.
    node_dir = custom_node_dir()
    if node_dir is not None:
        custom_npm = node_dir / node_tool_filename("npm")
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
    node_dir = custom_node_dir()
    if node_dir is not None:
        candidates.append(node_dir / node_tool_filename("node"))
    if os.name == "nt":
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


def native_toolchain_status():
    """Report optional native-build tools without changing launcher readiness."""
    sdk_configured = bool(
        os.environ.get("ANDROID_HOME", "").strip()
        or os.environ.get("ANDROID_SDK_ROOT", "").strip()
    )
    return {
        "android": {
            "adb": shutil.which("adb") or shutil.which("adb.exe"),
            "sdk_configured": sdk_configured,
            "ready": bool((shutil.which("adb") or shutil.which("adb.exe")) and sdk_configured),
        },
        "ios": {
            "xcodebuild": shutil.which("xcodebuild") or shutil.which("xcodebuild.exe"),
            "platform_supported": os.name != "nt",
            "ready": bool(shutil.which("xcodebuild") or shutil.which("xcodebuild.exe")),
        },
    }


def node_environment():
    """Build an environment that can run npm and its child processes."""
    env = os.environ.copy()
    node_dir = custom_node_dir()
    if node_dir is not None and node_dir.exists():
        env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
    return env


def process_group_options():
    """Keep launcher-owned child processes together for reliable shutdown."""
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    # The bounded startup smoke check owns the launcher process group and must
    # be able to reap its companion services as one tree on POSIX. Normal
    # launches keep the isolated groups used for interactive shutdown.
    if os.environ.get("EFFILIFE_INHERIT_PROCESS_GROUP") == "1":
        return {}
    return {"start_new_session": True}


def dependencies_ready(cwd):
    """Return whether the frontend dependency entry points are usable.

    Checking only ``node_modules/vite`` is insufficient after an interrupted
    npm install: the package directory can remain while ``.bin`` shims (or
    the desktop type-checker) are missing. In that state the launcher used to
    skip setup and fail later inside ``npm run dev`` with little context.
    """
    module_dir = Path(cwd) / "node_modules"
    bin_dir = module_dir / ".bin"
    suffix = ".cmd" if os.name == "nt" else ""
    required = ["vite"]
    resolved_cwd = Path(cwd).resolve()
    if resolved_cwd.name == "desk" and resolved_cwd.parent.name == "time-helper":
        required.append("vue-tsc")
    return module_dir.is_dir() and all((bin_dir / f"{name}{suffix}").is_file() for name in required)


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


def configured_port(name, default):
    """Return a safe local service port from the environment or its default."""
    raw = os.environ.get(name, "").strip()
    try:
        port = int(raw)
    except ValueError:
        return default
    return port if 1024 <= port <= 65535 else default


def workspace_port():
    return configured_port("EFFILIFE_WORKSPACE_PORT", 1420)


def todos_port():
    return configured_port("EFFILIFE_TODOS_PORT", 1421)


def plan_helper_port():
    return configured_port("EFFILIFE_PLAN_HELPER_PORT", 8765)


def local_url(port):
    return f"http://127.0.0.1:{port}"


def packaged_mode():
    """Return whether the launcher must use packaged artifacts only."""
    return "--packaged" in sys.argv or os.environ.get("EFFILIFE_LAUNCH_MODE", "").strip().lower() == "packaged"


def app_version():
    """Read the desktop version without importing frontend or build tooling."""
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def is_non_empty_file(path):
    """Return whether a candidate runtime artifact is a usable file."""
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


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
    """Print the read-only desktop/mobile release preflight as JSON."""
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    from scripts.check_release_config import validate
    from scripts.check_mobile_release_config import validate as validate_mobile
    from scripts.check_build_environment import build_report

    desktop_errors = validate(BASE_DIR)
    mobile_errors = validate_mobile(BASE_DIR)
    errors = desktop_errors + mobile_errors
    environment = {
        target: build_report(target, BASE_DIR)
        for target in ("desktop", "android", "ios")
    }
    print(json.dumps({
        "ok": not errors,
        "build_ready": all(report["ready"] for report in environment.values()),
        "errors": errors,
        "checks": {
            "desktop": {"ok": not desktop_errors, "errors": desktop_errors},
            "mobile": {"ok": not mobile_errors, "errors": mobile_errors},
        },
        "environment": environment,
    }, ensure_ascii=True, indent=2))
    return not errors


def get_time_helper_cmd():
    """Get command for time-helper, prefer dev mode for latest features"""
    exe_paths = time_helper_binary_paths()

    # Formal installers must never unexpectedly switch to a source checkout's
    # Vite server merely because Node happens to be installed on the machine.
    if packaged_mode():
        for exe_path in time_helper_binary_paths(include_debug=False):
            if is_non_empty_file(exe_path):
                return [str(exe_path)], None, None
        dist_path = BASE_DIR / "time-helper" / "desk" / "dist"
        if is_non_empty_file(dist_path / "index.html"):
            port = workspace_port()
            return [
                sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
                "--port", str(port), "--bind", "127.0.0.1", "--directory", str(dist_path),
            ], local_url(port), None
        return None, None, None

    npm = find_npm()
    if npm:
        # Dev mode - shows latest code changes
        port = workspace_port()
        return [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port), "--strictPort"], local_url(port), [npm, "install"]

    # Fall back to compiled exe
    for exe_path in exe_paths:
        if is_non_empty_file(exe_path):
            return [str(exe_path)], None, None  # cmd, url, setup

    # A checked-in/CI-produced static build remains usable on machines that
    # do not have Node.js. This is a test-launcher fallback; packaged Tauri
    # binaries still take precedence above it.
    dist_path = BASE_DIR / "time-helper" / "desk" / "dist"
    if is_non_empty_file(dist_path / "index.html"):
        port = workspace_port()
        return [
            sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
            "--port", str(port), "--bind", "127.0.0.1", "--directory", str(dist_path),
        ], local_url(port), None
    return None, None, None


def time_helper_binary_paths(include_debug=True):
    """Return Tauri binary candidates for Windows and POSIX targets.

    Development mode may use a debug binary, while packaged mode must never
    silently launch one as if it were a release artifact.
    """
    binary_names = ["efflife-desk.exe", "efflife-desk"] if os.name == "nt" else ["efflife-desk", "efflife-desk.exe"]
    profiles = ("release", "debug") if include_debug else ("release",)
    return [
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / profile / name
        for profile in profiles
        for name in binary_names
    ]


def installer_artifact_patterns():
    """Return the platform bundle locations produced by the release matrix."""
    bundle_root = BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "bundle"
    if os.name == "nt":
        return [bundle_root / "nsis" / "*.exe"]
    if sys.platform == "darwin":
        return [bundle_root / "dmg" / "*.dmg"]
    return [bundle_root / "deb" / "*.deb", bundle_root / "appimage" / "*.AppImage"]


def installer_artifact_version(path):
    """Extract a semantic version from a Tauri bundle filename when present."""
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)(?!\d)", path.name)
    return match.group(1) if match else None


def installer_artifacts():
    """Describe non-empty installer files without creating or mutating anything."""
    current_version = app_version()
    artifacts = []
    for pattern in installer_artifact_patterns():
        matches = sorted(path for path in pattern.parent.glob(pattern.name) if path.is_file())
        if matches:
            artifacts.extend(
                {
                    "path": str(path),
                    "exists": True,
                    "non_empty": path.stat().st_size > 0,
                    "size": path.stat().st_size,
                    "artifact_version": installer_artifact_version(path),
                    "version_matches": (
                        installer_artifact_version(path) is None
                        or current_version is None
                        or installer_artifact_version(path) == current_version
                    ),
                }
                for path in matches
            )
        else:
            artifacts.append({
                "path": str(pattern),
                "exists": False,
                "non_empty": False,
                "size": 0,
                "artifact_version": None,
                "version_matches": False,
            })
    return artifacts


def get_todos_web_cmd():
    """Get the compatibility Web command without leaking dev mode into packages."""
    dist_path = BASE_DIR / "to-dos" / "ui" / "dist"
    if packaged_mode():
        if not is_non_empty_file(dist_path / "index.html"):
            return None, None, None
    else:
        npm = find_npm()
        if npm:
            port = todos_port()
            return [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port), "--strictPort"], local_url(port), [npm, "install"]

    if is_non_empty_file(dist_path / "index.html"):
        port = todos_port()
        return [
            sys.executable, str(BASE_DIR / "launcher" / "static_server.py"),
            "--port", str(port), "--bind", "127.0.0.1", "--directory", str(dist_path),
        ], local_url(port), None
    return None, None, None


def build_modules():
    """Build module list dynamically"""
    th_cmd, th_url, th_setup = get_time_helper_cmd()
    td_cmd, td_url, td_setup = get_todos_web_cmd()

    plan_helper_companion = [{
        "name": "plan-helper API",
        "cmd": plan_helper_command(),
        "cwd": BASE_DIR / "plan-helper",
        "url": local_url(plan_helper_port()),
        "health_url": f"{local_url(plan_helper_port())}/api/health",
    }] if th_url else []

    modules = {
        "1": {
            "name": "EffiLife 统一工作台",
            "desc": "计划、待办、时间记录与主题统一入口",
            "cmd": th_cmd,
            "cwd": BASE_DIR / "time-helper" / "desk",
            "url": th_url,
            "setup": th_setup,
            # A native Tauri build owns its Plan Helper sidecar. Only the
            # browser-based development/static-server modes need the external
            # compatibility API managed by this launcher.
            "companions": plan_helper_companion,
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
    native_tools = native_toolchain_status()
    module_status = {}
    for key, module in modules.items():
        url = module.get("url")
        port_occupied = bool(url and local_port_is_occupied(url))
        service_ready = bool(url and service_is_ready(url))
        runtime_state = (
            "unavailable" if not module.get("available") else
            "ready" if service_ready else
            "port-conflict" if port_occupied else
            "stopped" if url else
            "launchable"
        )
        module_status[key] = {
            "name": module.get("name"),
            "cwd": str(module.get("cwd")) if module.get("cwd") else None,
            "command": [str(item) for item in module.get("cmd") or []],
            "setup": [str(item) for item in module.get("setup") or []],
            "available": bool(module.get("available")),
            "runtime_state": runtime_state,
            "unavailable_reason": module.get("unavailable_reason"),
            "url": url,
            "port_occupied": port_occupied,
            "service_ready": service_ready,
            "needs_setup": bool(module.get("needs_setup")),
        }
    companion_status = {}
    for module_key, module in modules.items():
        for index, companion in enumerate(module.get("companions", [])):
            companion_key = f"{module_key}.{index + 1}"
            url = companion.get("url")
            health_url = companion.get("health_url", url)
            port_occupied = bool(health_url and local_port_is_occupied(health_url))
            service_ready = bool(health_url and service_is_ready(health_url))
            companion_status[companion_key] = {
                "name": companion.get("name"),
                "parent_module": module_key,
                "cwd": str(companion.get("cwd")) if companion.get("cwd") else None,
                "command": [str(item) for item in companion.get("cmd") or []],
                "url": url,
                "health_url": health_url,
                "runtime_state": "ready" if service_ready else "port-conflict" if port_occupied else "stopped",
                "port_occupied": port_occupied,
                "service_ready": service_ready,
            }
    issues = []
    hints = []
    workspace = module_status.get("1", {})
    if not workspace.get("available"):
        issues.append({
            "code": "workspace-unavailable",
            "severity": "error",
            "message": workspace.get("unavailable_reason") or "The unified workspace is not available",
            "hint": "Install Node.js/npm or provide a built Tauri binary or desk/dist/index.html",
        })
    for key, status in module_status.items():
        if status.get("port_occupied") and not status.get("service_ready"):
            issues.append({
                "code": "port-conflict",
                "severity": "error",
                "module": key,
                "message": f"Port for {status.get('name')} is occupied by an unhealthy service",
                "hint": f"Stop the process using {status.get('url')} and run the launcher again",
            })
    for key, status in companion_status.items():
        if status.get("port_occupied") and not status.get("service_ready"):
            issues.append({
                "code": "companion-port-conflict",
                "severity": "error",
                "module": key,
                "message": f"Port for {status.get('name')} is occupied by an unhealthy companion service",
                "hint": f"Stop the process using {status.get('health_url')} and run the launcher again",
            })
    if not cargo or not rustc:
        hints.append({
            "code": "rust-toolchain-missing",
            "severity": "info",
            "message": "Rust/Cargo is unavailable; native Tauri installer builds must run in CI or a release machine",
            "hint": "Install Rust with rustup, or run the desktop release workflow on a release machine",
        })
    if not native_tools["android"]["ready"]:
        hints.append({
            "code": "android-toolchain-missing",
            "severity": "info",
            "message": "Android SDK/ADB is unavailable; Android builds remain a release-runner task",
            "hint": "Install Android SDK platform-tools and set ANDROID_HOME or ANDROID_SDK_ROOT",
        })
    if not native_tools["ios"]["ready"]:
        hints.append({
            "code": "ios-toolchain-missing",
            "severity": "info",
            "message": "iOS native tooling is unavailable in this environment",
            "hint": "Run the iOS workflow on macOS with Xcode and Apple signing prerequisites",
        })
    installer_status = installer_artifacts()
    usable_installers = [
        item for item in installer_status
        if item["exists"] and item["non_empty"] and item.get("version_matches", True)
    ]
    stale_installers = [
        item for item in installer_status
        if item["exists"] and item["non_empty"] and not item.get("version_matches", True)
    ]
    if not usable_installers and not stale_installers:
        hints.append({
            "code": "installer-artifact-missing",
            "severity": "info",
            "message": "No non-empty native installer was found; a Tauri binary is not the same as an installable release",
            "hint": "Run the desktop release workflow or build the platform bundle on a release machine",
        })
    if stale_installers:
        hints.append({
            "code": "installer-artifact-stale",
            "severity": "info",
            "message": "A native installer exists, but its embedded filename version does not match the current application version",
            "hint": "Build a new installer before distributing this checkout",
        })
    if any(status.get("needs_setup") for status in module_status.values()):
        hints.append({
            "code": "dependencies-pending",
            "severity": "info",
            "message": "One or more development modules will install npm dependencies on first launch",
        })
    return {
        "base_dir": str(BASE_DIR),
        "version": app_version(),
        "data_dir": str(configured_data_dir()) if configured_data_dir() else None,
        "ports": {
            "workspace": workspace_port(),
            "todos": todos_port(),
            "plan_helper": plan_helper_port(),
        },
        "python": sys.executable,
        "node": node,
        "npm": npm,
        "rust_toolchain": {
            "cargo": cargo,
            "rustc": rustc,
            "available": bool(cargo and rustc),
        },
        "native_toolchain": native_tools,
        "launch_mode": "packaged" if packaged_mode() else "development",
        "time_helper_binaries": [
            {"path": str(path), "exists": path.exists(), "usable": is_non_empty_file(path)}
            for path in time_helper_binary_paths()
        ],
        "installer_artifacts": installer_status,
        "modules": module_status,
        "companions": companion_status,
        "issues": issues,
        "hints": hints,
    }


def print_doctor_report(report):
    """Render the read-only diagnostic report for people, not parsers."""
    print("EffiLife launcher doctor")
    print(f"Version: {report.get('version') or 'unknown'}")
    print(f"Mode: {report.get('launch_mode')}")
    print(f"Python: {report.get('python')}")
    print(f"Node: {report.get('node') or 'missing'}")
    print(f"npm: {report.get('npm') or 'missing'}")
    rust_toolchain = report.get("rust_toolchain") or {}
    print(f"cargo: {rust_toolchain.get('cargo') or 'missing'}")
    print(f"rustc: {rust_toolchain.get('rustc') or 'missing'}")
    print("Native build: ready" if rust_toolchain.get("available") else "Native build: not ready (install Rust or use CI)")
    installer_status = report.get("installer_artifacts", [])
    installers_ready = any(
        item.get("exists") and item.get("non_empty") and item.get("version_matches", True)
        for item in installer_status
    )
    installers_stale = any(
        item.get("exists") and item.get("non_empty") and not item.get("version_matches", True)
        for item in installer_status
    )
    installer_state = "available" if installers_ready else (
        "stale (version mismatch)" if installers_stale else "not found (binary-only or source checkout)"
    )
    print(f"Native installer: {installer_state}")
    stale_details = [
        item for item in installer_status
        if item.get("exists") and item.get("non_empty") and not item.get("version_matches", True)
    ]
    for item in stale_details:
        artifact_version = item.get("artifact_version") or "unknown"
        artifact_path = item.get("path") or "unknown path"
        print(
            "Stale installer detail: "
            f"{artifact_path} (artifact {artifact_version}, current {report.get('version') or 'unknown'})"
        )
    if installers_ready:
        print("Distribution status: ready")
    else:
        print("Distribution status: not ready; build a version-matched installer before shipping")
    print()

    workspace = report.get("modules", {}).get("1", {})
    workspace_state = workspace.get("runtime_state") or ("ready" if workspace.get("available") else "blocked")
    if workspace_state == "ready" and workspace.get("service_ready"):
        workspace_state = "already running"
    print(f"Unified workspace: {workspace_state}")
    if workspace.get("url"):
        print(f"Workspace URL: {workspace['url']}")

    companions = report.get("companions", {})
    if companions:
        print("\nCompanion services:")
        for companion in companions.values():
            state = companion.get("runtime_state") or ("ready" if companion.get("service_ready") else (
                "port conflict" if companion.get("port_occupied") else "stopped"
            ))
            print(f"  {companion.get('name')}: {state}")

    issues = report.get("issues", [])
    hints = report.get("hints", [])
    if issues:
        print("\nBlocking issues:")
        for issue in issues:
            print(f"  [ERROR] {issue.get('message')}")
            if issue.get("hint"):
                print(f"          Next: {issue['hint']}")
    else:
        print("\nBlocking issues: none")
    if hints:
        print("\nInformation:")
        for hint in hints:
            print(f"  [INFO] {hint.get('message')}")
    print("\nResult: " + ("BLOCKED" if issues else "READY"))
    return not issues


def print_startup_failure_hint():
    """Give an actionable next step after a bounded startup failure."""
    print("诊断建议: python launcher/start.py --doctor")
    print("机器可读诊断: python launcher/start.py --diagnose")
    print(f"启动日志: {launcher_log_path()}")


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
        return 1

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
            return 1
        except OSError as error:
            record_launcher_event("dependency_setup_error", module=module.get("name"), error=str(error))
            print(f"\nUnable to run dependency setup: {error}")
            print(f"Run manually in {module['cwd']}: {' '.join(module['setup'])}")
            return 1
        if result.returncode != 0:
            record_launcher_event("dependency_setup_failed", module=module.get("name"), returncode=result.returncode)
            print(f"\n❌ Setup 失败，请手动执行:")
            print(f"   cd {module['cwd']}")
            print(f"   {' '.join(module['setup'])}")
            return 1
        # Keep the in-memory menu state accurate during a legacy-menu
        # session. A successful first-run install must not be repeated every
        # time the user reopens the same compatibility module.
        module["needs_setup"] = False

    # Run the command
    print(f"执行: {' '.join(module['cmd'])}")
    print(f"工作目录: {module['cwd']}")
    print("-" * 50)
    print("按 Ctrl+C 停止\n")

    # Reuse an already healthy main workspace, while still ensuring that
    # companions declared by this module are available beside it.
    if module.get("url") and service_is_ready(module["url"]):
        companion_processes = start_companions(module, env)
        if companion_processes is None:
            return 1
        record_launcher_event("reuse_existing_service", module=module.get("name"), url=module["url"])
        print(f"浣跨敤宸茶繍琛岀殑涓绘湇鍔? {module['url']}")
        try:
            if open_browser:
                webbrowser.open(module["url"])
            if companion_processes:
                wait_for_existing_service(module["url"])
        except KeyboardInterrupt:
            print("\nLauncher stopped.")
        finally:
            for companion_process in companion_processes:
                terminate_process(companion_process)
        return 0

    companion_processes = start_companions(module, env)
    if companion_processes is None:
        return 1

    # A separately started frontend may already occupy the configured port.
    # Reuse it instead of launching a second strict-port dev server that exits
    # immediately and is then reported as a startup failure.
    if module.get("url") and service_is_ready(module["url"]):
        record_launcher_event("reuse_existing_service", module=module.get("name"), url=module["url"])
        print(f"使用已运行的主服务: {module['url']}")
        try:
            if open_browser:
                webbrowser.open(module["url"])
            if companion_processes:
                wait_for_existing_service(module["url"])
        except KeyboardInterrupt:
            print("\n已停止")
        finally:
            for companion_process in companion_processes:
                terminate_process(companion_process)
        return 0

    if module.get("url") and local_port_is_occupied(module["url"]):
        record_launcher_event("port_conflict", module=module.get("name"), url=module["url"])
        print(f"\nPort conflict: {module['url']} is already occupied by another service.")
        print("Stop the conflicting process or choose another development port, then retry.")
        print_startup_failure_hint()
        for companion_process in companion_processes:
            terminate_process(companion_process)
        return 1

    module_command_missing = False
    process = None
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
                print_startup_failure_hint()
                # Do not block forever when a child stays alive but never
                # becomes reachable. The finally block cleans up companions.
                terminate_process(process)
                return 1
            print(f"\n>>> 打开浏览器: {module['url']}")
            if open_browser:
                webbrowser.open(module["url"])

        process.wait()
        record_launcher_event("module_exit", module=module.get("name"), returncode=process.returncode)
        output_thread.join(timeout=2)
        return process.returncode or 0

    except KeyboardInterrupt:
        if process is not None:
            terminate_process(process)
        print("\n已停止")
    except FileNotFoundError as e:
        record_launcher_event("module_command_missing", module=module.get("name"), error=str(e))
        module_command_missing = True
        print(f"\n❌ 找不到命令: {e}")
        print(f"请确保已安装所需依赖")
    finally:
        for companion_process in companion_processes:
            terminate_process(companion_process)
        if module_command_missing:
            return 1


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
            # The configured workspace port identifies the unified frontend.
            # Do not mistake an unrelated HTTP service for EffiLife.
            parsed = urlparse(url)
            if parsed.port == workspace_port():
                body = response.read(65536).decode("utf-8", errors="replace").lower()
                return 'name="application-name" content="effilife"' in body
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

        companion_url = companion.get("url")
        if companion_url and local_port_is_occupied(companion_url):
            record_launcher_event(
                "companion_port_conflict",
                companion=companion.get("name"),
                url=companion_url,
            )
            print(f"\nPort conflict: {companion_url} is occupied by another service.")
            print("Stop the conflicting process or verify that the existing service is plan-helper, then retry.")
            print_startup_failure_hint()
            for started in managed:
                terminate_process(started)
            return None

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
            print_startup_failure_hint()
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


def wait_for_existing_service(url):
    """Keep launcher-owned companions alive beside an external frontend."""
    while service_is_ready(url):
        time.sleep(0.5)


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


def print_help():
    """Print the launcher command reference without starting any service."""
    print(
        "EffiLife launcher\n"
        "\n"
        "Usage: python launcher/start.py [option]\n"
        "\n"
        "Default:\n"
        "  Start the unified EffiLife workspace.\n"
        "\n"
        "Options:\n"
        "  --help, -h       Show this help and exit\n"
        "  --no-browser     Start without opening the browser\n"
        "  --diagnose       Print machine-readable launcher diagnostics\n"
        "  --doctor         Print a human-readable readiness report\n"
        "  --release-check  Validate desktop and mobile release configuration\n"
        "  --verify-bundle  Verify a release bundle path\n"
        "  --packaged       Require a packaged Tauri binary or built dist\n"
        "\nEnvironment:\n"
        "  EFFILIFE_WORKSPACE_PORT / EFFILIFE_TODOS_PORT / EFFILIFE_PLAN_HELPER_PORT\n"
        "                   Override development service ports (1024-65535)\n"
        "  --legacy-menu    Open the legacy module launcher\n"
        "  --version        Print the application version\n"
    )


def main():
    """Launch the unified workspace by default.

    The old module menu remains available explicitly through
    ``--legacy-menu`` for migration and debugging.
    """
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return
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
    if "--doctor" in sys.argv:
        if not print_doctor_report(collect_diagnostics(modules)):
            raise SystemExit(1)
        return
    if "--unified" in sys.argv or "--legacy-menu" not in sys.argv:
        result = run_module("1", modules, open_browser="--no-browser" not in sys.argv)
        if result:
            raise SystemExit(result)
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
