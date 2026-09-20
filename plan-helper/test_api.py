"""
    ====== test_api.py ======
    Integration tests for the API layer and template/data modules.
    Run: python test_api.py
        by spinner-bot
"""

import sys
import os
import json

# Fix Windows GBK encoding for emoji output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import api
from modules import template as tmpl
from modules import data as dt
from modules.plan import Plan


def test_api_plan_crud():
    """Test Plan CRUD via API."""
    print("=" * 50)
    print("Test: API Plan CRUD")
    print("=" * 50)

    # Create
    resp = api.create_plan(name="API Test Plan", date_tuple=(2026, 9, 20))
    assert resp.success, f"Create failed: {resp.error}"
    plan_id = resp.data["id"]
    print(f"  ✅ Created plan {plan_id}")

    # Read
    resp = api.get_plan(plan_id)
    assert resp.success, f"Get failed: {resp.error}"
    assert resp.data["name"] == "API Test Plan"
    print(f"  ✅ Got plan: {resp.data['name']}")

    # List
    resp = api.list_plans()
    assert resp.success
    assert resp.data["count"] >= 1
    print(f"  ✅ Listed {resp.data['count']} plans")

    # Update name
    resp = api.update_plan_name(plan_id, "Updated Name")
    assert resp.success
    resp = api.get_plan(plan_id)
    assert resp.data["name"] == "Updated Name"
    print(f"  ✅ Updated name to: {resp.data['name']}")

    # Delete
    resp = api.delete_plan(plan_id)
    assert resp.success
    resp = api.get_plan(plan_id)
    assert not resp.success
    print(f"  ✅ Deleted plan {plan_id}")

    print("  🎉 All CRUD tests passed!\n")


def test_api_sections_tasks():
    """Test Section and Task operations."""
    print("=" * 50)
    print("Test: API Sections & Tasks")
    print("=" * 50)

    # Setup
    resp = api.create_plan(name="Section Test")
    plan_id = resp.data["id"]

    # Add sections
    resp = api.add_section(plan_id, "Math", "Calculus")
    assert resp.success
    sec_idx = resp.data["section_index"]
    print(f"  ✅ Added section at index {sec_idx}")

    resp = api.add_section(plan_id, "English", "Vocabulary")
    assert resp.success
    print(f"  ✅ Added second section")

    # Get sections
    resp = api.get_sections(plan_id)
    assert resp.success
    assert len(resp.data["sections"]) == 2
    print(f"  ✅ Got {len(resp.data['sections'])} sections")

    # Add tasks
    resp = api.add_task(plan_id, 0, "Do calculus exercises", 45)
    assert resp.success
    print(f"  ✅ Added task: {resp.data['task_id']}")

    resp = api.add_task(plan_id, 0, "Read textbook", 30)
    assert resp.success
    print(f"  ✅ Added second task: {resp.data['task_id']}")

    resp = api.add_task(plan_id, 1, "Memorize 50 words", 20)
    assert resp.success
    print(f"  ✅ Added task to section B: {resp.data['task_id']}")

    # Get tasks
    resp = api.get_tasks(plan_id)
    assert resp.success
    assert len(resp.data["tasks"]) == 3
    print(f"  ✅ Got {len(resp.data['tasks'])} tasks")

    # Complete a task
    resp = api.complete_task(plan_id, "A1", day=0, time_tuple=(10, 30))
    assert resp.success
    print(f"  ✅ Completed task A1")

    # Check progress
    resp = api.get_progress(plan_id)
    assert resp.success
    assert resp.data["completed_tasks"] == 1
    assert resp.data["progress_percentage"] > 0
    print(f"  ✅ Progress: {resp.data['progress_percentage']}%")

    # Cleanup
    api.delete_plan(plan_id)
    print("  🎉 All section/task tests passed!\n")


def test_api_logs():
    """Test Log operations."""
    print("=" * 50)
    print("Test: API Logs")
    print("=" * 50)

    resp = api.create_plan(name="Log Test")
    plan_id = resp.data["id"]
    api.add_section(plan_id, "Test Section", "")
    api.add_task(plan_id, 0, "Test Task", 30)

    # Add logs
    resp = api.add_log(plan_id, 0, "A1", [9, 0], "Started working")
    assert resp.success
    print(f"  ✅ Added log entry")

    resp = api.add_log(plan_id, 0, "base", "acc", "General progress")
    assert resp.success
    print(f"  ✅ Added second log with current time")

    # Get logs
    resp = api.get_logs(plan_id)
    assert resp.success
    assert len(resp.data["logs"]) == 2
    print(f"  ✅ Got {len(resp.data['logs'])} logs")

    # Cleanup
    api.delete_plan(plan_id)
    print("  🎉 All log tests passed!\n")


def test_template_system():
    """Test template system."""
    print("=" * 50)
    print("Test: Template System")
    print("=" * 50)

    # List templates
    resp = tmpl.list_templates()
    assert resp.success
    assert resp.data["count"] >= 3
    print(f"  ✅ Found {resp.data['count']} templates")

    # Get specific template
    resp = tmpl.get_template("workday")
    assert resp.success
    assert resp.data["template"]["name"] == "工作日计划"
    print(f"  ✅ Got workday template: {resp.data['template']['name']}")

    # Apply template
    resp = tmpl.apply_template("workday", plan_name="My Workday")
    assert resp.success
    plan_id = resp.data["id"]
    print(f"  ✅ Applied workday template -> plan {plan_id}")

    # Verify plan has sections
    resp = api.get_sections(plan_id)
    assert resp.success
    assert len(resp.data["sections"]) >= 2
    print(f"  ✅ Plan has {len(resp.data['sections'])} sections from template")

    # Copy plan
    resp = tmpl.copy_plan(plan_id, new_name="Copied Plan")
    assert resp.success
    copied_id = resp.data["id"]
    print(f"  ✅ Copied plan -> {copied_id}")

    # Cleanup
    api.delete_plan(plan_id)
    api.delete_plan(copied_id)
    print("  🎉 All template tests passed!\n")


def test_conflict_detection():
    """Test conflict detection."""
    print("=" * 50)
    print("Test: Conflict Detection")
    print("=" * 50)

    resp = api.create_plan(name="Conflict Test")
    plan_id = resp.data["id"]
    api.add_section(plan_id, "Test", "")

    # Add tasks with potential issues
    api.add_task(plan_id, 0, "Task A", 300)  # 5 hours - should warn
    api.add_task(plan_id, 0, "Task A", 60)   # Duplicate content

    resp = tmpl.detect_conflicts(plan_id)
    assert resp.success
    data = resp.data
    print(f"  ✅ Conflicts: {data['conflict_count']}, Warnings: {data['warning_count']}")

    # Should detect duplicate
    has_duplicate = any(c["type"] == "duplicate_task" for c in data["conflicts"])
    assert has_duplicate, "Should detect duplicate task"
    print(f"  ✅ Detected duplicate task")

    # Should warn about long task
    has_long = any(w["type"] == "long_task" for w in data["warnings"])
    assert has_long, "Should warn about long task"
    print(f"  ✅ Warned about long task")

    # Cleanup
    api.delete_plan(plan_id)
    print("  🎉 All conflict detection tests passed!\n")


def test_data_export_import():
    """Test data export/import."""
    print("=" * 50)
    print("Test: Data Export/Import")
    print("=" * 50)

    resp = api.create_plan(name="Export Test")
    plan_id = resp.data["id"]
    api.add_section(plan_id, "Section 1", "Info")
    api.add_task(plan_id, 0, "Task 1", 30)

    # Export
    resp = dt.export_plan_to_json(plan_id)
    assert resp.success
    json_str = resp.data["json"]
    print(f"  ✅ Exported plan as JSON ({len(json_str)} chars)")

    # Delete original
    api.delete_plan(plan_id)

    # Import back
    resp = dt.import_plan_from_json(json_str)
    assert resp.success
    new_id = resp.data["id"]
    print(f"  ✅ Imported plan as {new_id}")

    # Verify
    resp = api.get_plan(new_id)
    assert resp.success
    assert resp.data["name"] == "Export Test"
    print(f"  ✅ Verified imported plan: {resp.data['name']}")

    # Cleanup
    api.delete_plan(new_id)
    print("  🎉 All export/import tests passed!\n")


def test_backup_restore():
    """Test backup and restore."""
    print("=" * 50)
    print("Test: Backup & Restore")
    print("=" * 50)

    # Create some plans
    api.create_plan(name="Backup Test 1")
    api.create_plan(name="Backup Test 2")

    # Create backup
    resp = dt.create_backup(backup_dir="test_backups")
    assert resp.success
    backup_file = resp.data["backup_file"]
    print(f"  ✅ Created backup: {backup_file}")

    # List backups
    resp = dt.list_backups(backup_dir="test_backups")
    assert resp.success
    assert resp.data["count"] >= 1
    print(f"  ✅ Found {resp.data['count']} backup(s)")

    # Cleanup
    api.delete_plan(1)
    api.delete_plan(2)
    import shutil
    try:
        shutil.rmtree("test_backups")
    except Exception:
        pass

    print("  🎉 All backup tests passed!\n")


def test_data_validation():
    """Test data validation."""
    print("=" * 50)
    print("Test: Data Validation")
    print("=" * 50)

    resp = api.create_plan(name="Validation Test")
    plan_id = resp.data["id"]
    api.add_section(plan_id, "Valid Section", "")
    api.add_task(plan_id, 0, "Valid Task", 30)

    resp = dt.validate_plan(plan_id)
    assert resp.success
    assert resp.data["is_valid"] == True
    assert resp.data["critical_count"] == 0
    print(f"  ✅ Valid plan: {resp.data['issue_count']} issues")

    # Cleanup
    api.delete_plan(plan_id)
    print("  🎉 All validation tests passed!\n")


def test_boundary_tests():
    """Run the boundary test suite."""
    print("=" * 50)
    print("Test: Boundary Tests")
    print("=" * 50)

    resp = dt.run_boundary_tests()
    assert resp.success
    data = resp.data
    print(f"  Results: {data['passed']}/{data['total']} passed")

    for test in data["tests"]:
        status = "✅" if test["passed"] else "❌"
        detail = f" - {test['detail']}" if test.get("detail") else ""
        print(f"  {status} {test['name']}{detail}")

    assert data["all_passed"], f"Not all tests passed: {data['passed']}/{data['total']}"
    print("  🎉 All boundary tests passed!\n")


def test_suggestions():
    """Test smart suggestions."""
    print("=" * 50)
    print("Test: Smart Suggestions")
    print("=" * 50)

    # Create some plans for history
    api.create_plan(name="History 1", date_tuple=(2026, 9, 15))
    api.create_plan(name="History 2", date_tuple=(2026, 9, 16))

    resp = tmpl.suggest_plan_based_on_history()
    assert resp.success
    print(f"  ✅ Got suggestion: {resp.data.get('message', 'N/A')}")

    # Cleanup
    for idx in list(Plan.registry.keys()):
        Plan.registry[idx].delete()

    print("  🎉 Suggestion test passed!\n")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   plan-helper API Integration Tests")
    print("=" * 50 + "\n")

    tests = [
        test_api_plan_crud,
        test_api_sections_tasks,
        test_api_logs,
        test_template_system,
        test_conflict_detection,
        test_data_export_import,
        test_backup_restore,
        test_data_validation,
        test_boundary_tests,
        test_suggestions,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            # Clean up any leftover plans
            for idx in list(Plan.registry.keys()):
                if idx >= 99900:
                    Plan.registry[idx].delete()

    print("\n" + "=" * 50)
    print(f"   Results: {passed} passed, {failed} failed")
    print("=" * 50)

    sys.exit(0 if failed == 0 else 1)
