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


def find_npm():
    """Find npm executable, handling Windows quirks"""
    if os.name == "nt":
        # Windows: try npm.cmd first
        for name in ["npm.cmd", "npm"]:
            path = shutil.which(name)
            if path:
                return path
    else:
        path = shutil.which("npm")
        if path:
            return path
    return None


def check_dependencies(module):
    """Check if required dependencies are available"""
    cmd = module["cmd"]
    if not cmd:
        return True, None

    exe = cmd[0]

    if exe == "npm":
        npm_path = find_npm()
        if not npm_path:
            return False, "Node.js/npm 未安装或不在 PATH 中\n请从 https://nodejs.org 下载安装"
        # Replace "npm" with full path
        module["cmd"][0] = npm_path
        if module.get("setup"):
            module["setup"][0] = npm_path

    elif exe == sys.executable:
        # Python should always be available
        pass

    return True, None


MODULES = {
    "1": {
        "name": "time-helper",
        "desc": "时间记录与统计 (v1.2.0)",
        "cmd": ["npm", "run", "dev"],
        "cwd": BASE_DIR / "time-helper" / "desk",
        "url": "http://localhost:1420",
        "setup": ["npm", "install"],
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
        "cmd": ["npm", "run", "dev"],
        "cwd": BASE_DIR / "to-dos" / "ui",
        "url": "http://localhost:1421",
        "setup": ["npm", "install"],
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


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_menu():
    clear()
    print("=" * 50)
    print("  EffLife 效率工具集 - 统一启动器")
    print("=" * 50)
    print()

    for key, module in MODULES.items():
        print(f"  [{key}] {module['name']}")
        print(f"      {module['desc']}")
        print()

    print("  [0] 退出")
    print()


def run_module(choice):
    if choice == "0":
        print("再见！")
        sys.exit(0)

    if choice not in MODULES:
        print("无效选择，请重试")
        return

    module = MODULES[choice]
    print(f"\n启动 {module['name']}...")

    # Check dependencies
    ok, err = check_dependencies(module)
    if not ok:
        print(f"\n❌ 依赖检查失败:\n{err}")
        return

    # Setup if needed
    if module.get("setup"):
        print(f"首次运行，执行 setup: {' '.join(module['setup'])}")
        result = subprocess.run(module["setup"], cwd=module["cwd"], shell=True)
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
        subprocess.run(module["cmd"], cwd=module["cwd"])
    except KeyboardInterrupt:
        print("\n已停止")
    except FileNotFoundError as e:
        print(f"\n❌ 找不到命令: {e}")
        print(f"请确保已安装所需依赖")


def main():
    while True:
        show_menu()
        choice = input("请选择 [0-6]: ").strip()
        run_module(choice)
        input("\n按 Enter 继续...")


if __name__ == "__main__":
    main()
