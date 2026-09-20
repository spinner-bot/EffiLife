"""
    ============ 跨模块集成示例 ============
    to-dos 与 plan-helper / time-helper 集成示例

    展示如何使用预留的跨模块接口
"""

import sys
from pathlib import Path

# 确保可以导入 to-dos 模块的 src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import TodoAPI


def demo_plan_integration():
    """与 plan-helper 集成示例"""
    print("\n" + "=" * 50)
    print("  与 plan-helper 集成示例")
    print("=" * 50)

    api = TodoAPI()

    # 1. 为计划创建关联待办
    plan_id = "PLAN-001"
    print(f"\n1. 为计划 {plan_id} 创建关联待办...")

    r = api.create_todo_for_plan(
        plan_id=plan_id,
        title="完成计划的第一步",
        priority="important",
        category="work",
        description="这是与 plan-helper 关联的待办事项",
    )

    if r["success"]:
        todo_id = r["data"]["id"]
        print(f"   [OK] 创建成功: {todo_id}")
        print(f"   关联计划: {r['data']['related_plan_id']}")
    else:
        print(f"   [FAIL] 创建失败: {r['message']}")
        return

    # 2. 查询计划的所有待办
    print(f"\n2. 查询计划 {plan_id} 的所有待办...")
    r = api.get_todos_by_plan(plan_id)

    if r["success"]:
        items = r["data"]["items"]
        print(f"   共 {len(items)} 个关联待办:")
        for item in items:
            print(f"   - [{item['status']}] {item['title']}")
    else:
        print(f"   [FAIL] 查询失败: {r['message']}")

    # 3. 清理
    api.delete_todo(todo_id)
    print(f"\n3. 已清理测试数据")


def demo_time_integration():
    """与 time-helper 集成示例"""
    print("\n" + "=" * 50)
    print("  与 time-helper 集成示例")
    print("=" * 50)

    api = TodoAPI()

    # 1. 创建待办
    r = api.create_todo(title="专注工作 25 分钟", category="work")
    if not r["success"]:
        print(f"创建失败: {r['message']}")
        return
    todo_id = r["data"]["id"]
    print(f"\n1. 创建待办: {todo_id}")

    # 2. 记录时间（模拟番茄钟）
    print("\n2. 记录专注时间...")
    durations = [25, 5, 25, 5, 25]  # 番茄钟模式

    for i, duration in enumerate(durations):
        r = api.track_time(todo_id, duration)
        if r["success"]:
            total = r["data"]["time_spent"]
            kind = "工作" if duration == 25 else "休息"
            print(f"   第 {i+1} 个番茄 ({kind} {duration}分钟) - 累计: {total} 分钟")

    # 3. 查看最终状态
    r = api.get_todo(todo_id)
    if r["success"]:
        print(f"\n3. 最终状态:")
        print(f"   预估时间: {r['data'].get('time_estimate', '未设置')} 分钟")
        print(f"   实际花费: {r['data'].get('time_spent', 0)} 分钟")

    # 4. 清理
    api.delete_todo(todo_id)
    print(f"\n4. 已清理测试数据")


def demo_export_import():
    """数据导入/导出示例"""
    print("\n" + "=" * 50)
    print("  数据导入/导出示例")
    print("=" * 50)

    api = TodoAPI()

    # 1. 创建一些数据
    print("\n1. 创建测试数据...")
    for i in range(3):
        api.create_todo(title=f"导出测试-{i}", tags=["测试"])

    # 2. 导出为 JSON
    print("\n2. 导出 JSON...")
    r = api.export_data(format="json")
    if r["success"]:
        json_data = r["data"]["data"]
        print(f"   JSON 长度: {len(json_data)} 字符")
        print(f"   前 200 字符: {json_data[:200]}...")
    else:
        print(f"   [FAIL] 导出失败: {r['message']}")

    # 3. 导出为 CSV
    print("\n3. 导出 CSV...")
    r = api.export_data(format="csv")
    if r["success"]:
        csv_data = r["data"]["data"]
        lines = csv_data.split('\n')
        print(f"   CSV 行数: {len(lines)}")
        print(f"   标题行: {lines[0]}")
    else:
        print(f"   [FAIL] 导出失败: {r['message']}")

    # 4. 创建备份
    print("\n4. 创建自动备份...")
    r = api.create_backup()
    if r["success"]:
        print(f"   备份路径: {r['data']['path']}")
    else:
        print(f"   [FAIL] 备份失败: {r['message']}")

    # 5. 列出备份
    r = api.list_backups()
    if r["success"]:
        print(f"   现有备份: {len(r['data'])} 个")

    # 6. 清理
    print("\n5. 清理测试数据...")
    all_r = api.list_todos()
    if all_r["success"]:
        for item in all_r["data"]["items"]:
            if "导出测试" in item["title"]:
                api.delete_todo(item["id"])
    print("   清理完成")


def demo_new_features():
    """v0.3.0 新功能演示"""
    print("\n" + "=" * 50)
    print("  v0.3.0 新功能演示")
    print("=" * 50)

    api = TodoAPI()

    # 1. 创建带新字段的待办
    print("\n1. 创建待办（含重复、提醒、备注）...")
    r = api.create_todo(
        title="每日站会",
        priority="important",
        category="work",
        deadline="2026-09-25T09:30:00",
    )

    if r["success"]:
        todo_id = r["data"]["id"]
        print(f"   创建成功: {todo_id}")

        # 2. 更新新字段
        print("\n2. 更新重复类型和提醒天数...")
        r = api.update_todo(
            todo_id,
            recurrence="daily",
            deadline_warning_days=1,
            notes="## 每日站会议程\n- 昨天完成了什么\n- 今天计划做什么\n- 有什么阻碍",
        )
        if r["success"]:
            print(f"   重复: {r['data']['recurrence']}")
            print(f"   提醒: 提前 {r['data']['deadline_warning_days']} 天")
            print(f"   备注: {r['data']['notes'][:30]}...")

        # 3. 置顶
        print("\n3. 切换置顶状态...")
        r = api.toggle_pin(todo_id)
        if r["success"]:
            print(f"   已置顶: {r['data']['pinned']}")

        # 4. 查看即将到期
        print("\n4. 查询即将到期待办...")
        r = api.get_warning_todos()
        if r["success"]:
            print(f"   需要提醒: {len(r['data'])} 个")

        # 清理
        api.delete_todo(todo_id)
        print("\n5. 已清理测试数据")


def main():
    """运行所有集成示例"""
    print("=" * 50)
    print("  to-dos v0.3.0 跨模块集成示例")
    print("=" * 50)

    demo_plan_integration()
    demo_time_integration()
    demo_export_import()
    demo_new_features()

    print("\n" + "=" * 50)
    print("  所有示例运行完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
