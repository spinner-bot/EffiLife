"""
    ============ test_api.py ============
    to-dos 模块 API 测试脚本
        by spinner-bot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src import TodoAPI, Priority, TodoStatus, PRIORITY_LABELS, STATUS_LABELS


def run_tests():
    print("=" * 50)
    print("  to-dos API 测试")
    print("=" * 50)

    api = TodoAPI()
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ===== 1. 创建 =====
    print("\n--- 创建测试 ---")
    r = api.create_todo(title="测试: 写文档", priority="important", category="work")
    check("创建普通任务", r["success"])
    id1 = r["data"]["id"]

    r = api.create_todo(
        title="测试: 紧急任务",
        priority="urgent-important",
        category="work",
        deadline="2026-09-19T18:00:00",
        tags=["紧急", "文档"],
    )
    check("创建紧急任务", r["success"])
    id2 = r["data"]["id"]

    r = api.create_todo(title="测试: 学习任务", priority="normal", category="study")
    check("创建学习任务", r["success"])
    id3 = r["data"]["id"]

    r = api.create_todo(title="测试: 买菜", priority="normal", category="life")
    check("创建生活任务", r["success"])
    id4 = r["data"]["id"]

    # 创建失败
    r = api.create_todo(title="")
    check("空标题应失败", not r["success"])

    r = api.create_todo(title="test", priority="invalid")
    check("无效优先级应失败", not r["success"])

    # ===== 2. 列表查询 =====
    print("\n--- 列表查询测试 ---")
    r = api.list_todos()
    check("获取全部列表", r["success"] and r["data"]["total"] >= 4)

    r = api.list_todos(status="pending")
    check("按状态筛选(pending)", r["success"] and r["data"]["total"] >= 4)

    r = api.list_todos(priority="urgent-important")
    check("按优先级筛选", r["success"] and r["data"]["total"] >= 1)

    r = api.list_todos(category="work")
    check("按分类筛选(work)", r["success"] and r["data"]["total"] >= 2)

    # ===== 3. 获取单个 =====
    print("\n--- 获取详情测试 ---")
    r = api.get_todo(id1)
    check("获取存在的任务", r["success"] and r["data"]["title"] == "测试: 写文档")

    r = api.get_todo("nonexistent")
    check("获取不存在的任务", not r["success"])

    # ===== 4. 更新 =====
    print("\n--- 更新测试 ---")
    r = api.update_todo(id1, description="更新后的描述", priority="urgent")
    check("更新描述和优先级", r["success"] and r["data"]["description"] == "更新后的描述")

    # ===== 5. 状态操作 =====
    print("\n--- 状态操作测试 ---")
    r = api.complete_todo(id1)
    check("完成任务", r["success"] and r["data"]["status"] == "completed")

    r = api.cancel_todo(id4)
    check("取消任务", r["success"] and r["data"]["status"] == "cancelled")

    # ===== 6. 子任务 =====
    print("\n--- 子任务测试 ---")
    r = api.add_subtask(id2, "编写目录")
    check("添加子任务", r["success"])
    sub_id = r["data"]["id"]

    r = api.add_subtask(id2, "编写内容")
    check("添加第二个子任务", r["success"])

    r = api.toggle_subtask(id2, sub_id)
    check("切换子任务状态", r["success"])

    # 验证子任务状态
    r = api.get_todo(id2)
    subtasks = r["data"]["subtasks"]
    check("子任务状态已更新", any(s["completed"] for s in subtasks))

    # ===== 7. 搜索 =====
    print("\n--- 搜索测试 ---")
    r = api.list_todos(search="文档")
    check("搜索关键词(文档)", r["success"] and r["data"]["total"] >= 1)

    r = api.list_todos(search="不存在的关键词xyz")
    check("搜索无结果", r["success"] and r["data"]["total"] == 0)

    # ===== 8. 逾期 =====
    print("\n--- 逾期测试 ---")
    r = api.get_overdue()
    check("获取逾期待办", r["success"] and len(r["data"]) >= 1)

    # ===== 9. 今日 =====
    print("\n--- 今日测试 ---")
    r = api.get_today()
    check("获取今日待办", r["success"])

    # ===== 10. 统计 =====
    print("\n--- 统计测试 ---")
    r = api.get_stats()
    check("获取统计", r["success"])
    stats = r["data"]
    check("统计包含总数", stats["total"] >= 4)
    check("统计包含完成率", "completion_rate" in stats)

    # ===== 11. 分类 =====
    print("\n--- 分类测试 ---")
    r = api.list_categories()
    check("列出分类", r["success"] and len(r["data"]) >= 4)

    r = api.create_category(name="测试分类", color="#FF0000", icon="test")
    check("创建分类", r["success"])
    cat_id = r["data"]["id"]

    r = api.update_category(cat_id, name="更新后分类")
    check("更新分类", r["success"] and r["data"]["name"] == "更新后分类")

    r = api.delete_category(cat_id)
    check("删除分类", r["success"])

    # ===== 12. 批量操作 =====
    print("\n--- 批量操作测试 ---")
    # 创建几个用于批量操作的任务
    ids = []
    for i in range(3):
        r = api.create_todo(title=f"批量测试-{i}")
        ids.append(r["data"]["id"])

    r = api.batch_action("complete", ids[:2])
    check("批量完成", r["success"] and r["data"]["success"] == 2)

    # ===== 13. 跨模块接口 =====
    print("\n--- 跨模块接口测试 ---")
    r = api.create_todo_for_plan("PLAN-001", title="计划关联任务")
    check("为计划创建任务", r["success"])
    plan_todo_id = r["data"]["id"]

    r = api.get_todos_by_plan("PLAN-001")
    check("按计划查询任务", r["success"] and r["data"]["total"] >= 1)

    r = api.track_time(plan_todo_id, 30)
    check("记录时间", r["success"] and r["data"]["time_spent"] == 30)

    # ===== 14. 删除(归档) =====
    print("\n--- 删除(归档)测试 ---")
    r = api.delete_todo(id3)
    check("删除(归档)任务", r["success"])

    r = api.get_todo(id3)
    check("已归档任务状态为archived", r["success"] and r["data"]["status"] == "archived")

    # ===== 结果汇总 =====
    print("\n" + "=" * 50)
    total = passed + failed
    print(f"  测试结果: {passed}/{total} 通过, {failed} 失败")
    print("=" * 50)

    # 清理测试数据
    print("\n  清理测试数据...")
    all_r = api.list_todos()
    if all_r["success"]:
        for item in all_r["data"]["items"]:
            api.delete_todo(item["id"])
    print("  清理完成")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
