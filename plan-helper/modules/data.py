"""
    ====== modules/data.py ======
    Data robustness utilities: import/export, auto-backup, validation,
    boundary testing, and data integrity checks.
        by spinner-bot
"""

import json
import shutil
import os
from datetime import datetime, date
from pathlib import Path
from . import plan as plan_module
from . import api


# ==========================================
# Data Export
# ==========================================

def export_plan_to_json(plan_id):
    """
    Export a plan as a JSON string.
    Returns the raw JSON string (not wrapped in APIResponse).
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return api.error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        json_str = plan_module.Plan.to_json(p)
        return api.success_response(data={"json": json_str})
    except Exception as e:
        return api.error_response(str(e))


def export_all_plans():
    """Export all plans as a single JSON file content."""
    try:
        all_data = {}
        for idx, p in plan_module.Plan.registry.items():
            all_data[str(idx)] = p.plan

        json_str = json.dumps(all_data, indent=2, ensure_ascii=False)
        return api.success_response(data={
            "json": json_str,
            "count": len(all_data),
        })
    except Exception as e:
        return api.error_response(str(e))


def export_to_file(plan_id, output_path):
    """Export a plan to a specific JSON file."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return api.error_response(f"Plan {plan_id} not found", code=404)

        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p_plan = plan_module.Plan.registry[plan_id]
        p_plan.save(str(p))

        return api.success_response(data={"path": str(p), "plan_id": plan_id})
    except Exception as e:
        return api.error_response(str(e))


def export_all_to_directory(dir_path):
    """Export all plans to individual JSON files in a directory."""
    try:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)

        exported = []
        for idx, plan_obj in plan_module.Plan.registry.items():
            file_path = p / f"plan_{idx}.json"
            plan_obj.save(str(file_path))
            exported.append(str(file_path))

        return api.success_response(data={
            "directory": str(p),
            "exported": exported,
            "count": len(exported),
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Data Import
# ==========================================

def import_plan_from_json(json_str, new_id=None):
    """
    Import a plan from a JSON string.
    If new_id is provided, the plan is loaded with that ID.
    """
    try:
        p = plan_module.Plan.load_from_json(json_str, new_id)
        return api.success_response(data=api._serialize_plan(p), code=201)
    except IndexError as e:
        return api.error_response(f"ID conflict: {e}", code=409)
    except json.JSONDecodeError:
        return api.error_response("Invalid JSON format")
    except Exception as e:
        return api.error_response(str(e))


def import_from_file(file_path, new_id=None):
    """Import a plan from a JSON file."""
    try:
        p = plan_module.Plan.read_json(file_path, new_id)
        return api.success_response(data=api._serialize_plan(p), code=201)
    except FileNotFoundError:
        return api.error_response(f"File not found: {file_path}", code=404)
    except IndexError as e:
        return api.error_response(f"ID conflict: {e}", code=409)
    except json.JSONDecodeError:
        return api.error_response("Invalid JSON format in file")
    except Exception as e:
        return api.error_response(str(e))


def import_all_from_directory(dir_path):
    """Import all JSON files from a directory as plans."""
    try:
        p = Path(dir_path)
        if not p.exists():
            return api.error_response(f"Directory not found: {dir_path}", code=404)

        imported = []
        errors = []
        for f in sorted(p.glob("*.json")):
            try:
                plan_obj = plan_module.Plan.read_json(str(f))
                imported.append({"file": str(f), "plan_id": plan_obj.index})
            except Exception as e:
                errors.append({"file": str(f), "error": str(e)})

        return api.success_response(data={
            "imported": imported,
            "errors": errors,
            "imported_count": len(imported),
            "error_count": len(errors),
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Auto Backup
# ==========================================

def create_backup(backup_dir="data/backups"):
    """
    Create a backup of all current plans.
    Saves a timestamped JSON file containing all plan data.
    """
    try:
        p = Path(backup_dir)
        p.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = p / f"backup_{timestamp}.json"

        all_data = {
            "backup_time": datetime.now().isoformat(),
            "plan_count": len(plan_module.Plan.registry),
            "plans": {}
        }

        for idx, plan_obj in plan_module.Plan.registry.items():
            all_data["plans"][str(idx)] = plan_obj.plan

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)

        return api.success_response(data={
            "backup_file": str(backup_file),
            "plan_count": all_data["plan_count"],
            "timestamp": all_data["backup_time"],
        })
    except Exception as e:
        return api.error_response(str(e))


def restore_from_backup(backup_file):
    """
    Restore all plans from a backup file.
    Clears the current registry and loads from backup.
    """
    try:
        p = Path(backup_file)
        if not p.exists():
            return api.error_response(f"Backup file not found: {backup_file}", code=404)

        with open(p, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        plans = backup_data.get("plans", {})
        if not plans:
            return api.error_response("Backup file contains no plans")

        # Clear current registry
        old_registry = plan_module.Plan.registry.copy()
        plan_module.Plan.registry.clear()

        try:
            restored = 0
            for idx_str, plan_data in plans.items():
                idx = int(idx_str)
                plan_obj = plan_module.Plan(idx)
                plan_obj.plan = plan_data
                plan_module.Plan.registry[idx] = plan_obj
                restored += 1

            return api.success_response(data={
                "restored_count": restored,
                "backup_time": backup_data.get("backup_time", "unknown"),
                "message": f"Successfully restored {restored} plans",
            })
        except Exception as e:
            # Rollback
            plan_module.Plan.registry.clear()
            plan_module.Plan.registry.update(old_registry)
            return api.error_response(f"Restore failed, rolled back: {e}")

    except json.JSONDecodeError:
        return api.error_response("Invalid backup file format")
    except Exception as e:
        return api.error_response(str(e))


def list_backups(backup_dir="data/backups"):
    """List all available backup files."""
    try:
        p = Path(backup_dir)
        if not p.exists():
            return api.success_response(data={"backups": [], "count": 0})

        backups = []
        for f in sorted(p.glob("backup_*.json"), reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                backups.append({
                    "file": str(f),
                    "backup_time": data.get("backup_time", "unknown"),
                    "plan_count": data.get("plan_count", 0),
                    "size_bytes": f.stat().st_size,
                })
            except Exception:
                backups.append({
                    "file": str(f),
                    "backup_time": "unknown",
                    "plan_count": 0,
                    "size_bytes": f.stat().st_size,
                })

        return api.success_response(data={"backups": backups, "count": len(backups)})
    except Exception as e:
        return api.error_response(str(e))


def cleanup_old_backups(backup_dir="data/backups", keep=5):
    """Keep only the most recent N backups, delete the rest."""
    try:
        p = Path(backup_dir)
        if not p.exists():
            return api.success_response(data={"deleted": 0})

        backups = sorted(p.glob("backup_*.json"), reverse=True)
        to_delete = backups[keep:]
        deleted = 0

        for f in to_delete:
            try:
                f.unlink()
                deleted += 1
            except Exception:
                pass

        return api.success_response(data={
            "deleted": deleted,
            "remaining": len(backups) - deleted,
            "kept": keep,
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Data Validation
# ==========================================

def validate_plan(plan_id):
    """
    Validate a plan's data integrity.
    Returns a list of issues found (empty = valid).
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return api.error_response(f"Plan {plan_id} not found", code=404)

        p = plan_module.Plan.registry[plan_id]
        issues = []

        # Check head structure
        head = p.plan.get("head")
        if not head:
            issues.append({"level": "critical", "message": "Missing 'head' section"})
        else:
            if "index" not in head:
                issues.append({"level": "critical", "message": "Missing head.index"})
            elif head["index"] != plan_id:
                issues.append({"level": "warning", "message": f"head.index ({head['index']}) != registry key ({plan_id})"})
            if "date" not in head:
                issues.append({"level": "warning", "message": "Missing head.date"})
            elif not isinstance(head["date"], (list, tuple)) or len(head["date"]) != 3:
                issues.append({"level": "warning", "message": "head.date must be [year, month, day]"})

        # Check main structure
        main = p.plan.get("main")
        if main is None:
            issues.append({"level": "critical", "message": "Missing 'main' section"})
        elif not isinstance(main, list):
            issues.append({"level": "critical", "message": "'main' must be a list"})
        else:
            for sec_idx, sec in enumerate(main):
                letter = chr(ord('A') + sec_idx)
                if sec is None:
                    continue
                if not isinstance(sec, dict):
                    issues.append({"level": "critical", "message": f"Section {letter} is not a dict"})
                    continue

                if "plan" not in sec:
                    issues.append({"level": "critical", "message": f"Section {letter}: missing 'plan' list"})
                else:
                    plan_list = sec["plan"]
                    if not isinstance(plan_list, list):
                        issues.append({"level": "critical", "message": f"Section {letter}: 'plan' must be a list"})
                    elif len(plan_list) > 0 and plan_list[0] is not None:
                        issues.append({"level": "warning", "message": f"Section {letter}: plan[0] should be null"})

                    for task_idx, task in enumerate(plan_list):
                        if task is None or task_idx == 0:
                            continue
                        if not isinstance(task, dict):
                            issues.append({"level": "error", "message": f"Section {letter} task {task_idx}: not a dict"})
                            continue
                        if "content" not in task:
                            issues.append({"level": "warning", "message": f"Section {letter} task {task_idx}: missing content"})
                        if "t_m" not in task:
                            issues.append({"level": "warning", "message": f"Section {letter} task {task_idx}: missing t_m"})

                # Check groups
                groups = sec.get("group", {})
                if not isinstance(groups, dict):
                    issues.append({"level": "error", "message": f"Section {letter}: 'group' must be a dict"})
                else:
                    for key in groups:
                        if "_" not in key:
                            issues.append({"level": "warning", "message": f"Section {letter}: group key '{key}' invalid format"})

        # Check log structure
        log = p.plan.get("log")
        if log is None:
            issues.append({"level": "warning", "message": "Missing 'log' section"})
        elif not isinstance(log, list):
            issues.append({"level": "error", "message": "'log' must be a list"})
        else:
            for i, entry in enumerate(log):
                if not isinstance(entry, dict):
                    issues.append({"level": "error", "message": f"Log entry {i}: not a dict"})

        is_valid = not any(i["level"] == "critical" for i in issues)

        return api.success_response(data={
            "plan_id": plan_id,
            "is_valid": is_valid,
            "issues": issues,
            "issue_count": len(issues),
            "critical_count": sum(1 for i in issues if i["level"] == "critical"),
        })
    except Exception as e:
        return api.error_response(str(e))


def validate_all_plans():
    """Validate all plans in registry."""
    try:
        results = []
        all_valid = True
        for idx in plan_module.Plan.registry:
            resp = validate_plan(idx)
            if resp.success:
                results.append(resp.data)
                if not resp.data["is_valid"]:
                    all_valid = False

        return api.success_response(data={
            "all_valid": all_valid,
            "plans_checked": len(results),
            "results": results,
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Boundary Tests
# ==========================================

def run_boundary_tests():
    """
    Run boundary condition tests to verify data robustness.
    Returns test results.
    """
    results = []

    def record(name, passed, detail=""):
        results.append({"name": name, "passed": passed, "detail": detail})

    # Test 1: Create plan with edge-case IDs
    try:
        p = plan_module.Plan(99901, name="Boundary Test", date=(2000, 1, 1))
        record("Create plan with ID 99901", True)
        p.delete()
    except Exception as e:
        record("Create plan with ID 99901", False, str(e))

    # Test 2: Duplicate ID should fail
    try:
        p1 = plan_module.Plan(99902, name="Dup Test 1")
        p2 = plan_module.Plan(99902, name="Dup Test 2")
        record("Duplicate ID should raise", False, "No exception raised")
        p1.delete()
        p2.delete()
    except IndexError:
        try:
            plan_module.Plan.registry.pop(99902, None)
        except Exception:
            pass
        record("Duplicate ID should raise", True)
    except Exception as e:
        record("Duplicate ID should raise", False, str(e))

    # Test 3: Empty plan
    try:
        p = plan_module.Plan(99903, name="Empty Plan")
        h, m = p.time_sum()
        assert h == 0 and m == 0 or h == 0, f"Expected 0 time, got {h}h {m}6m"
        record("Empty plan time_sum", True)
        p.delete()
    except Exception as e:
        record("Empty plan time_sum", False, str(e))
        plan_module.Plan.registry.pop(99903, None)

    # Test 4: Invalid index strings
    try:
        plan_module.Plan("abc")
        record("Non-numeric ID should fail", False)
    except (IndexError, TypeError):
        record("Non-numeric ID should fail", True)

    # Test 5: sep_index edge cases
    try:
        assert plan_module.Plan.sep_index("") == (-3, -3)
        assert plan_module.Plan.sep_index("A") == (0, -1)
        assert plan_module.Plan.sep_index("A1") == (0, 1)
        assert plan_module.Plan.sep_index("Z99") == (25, 99)
        record("sep_index edge cases", True)
    except Exception as e:
        record("sep_index edge cases", False, str(e))

    # Test 6: num2char / char2num roundtrip
    try:
        for i in range(26):
            c = plan_module.Plan.num2char(i)
            n = plan_module.Plan.char2num(c)
            assert n == i, f"Roundtrip failed: {i} -> {c} -> {n}"
        record("num2char/char2num roundtrip (A-Z)", True)
    except Exception as e:
        record("num2char/char2num roundtrip (A-Z)", False, str(e))

    # Test 7: Log with special time values
    try:
        p = plan_module.Plan(99904, name="Log Test")
        p.add_section("Test", "")
        p.add_plan(0, "Test task", 1)

        # "acc" time
        idx = p.add_log(0, "A1", "acc", "test acc")
        assert idx >= 0
        # "nacc" time
        idx = p.add_log(0, "A1", "nacc", "test nacc")
        assert idx >= 0
        # Explicit time
        idx = p.add_log(0, "A1", [10, 30], "explicit time")
        assert idx >= 0

        record("Log with special time values", True)
        p.delete()
    except Exception as e:
        record("Log with special time values", False, str(e))
        plan_module.Plan.registry.pop(99904, None)

    # Test 8: JSON roundtrip
    try:
        p = plan_module.Plan(99905, name="JSON Test", date=(2026, 9, 20))
        p.add_section("S1", "Info")
        p.add_plan(0, "Task 1", 5)
        json_str = plan_module.Plan.to_json(p)
        p.delete()

        p2 = plan_module.Plan.load_from_json(json_str, 99905)
        assert p2.plan["head"]["name"] == "JSON Test"
        assert len(p2.plan["main"]) == 1

        record("JSON roundtrip", True)
        p2.delete()
    except Exception as e:
        record("JSON roundtrip", False, str(e))
        plan_module.Plan.registry.pop(99905, None)

    # Test 9: Time overflow handling
    try:
        p = plan_module.Plan(99906, name="Time Overflow")
        p.add_section("S", "")
        # Add a task with very large time
        p.add_plan(0, "Huge task", 1000)
        h, m = p.time_sum()
        assert h > 0
        record("Large time value handling", True)
        p.delete()
    except Exception as e:
        record("Large time value handling", False, str(e))
        plan_module.Plan.registry.pop(99906, None)

    # Test 10: Negative day in log
    try:
        p = plan_module.Plan(99907, name="Negative Day")
        idx = p.add_log(-1, "base", [10, 0], "before plan start")
        log_entry = p.plan["log"][idx]
        assert log_entry["day"] == -1
        record("Negative day in log", True)
        p.delete()
    except Exception as e:
        record("Negative day in log", False, str(e))
        plan_module.Plan.registry.pop(99907, None)

    # Summary
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    return api.success_response(data={
        "tests": results,
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
    })
