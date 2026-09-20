"""
    ============ test_v030.py ============
    to-dos v0.3.0 功能测试
    测试新增的导出/导入、重复任务、备份等功能
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src import TodoAPI, Priority, TodoStatus, RecurrenceType
from src.export import TodoExporter, TodoImporter, AutoBackup
from src.types import Todo, Category


def run_tests():
    print("=" * 50)
    print("  to-dos v0.3.0 功能测试")
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

    # ===== 1. 新字段测试 =====
    print("\n--- 1. 新字段测试 ---")

    r = api.create_todo(
        title="测试: 重复任务",
        priority="important",
        category="work",
    )
    check("创建待办", r["success"])
    todo_id = r["data"]["id"]
    check("默认 recurrence 为 none", r["data"]["recurrence"] == "none")
    check("默认 deadline_warning_days 为 3", r["data"]["deadline_warning_days"] == 3)
    check("默认 sort_order 为 0", r["data"]["sort_order"] == 0)
    check("默认 pinned 为 false", r["data"]["pinned"] == False)

    # 测试置顶
    r = api.toggle_pin(todo_id)
    check("切换置顶", r["success"] and r["data"]["pinned"] == True)

    r = api.toggle_pin(todo_id)
    check("取消置顶", r["success"] and r["data"]["pinned"] == False)

    # 更新重复类型
    r = api.update_todo(todo_id, recurrence="daily")
    check("更新重复类型", r["success"])

    # 更新截止提醒天数
    r = api.update_todo(todo_id, deadline_warning_days=7)
    check("更新截止提醒天数", r["success"])

    # ===== 2. 导出测试 =====
    print("\n--- 2. 导出测试 ---")

    # 导出 JSON
    r = api.export_data(format="json")
    check("导出 JSON", r["success"])
    exported = json.loads(r["data"]["data"])
    check("JSON 包含 version", exported.get("version") == "0.3.0")
    check("JSON 包含 todos", "todos" in exported and len(exported["todos"]) > 0)
    check("JSON 包含 categories", "categories" in exported)

    # 导出 CSV
    r = api.export_data(format="csv")
    check("导出 CSV", r["success"])
    csv_data = r["data"]["data"]
    check("CSV 包含标题行", "ID" in csv_data)
    check("CSV 包含数据行", "测试: 重复任务" in csv_data)

    # 文件导出测试
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        from src.export import TodoExporter
        exporter = TodoExporter(api._storage)
        result = exporter.export_json(temp_path)
        check("JSON 文件导出", os.path.exists(temp_path))

        # 验证文件内容
        with open(temp_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        check("JSON 文件内容正确", "todos" in file_data)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    # ===== 3. 导入测试 =====
    print("\n--- 3. 导入测试 ---")

    # JSON 字符串导入
    import_data = json.dumps({
        "version": "0.3.0",
        "todos": [
            {
                "id": "TODO-TEST-0001",
                "title": "导入测试任务",
                "created_at": "2026-09-20T10:00:00",
                "updated_at": "2026-09-20T10:00:00",
                "priority": "important",
                "category": "work",
                "status": "pending",
                "tags": ["测试"],
                "subtasks": [],
            }
        ],
        "categories": [],
    })

    r = api.import_data(import_data, format="json", merge=True)
    check("JSON 导入", r["success"] and r["data"]["count"] == 1)

    # 验证导入的数据
    r = api.get_todo("TODO-TEST-0001")
    check("导入数据可查询", r["success"] and r["data"]["title"] == "导入测试任务")

    # 无效 JSON 导入
    r = api.import_data("not valid json", format="json")
    check("无效 JSON 导入失败", not r["success"])

    # 空数据导入
    r = api.import_data('{"invalid": true}', format="json")
    check("缺少 todos 字段导入失败", not r["success"])

    # ===== 4. 备份测试 =====
    print("\n--- 4. 备份测试 ---")

    # 创建备份
    r = api.create_backup()
    check("创建备份", r["success"])
    backup_path = r["data"]["path"]
    check("备份文件存在", os.path.exists(backup_path))

    # 列出备份
    r = api.list_backups()
    check("列出备份", r["success"] and len(r["data"]) >= 1)

    # ===== 5. 排序测试 =====
    print("\n--- 5. 排序测试 ---")

    # 创建多个待办测试排序
    ids = []
    for i in range(3):
        r = api.create_todo(title=f"排序测试-{i}")
        ids.append(r["data"]["id"])

    # 自定义排序
    r = api.reorder(ids[::-1])  # 反转顺序
    check("自定义排序", r["success"])

    # ===== 6. 边界测试 =====
    print("\n--- 6. 边界测试 ---")

    # 空标题
    r = api.create_todo(title="")
    check("空标题应失败", not r["success"])

    r = api.create_todo(title="   ")
    check("空白标题应失败", not r["success"])

    # 特殊字符标题
    r = api.create_todo(title="<script>alert('xss')</script>")
    check("特殊字符标题", r["success"])

    # 超长标题
    r = api.create_todo(title="x" * 500)
    check("超长标题", r["success"])

    # 无效 ID 查询
    r = api.get_todo("INVALID-ID")
    check("无效 ID 查询", not r["success"])

    # 无效操作
    r = api.batch_action("invalid_action", ["some-id"])
    check("无效批量操作", not r["success"])

    # 空列表批量操作
    r = api.batch_action("complete", [])
    check("空列表批量操作", not r["success"])

    # ===== 7. RecurrenceType 测试 =====
    print("\n--- 7. RecurrenceType 测试 ---")

    check("NONE 枚举值", RecurrenceType.NONE.value == "none")
    check("DAILY 枚举值", RecurrenceType.DAILY.value == "daily")
    check("WEEKLY 枚举值", RecurrenceType.WEEKLY.value == "weekly")
    check("MONTHLY 枚举值", RecurrenceType.MONTHLY.value == "monthly")

    # Todo 的 needs_warning 方法
    todo = Todo(
        id="test", title="test", created_at="2026-01-01", updated_at="2026-01-01",
        deadline="2026-01-02T00:00:00", deadline_warning_days=3
    )
    # 这个日期已经过去了，所以不需要警告
    check("needs_warning 过期日期返回 False", not todo.needs_warning())

    # 已完成任务不需要警告
    todo.status = TodoStatus.COMPLETED
    check("needs_warning 已完成返回 False", not todo.needs_warning())

    # ===== 8. 导出器直接测试 =====
    print("\n--- 8. 导出器直接测试 ---")

    exporter = TodoExporter(api._storage)
    json_str = exporter.export_json()
    check("Exporter.export_json 返回字符串", isinstance(json_str, str))

    csv_str = exporter.export_csv()
    check("Exporter.export_csv 返回字符串", isinstance(csv_str, str))

    importer = TodoImporter(api._storage)
    result = importer.import_json('{"todos": [], "categories": []}')
    check("Importer 空数据导入", result["success"] and result["count"] == 0)

    # ===== 9. 自动备份测试 =====
    print("\n--- 9. 自动备份测试 ---")

    auto_backup = AutoBackup(api._storage, max_backups=2)
    path1 = auto_backup.run_backup()
    check("自动备份1", os.path.exists(path1))

    path2 = auto_backup.run_backup()
    check("自动备份2", os.path.exists(path2))

    path3 = auto_backup.run_backup()
    check("自动备份3", os.path.exists(path3))

    backups = auto_backup.get_backup_list()
    check("备份列表不超过 max_backups", len(backups) <= 2)

    # ===== 清理 =====
    print("\n--- 清理测试数据 ---")
    all_r = api.list_todos()
    if all_r["success"]:
        for item in all_r["data"]["items"]:
            api.delete_todo(item["id"])

    # ===== 结果汇总 =====
    print("\n" + "=" * 50)
    total = passed + failed
    print(f"  测试结果: {passed}/{total} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
