"""
    ============ plan-helper ============
    [repository] https://github.com/spinner-bot/plan-helper
    [description] 暂时还没写……
        by spinner-bot
"""

import modules as m
import shutil
from pathlib import Path

def rtest1():
    print("测试1启动。来源：main\n")
    m.p.run_test1()
    m.tx.run_test2()
    while not input("输入ph以退出main:") in ("ph", "Ph", "pH", "PH"):
        m.wz.main()
    for target, is_dir in [(Path("test_plan_data.json"), False), (Path("output"), True)]:
        while True:
            try:
                if target.exists():
                    if is_dir:
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                break
            except Exception as e:
                input(f"[测试1|复原程序]清理 {target} 失败: {e} 请重试...")
    print("完成")

    if __name__ == "__main__":
        rtest1()