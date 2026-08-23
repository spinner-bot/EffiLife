"""
    ====== modules/test.py ======
    存放各类测试函数.
        by spinner-bot
"""
import shutil
from pathlib import Path

# 使用相对导入直接获取需要的子模块，避免循环导入
from . import plan as p
from . import text as tx
from . import wizard as wz


def base1_test():
    print(f"测试1启动。来源：main\n")
    p.run_test1()
    tx.run_test2()
    wz.main()
    while not input("输入ph以退出main:") in ("ph", "Ph", "pH", "PH"):
        wz.main()
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
                input(f"[测试1|复原程序] 清理 {target} 失败: {e} 请重试...")
    print("[测试1：全部完成] 测试结论未知。测试程序已退出，所有测试文件已被清理")

def t(id):
    if id == 1:
        base1_test()