#!/usr/bin/env python3
"""
EffLife 效率工具集 - 统一启动器
"""

import os
import sys
import subprocess
import webbrowser
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

# Custom Node.js location (F drive)
CUSTOM_NODE_DIR = Path("F:/dev-tools/node")


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


def get_time_helper_cmd():
    """Get command for time-helper, preferring compiled exe"""
    # Check for compiled exe first
    exe_paths = [
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe",
        BASE_DIR / "time-helper" / "desk" / "src-tauri" / "target" / "debug" / "efflife-desk.exe",
    ]
    for exe_path in exe_paths:
        if exe_path.exists():
            return [str(exe_path)], None, None  # cmd, url, setup

    # Fall back to npm dev server
    npm = find_npm()
    if npm:
        return [npm, "run", "dev"], "http://localhost:1420", [npm, "install"]
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
            "name": "time-helper",
            "desc": "时间记录与统计 (v1.2.0)",
            "cmd": th_cmd,
            "cwd": BASE_DIR / "time-helper" / "desk",
            "url": th_url,
            "setup": th_setup,
        },
        "2": {
            "name": "plan-helper",
            "desc": "计划制定与日程管理 (v0.3.0)",
            "cmd": [sys.executable, "-m", "web.server"],
            "cwd": BASE_DIR / "plan-helper",
            "url": "http://127.0.0.1:8765",
            "setup": None,
        },
        "3": {
            "name": "to-dos",
            "desc": "任务清单与待办追踪 (v0.4.0)",
            "cmd": [sys.executable, "main.py"],
            "cwd": BASE_DIR / "to-dos",
            "url": None,
            "setup": None,
        },
        "4": {
            "name": "to-dos (Web)",
            "desc": "待办事项 Web 界面",
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

    # Mark modules that aren't available
    for key, mod in modules.items():
        if mod["cmd"] is None:
            mod["available"] = False
        else:
            mod["available"] = True

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

    # Prepare environment with custom Node.js path
    env = os.environ.copy()
    if os.name == "nt" and CUSTOM_NODE_DIR.exists():
        env["PATH"] = str(CUSTOM_NODE_DIR) + os.pathsep + env.get("PATH", "")

    # Setup if needed
    if module.get("setup"):
        print(f"首次运行，执行 setup: {' '.join(module['setup'])}")
        result = subprocess.run(module["setup"], cwd=module["cwd"], shell=True, env=env)
        if result.returncode != 0:
            print(f"\n❌ Setup 失败，请手动执行:")
            print(f"   cd {module['cwd']}")
            print(f"   {' '.join(module['setup'])}")
            return

    # Open browser if has URL
    if module.get("url"):
        print(f"将在浏览器打开: {module['url']}")
        webbrowser.open(module["url"])

    # Run the command
    print(f"执行: {' '.join(module['cmd'])}")
    print(f"工作目录: {module['cwd']}")
    print("-" * 50)
    print("按 Ctrl+C 停止\n")

    try:
        # On Windows, use shell=True to inherit full PATH
        use_shell = os.name == "nt"
        subprocess.run(module["cmd"], cwd=module["cwd"], shell=use_shell, env=env)
    except KeyboardInterrupt:
        print("\n已停止")
    except FileNotFoundError as e:
        print(f"\n❌ 找不到命令: {e}")
        print(f"请确保已安装所需依赖")


def main():
    modules = build_modules()
    while True:
        show_menu(modules)
        choice = input("请选择 [0-6]: ").strip()
        run_module(choice, modules)
        input("\n按 Enter 继续...")


if __name__ == "__main__":
    main()
