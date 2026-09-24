#!/usr/bin/env python3
"""
EffLife 效率工具集 - 统一启动器
"""

import os
import sys
import subprocess
import webbrowser
import shutil
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Custom Node.js location (F drive)
CUSTOM_NODE_DIR = Path(os.environ.get("EFFILIFE_NODE_DIR", "F:/dev-tools/node"))


def find_npm():
    """Find npm executable, checking custom location first"""
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


def node_environment():
    """Build an environment that can run npm and its child processes."""
    env = os.environ.copy()
    if CUSTOM_NODE_DIR.exists():
        env["PATH"] = str(CUSTOM_NODE_DIR) + os.pathsep + env.get("PATH", "")
    return env


def dependencies_ready(cwd):
    """Avoid running npm install on every launch."""
    return (Path(cwd) / "node_modules").is_dir()


def get_time_helper_cmd():
    """Get command for time-helper, prefer dev mode for latest features"""
    npm = find_npm()
    if npm:
        # Dev mode - shows latest code changes
        return [npm, "run", "dev"], "http://localhost:1420", [npm, "install"]

    # Fall back to compiled exe
    exe_paths = [
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe",
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / "debug" / "efflife-desk.exe",
    ]
    for exe_path in exe_paths:
        if exe_path.exists():
            return [str(exe_path)], None, None  # cmd, url, setup
    return None, None, None


def get_todos_web_cmd():
    """Get command for to-dos web, checking for npm"""
    npm = find_npm()
    if npm:
        return [npm, "run", "dev"], "http://localhost:1421", [npm, "install"]
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
                "cmd": [sys.executable, "web/server.py"],
                "cwd": BASE_DIR / "plan-helper",
                "url": "http://127.0.0.1:8765",
            }],
        },
        "2": {
            "name": "plan-helper（兼容入口）",
            "desc": "旧版计划编辑器，仅用于迁移与调试",
            "cmd": [sys.executable, "web/server.py"],
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

    node_available = bool(find_node() or find_npm())

    # Mark modules that aren't available
    for key, mod in modules.items():
        if mod["cmd"] is None:
            mod["available"] = False
        else:
            mod["available"] = True
        if mod["setup"] and not node_available:
            mod["available"] = False
            mod["unavailable_reason"] = "未找到 Node.js/npm"
        mod["needs_setup"] = bool(mod["setup"] and not dependencies_ready(mod["cwd"]))

    return modules


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_menu(modules):
    clear()
    print("=" * 50)
    print("  EffLife 效率工具集 - 统一启动器")
    print("=" * 50)
    print()

    for key, module in modules.items():
        status = "" if module["available"] else " [未就绪]"
        print(f"  [{key}] {module['name']}{status}")
        print(f"      {module['desc']}")
        print()

    print("  [0] 退出")
    print()


def run_module(choice, modules):
    if choice == "0":
        print("再见！")
        sys.exit(0)

    if choice not in modules:
        print("无效选择，请重试")
        return

    module = modules[choice]

    if not module["available"]:
        print(f"\n❌ {module['name']} 未就绪")
        if "npm" in str(module.get("setup", "")):
            print("请安装 Node.js: https://nodejs.org")
        return

    print(f"\n启动 {module['name']}...")

    env = node_environment()

    # Setup if needed
    if module.get("setup") and module.get("needs_setup"):
        print(f"首次运行，执行 setup: {' '.join(module['setup'])}")
        result = subprocess.run(module["setup"], cwd=module["cwd"], shell=False, env=env)
        if result.returncode != 0:
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

    try:
        process = subprocess.Popen(
            module["cmd"],
            cwd=module["cwd"],
            shell=False,
            env=env,
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
            if wait_for_service(process, module["url"]):
                print(f"\n>>> 打开浏览器: {module['url']}")
                webbrowser.open(module["url"])

        process.wait()
        output_thread.join(timeout=2)

    except KeyboardInterrupt:
        print("\n已停止")
    except FileNotFoundError as e:
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
            return response.status < 500
    except (OSError, URLError):
        return False


def terminate_process(process):
    """Stop a process started by the launcher without affecting external services."""
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def start_companions(module, env):
    """Start only companion services not already provided by the user."""
    managed = []
    for companion in module.get("companions", []):
        if companion.get("url") and service_is_ready(companion["url"]):
            print(f"使用已运行的 {companion['name']}: {companion['url']}")
            continue

        print(f"启动配套服务: {companion['name']}")
        process = subprocess.Popen(
            companion["cmd"],
            cwd=companion["cwd"],
            shell=False,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        output_thread = threading.Thread(target=stream_output, args=(process,), daemon=True)
        output_thread.start()
        if companion.get("url") and not wait_for_service(process, companion["url"]):
            terminate_process(process)
            for started in managed:
                terminate_process(started)
            return None
        managed.append(process)
    return managed


def wait_for_service(process, url, timeout=30):
    """Wait for an HTTP service instead of trusting a particular log format."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            print(f"\n❌ 服务提前退出，退出码: {process.returncode}")
            return False
        try:
            with urlopen(url, timeout=1) as response:
                if response.status < 500:
                    return True
        except (OSError, URLError):
            time.sleep(0.25)
    print(f"\n⚠️ 服务在 {timeout} 秒内未响应，请手动打开: {url}")
    return False


def main():
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


if __name__ == "__main__":
    main()
