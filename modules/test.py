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

"""
    ====== modules/test.py ======
    存放各类测试函数.
        by spinner-bot
"""
import shutil
import subprocess
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


def _build_plan_data(index):
    """
    构造用于测试的 Plan 数据，内容与题目示例基本一致。
    """
    return {
        "head": {
            "index": index,
            "name": "初始计划",
            "date": [2026, 8, 4]
        },
        "main": [
            {
                "name": "zzlab-pre（实验室招新）",
                "info": "",
                "plan": [
                    None,
                    {"is_active": True, "content": "建好仓库并设定连接", "t_m": 15 / 6},
                    {"is_active": True, "content": "学习C++面向对象编程", "t_m": 45 / 6},
                    {"is_active": True, "content": "完成Software_A1题目", "t_m": 30 / 6},
                    {"is_active": True, "content": "完成Software_A2题目", "t_m": 30 / 6},
                    {"is_active": True, "content": "准备Software_B相关环境，需要理解相应背景", "t_m": 40 / 6}
                ],
                "group": {
                    "2_4": {"title": "组", "description": "按序完成题目即可"}
                }
            },
            {
                "name": "mm-OPD（ICLR 2027）",
                "info": "",
                "plan": [
                    None,
                    {"is_active": True, "content": "复习OPD相关内容", "t_m": 75 / 6},
                    {"is_active": True, "content": "阅读拆解好的flow-OPD相关论文，并暂时不做复现", "t_m": 75 / 6},
                    {"is_active": True, "content": "依次阅读所有OPD论文，并做idea整理，完成阅读笔记", "t_m": 210 / 6},
                    {"is_active": True, "content": "基于以上所有工作，总结idea发掘视角，并给出书面理解", "t_m": 20 / 6},
                    {"is_active": True, "content": "试着提出3个以上idea，并做前期论证，形成文档", "t_m": 60 / 6}
                ],
                "group": {}
            }
        ],
        "log": [
            {"day": 1, "plan": "base", "time": [8, 99], "content": "本地工作流准备就绪"},
            {"day": 1, "plan": "A1", "time": [9, 99], "content": "任务完成。基本环境准备就绪"},
            {"day": 1, "plan": "base", "time": [10, 45], "content": "finished the plan of the day"},
            {"day": 1, "plan": "B1", "time": [10, 58], "content": "开始复习"},
            {"day": 1, "plan": "B1", "time": [11, 33], "content": "完成OPD模块复习，进入MM模块"},
            {"day": 1, "plan": "B1", "time": [12, 99], "content": "快速完成MM模块，进入mm-OPD模块"},
            {"day": 1, "plan": "B1", "time": [13, 25], "content": "任务完成。基本达成了复习目标，尽管内容并未100%覆盖"},
            {"day": 1, "plan": "base", "time": [14, 0], "content": "环境变更。本任务清单终止，我需要快速处理其他事项。"}
        ]
    }


def base2_test():
    """
    测试2：注册计划 → 保存JSON → 转换文本 → 打开文本 → 删除文件 → 释放索引。
    索引冲突处理：12 → 10012 → 100012 ...（即 10^4 + 12, 10^5 + 12, ...）
    """
    print("测试2启动。来源：main\n")

    # 1. 确定可用索引（12, 10012, 100012...）
    candidate = 12
    power = 4
    while candidate in p.Plan.registry:
        candidate = 10 ** power + 12
        power += 1

    json_path = None
    txt_path = None

    # 2. 创建 Plan 实例并覆盖数据
    try:
        plan = p.Plan(candidate)          # 自动注册
        plan.plan = _build_plan_data(candidate)   # 替换为预定义数据
        p.Plan.registry[candidate] = plan # 确保注册表指向同一对象
        print(f"✅ 计划实例已创建，索引：{candidate}")

        # 3. 标记任务完成（测试 finish 功能）
        print("正在标记任务完成...")
        # 完成 A1：建好仓库并设定连接，完成时间 9am（模糊时间）
        res1 = plan.finish("A1", 1, (9, 99))
        if res1 == -1:
            print("⚠️ finish A1 失败")
        else:
            print("✅ 任务 A1 已完成")

        # 完成 B1：复习OPD相关内容，完成时间 13:25（精确时间）
        res2 = plan.finish("B1", 1, (13, 25))
        if res2 == -1:
            print("⚠️ finish B1 失败")
        else:
            print("✅ 任务 B1 已完成")

        # 4. 保存为 JSON
        json_path = f"plan_{candidate}.json"
        plan.save(json_path)
        print(f"✅ JSON 已保存：{json_path}")

        # 5. 转换为文本
        txt_path = f"plan_{candidate}.txt"
        tx.convert(json_path, txt_path)
        print(f"✅ 文本已生成：{txt_path}")

        # 6. 打开文本文件，等待用户关闭（Windows 记事本）
        print("正在用记事本打开文本文件，请查看...")
        subprocess.Popen(['notepad', txt_path]).wait()
        print("记事本已关闭。")

        # 7. 强制删除两个文件（失败则重试）
        print("开始清理测试文件...")
        for target, is_dir in [(Path(json_path), False), (Path(txt_path), False)]:
            while True:
                try:
                    if target.exists():
                        target.unlink()
                    break
                except Exception as e:
                    input(f"[测试2|复原程序] 清理 {target} 失败: {e} 请按回车重试...")

        # 8. 释放索引（从注册表移除）
        plan.delete()
        print(f"✅ 索引 {candidate} 已释放。")

    except Exception as e:
        # 异常时也尽量清理文件和注册表
        for f in [json_path, txt_path]:
            if f:
                try:
                    if Path(f).exists():
                        Path(f).unlink()
                except:
                    pass
        if candidate in p.Plan.registry:
            p.Plan.registry.pop(candidate, None)
        print(f"❌ 测试2出现错误：{e}")
        raise

    print("[测试2：全部完成] 测试结论未知。测试程序已退出，所有测试文件已被清理")


def t(id):
    if id == 1:
        base1_test()
    elif id == 2:
        base2_test()
    else:
        print(f"未知测试 ID: {id}")