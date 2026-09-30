"""
    ====== modules/api.py ======
    Unified API layer for plan-helper core functionality.
    Wraps core logic (plan, manager) with a consistent response format,
    making it callable by other modules (time-helper, to-dos) or external tools.
        by spinner-bot
"""

import json
import copy
import os
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from . import plan as plan_module
from . import manager as manager_module


# ==========================================
# Unified Response Format
# ==========================================

class APIResponse:
    """Unified response wrapper for all API calls."""

    def __init__(self, success=True, data=None, error=None, code=200):
        self.success = success
        self.data = data
        self.error = error
        self.code = code
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        result = {
            "success": self.success,
            "code": self.code,
            "timestamp": self.timestamp,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        return result

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def success_response(data=None, code=200):
    return APIResponse(success=True, data=data, code=code)

def error_response(message, code=400):
    return APIResponse(success=False, error=message, code=code)


def _archive_dir(archive_dir=None):
    """Resolve the archive root without breaking the legacy source layout."""
    if archive_dir:
        return Path(archive_dir)
    configured = os.environ.get("EFFILIFE_PLAN_ARCHIVE_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).parent.parent / "data" / "archives"


# ==========================================
# Plan CRUD Operations
# ==========================================

def create_plan(name=None, date_tuple=None, plan_id=None, sections=None):
    """
    Create a new plan.
    Args:
        name: Plan name (optional)
        date_tuple: (year, month, day) tuple, defaults to today
        plan_id: Preferred ID (optional, auto-assigned if None)
    Returns:
        APIResponse with plan data
    """
    try:
        if plan_id is None:
            plan_id = plan_module.Plan.request_id()
        else:
            plan_id = int(plan_id)
            if plan_id in plan_module.Plan.registry:
                return error_response(f"Plan ID {plan_id} is already in use", code=409)

        if date_tuple is None:
            today = date.today()
            date_tuple = (today.year, today.month, today.day)

        if not name or not str(name).strip():
            return error_response("Plan name is required")
        _validate_date_tuple(date_tuple)
        p = plan_module.Plan(plan_id, name=str(name).strip(), date=date_tuple)
        for section in sections or []:
            section_name = str(section.get("name", "")).strip()
            if not section_name:
                continue
            p.add_section(section_name, section.get("info", ""))
            section_index = len(p.plan["main"]) - 1
            for task in section.get("tasks", []):
                content = str(task.get("content", "")).strip()
                if content:
                    minutes = max(float(task.get("time_minutes", 0) or 0), 0)
                    p.add_plan(section_index, content, minutes / 6.0)
        return success_response(data=_serialize_plan(p), code=201)
    except Exception as e:
        return error_response(str(e))


def get_plan(plan_id):
    """Get a plan by ID."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        return success_response(data=_serialize_plan(p))
    except (ValueError, TypeError):
        return error_response("Invalid plan ID")


def list_plans():
    """List all plans in registry."""
    try:
        plans = []
        for idx, p in plan_module.Plan.registry.items():
            plans.append(_serialize_plan_summary(p))
        return success_response(data={"plans": plans, "count": len(plans)})
    except Exception as e:
        return error_response(str(e))


def update_plan_name(plan_id, name):
    """Update plan name."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        if not str(name or "").strip():
            return error_response("Plan name is required")
        p.plan["head"]["name"] = str(name).strip()
        return success_response(data={"plan_id": plan_id, "name": p.plan["head"]["name"]})
    except (ValueError, TypeError):
        return error_response("Invalid plan ID")


def update_plan(plan_id, name=None, date_tuple=None):
    """Update plan metadata."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        if name is not None:
            if not str(name).strip():
                return error_response("Plan name is required")
            p.plan["head"]["name"] = str(name).strip()
        if date_tuple is not None:
            _validate_date_tuple(date_tuple)
            p.plan["head"]["date"] = tuple(int(v) for v in date_tuple)
        return success_response(data=_serialize_plan(p))
    except (ValueError, TypeError) as e:
        return error_response(str(e))


def delete_plan(plan_id):
    """Soft-delete a plan (remove from registry)."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        p.delete()
        return success_response(data={"plan_id": plan_id, "deleted": True})
    except (ValueError, TypeError):
        return error_response("Invalid plan ID")


def archive_plan(plan_id, archive_dir=None):
    """Archive a plan to a recoverable JSON file and remove it from active plans."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        target_dir = _archive_dir(archive_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = target_dir / f"plan_{plan_id}_{timestamp}.json"
        with open(archive_file, "w", encoding="utf-8") as handle:
            json.dump({
                "archived_at": datetime.now().isoformat(),
                "plan": p.plan,
            }, handle, ensure_ascii=False, indent=2)
        p.delete()
        return success_response(data={
            "plan_id": plan_id,
            "archived": True,
            "file": str(archive_file),
        })
    except (ValueError, TypeError, OSError) as e:
        return error_response(str(e))


def list_archives(archive_dir=None):
    """List recoverable archived plans."""
    try:
        target_dir = _archive_dir(archive_dir)
        if not target_dir.exists():
            return success_response(data={"archives": [], "count": 0})
        archives = []
        for archive_file in sorted(target_dir.glob("plan_*.json"), reverse=True):
            try:
                with open(archive_file, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                plan_data = payload.get("plan", {})
                head = plan_data.get("head", {})
                archives.append({
                    "file": archive_file.name,
                    "path": str(archive_file),
                    "plan_id": head.get("index"),
                    "name": head.get("name"),
                    "date": list(head.get("date", ())),
                    "archived_at": payload.get("archived_at"),
                })
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return success_response(data={"archives": archives, "count": len(archives)})
    except OSError as e:
        return error_response(str(e))


def restore_archive(filename, archive_dir=None, new_id=None):
    """Restore an archived plan into the active registry."""
    try:
        safe_name = Path(str(filename)).name
        target_dir = _archive_dir(archive_dir)
        archive_file = target_dir / safe_name
        if not archive_file.exists() or archive_file.suffix != ".json":
            return error_response("Archive not found", code=404)
        with open(archive_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        plan_data = payload.get("plan")
        if not isinstance(plan_data, dict):
            return error_response("Invalid archive format")
        restored = plan_module.Plan.load_from_json(json.dumps(plan_data, ensure_ascii=False), new_id=new_id)
        return success_response(data=_serialize_plan(restored), code=201)
    except (OSError, ValueError, TypeError, IndexError, json.JSONDecodeError) as e:
        return error_response(str(e))


def get_management_stats():
    """Return plans-level aggregate statistics for management screens."""
    summaries = [_serialize_plan_summary(p) for p in plan_module.Plan.registry.values()]
    total_tasks = sum(item["total_tasks"] for item in summaries)
    completed_tasks = sum(item["completed_tasks"] for item in summaries)
    total_minutes = sum(item["estimated_minutes"] for item in summaries)
    by_date = {}
    for item in summaries:
        key = "/".join(str(part).zfill(2) for part in item["date"])
        by_date[key] = by_date.get(key, 0) + 1
    return success_response(data={
        "plan_count": len(summaries),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "estimated_minutes": round(total_minutes, 1),
        "completion_percentage": round(completed_tasks / total_tasks * 100, 1) if total_tasks else 0,
        "by_date": by_date,
        "plans": summaries,
    })


# ==========================================
# Section Operations
# ==========================================

def add_section(plan_id, name, info=""):
    """Add a section to a plan."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        p.add_section(name, info)
        section_idx = len(p.plan["main"]) - 1
        return success_response(
            data={"plan_id": plan_id, "section_index": section_idx, "name": name},
            code=201
        )
    except Exception as e:
        return error_response(str(e))


def update_section(plan_id, section_index, name=None, info=None):
    """Update section metadata."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        section = p.update_section(int(section_index), name, info)
        return success_response(data={
            "plan_id": plan_id,
            "section_index": int(section_index),
            "name": section.get("name", ""),
            "info": section.get("info", ""),
        })
    except (IndexError, ValueError, TypeError) as e:
        return error_response(str(e), code=400)


def get_sections(plan_id):
    """Get all sections of a plan."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        sections = []
        for i, sec in enumerate(p.plan["main"]):
            sections.append({
                "index": i,
                "name": sec.get("name", ""),
                "info": sec.get("info", ""),
                "task_count": sum(1 for t in sec.get("plan", []) if t and t.get("is_active", False)),
                "letter": plan_module.Plan.num2char(i),
            })
        return success_response(data={"plan_id": plan_id, "sections": sections})
    except Exception as e:
        return error_response(str(e))


def delete_section(plan_id, section_index):
    """Soft-delete a section."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        p.del_section(int(section_index))
        return success_response(data={"plan_id": plan_id, "section_index": section_index})
    except Exception as e:
        return error_response(str(e))


# ==========================================
# Task (Plan Item) Operations
# ==========================================

def _active_task_entries(p, section_index):
    """Return active tasks with a compact, derived display index.

    The plan data keeps its original ordered slots so soft deletion does not
    invalidate historical task references.  Display numbering is deliberately
    calculated on demand and is never persisted.
    """
    section = p.plan["main"][section_index]
    entries = []
    display_index = 0
    for internal_index, task in enumerate(section.get("plan", [])):
        if internal_index == 0 or not task or not task.get("is_active", True):
            continue
        display_index += 1
        entries.append((internal_index, display_index, task))
    return entries


def _task_id_for_display(p, task_id):
    """Resolve an API task ID while preserving stable internal references.

    A stable internal ID is preferred when it points at an active task.  If
    that slot is inactive, the numeric part is interpreted as the compact
    display position among active tasks.  This lets the UI show A1, A2, ...
    after soft deletion without rewriting logs or stored task data.
    """
    section_index, requested_index = plan_module.Plan.sep_index(str(task_id))
    if section_index < 0 or requested_index < 1:
        return None
    if section_index >= len(p.plan["main"]):
        return None

    section = p.plan["main"][section_index]
    raw_tasks = section.get("plan", [])
    if requested_index < len(raw_tasks):
        task = raw_tasks[requested_index]
        if task and task.get("is_active", True):
            return plan_module.Plan.syn_index(section_index, requested_index)

    entries = _active_task_entries(p, section_index)
    for internal_index, display_index, _task in entries:
        if display_index == requested_index:
            return plan_module.Plan.syn_index(section_index, internal_index)
    return None

def add_task(plan_id, section_index, content, time_minutes):
    """
    Add a task to a section.
    time_minutes: estimated time in minutes (will be converted to t_m units)
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        t_m = float(time_minutes) / 6.0
        task_id = p.add_plan(int(section_index), content, t_m)
        return success_response(
            data={"plan_id": plan_id, "task_id": task_id, "content": content, "time_minutes": time_minutes},
            code=201
        )
    except Exception as e:
        return error_response(str(e))


def update_task(plan_id, task_id, content=None, time_minutes=None):
    """Update task content and estimated duration."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        if content is not None and not str(content).strip():
            return error_response("Task content is required")
        p = plan_module.Plan.registry[plan_id]
        internal_id = _task_id_for_display(p, task_id)
        if internal_id is None:
            return error_response(f"Invalid task ID: {task_id}", code=400)
        task = p.update_plan_item(
            internal_id,
            content=content,
            t_m=(float(time_minutes) / 6.0) if time_minutes is not None else None,
        )
        return success_response(data={
            "plan_id": plan_id,
            "task_id": task_id,
            "content": task.get("content", ""),
            "time_minutes": round(task.get("t_m", 0) * 6, 1),
        })
    except (ValueError, TypeError, IndexError) as e:
        return error_response(str(e), code=400)


def get_tasks(plan_id, section_index=None):
    """Get tasks, optionally filtered by section."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        tasks = []
        sections = p.plan["main"]
        for sec_idx, sec in enumerate(sections):
            if section_index is not None and sec_idx != int(section_index):
                continue
            for task_idx, display_idx, task in _active_task_entries(p, sec_idx):
                internal_id = plan_module.Plan.syn_index(sec_idx, task_idx)
                display_id = plan_module.Plan.syn_index(sec_idx, display_idx)
                tasks.append({
                    "id": internal_id,
                    "internal_id": internal_id,
                    "display_id": display_id,
                    "section_index": sec_idx,
                    "section_letter": plan_module.Plan.num2char(sec_idx),
                    "task_index": display_idx,
                    "internal_index": task_idx,
                    "content": task.get("content", ""),
                    "time_minutes": round(task.get("t_m", 0) * 6, 1),
                    "is_active": task.get("is_active", True),
                    "finish": task.get("finish"),
                })
        return success_response(data={"plan_id": plan_id, "tasks": tasks})
    except Exception as e:
        return error_response(str(e))


def complete_task(plan_id, task_id, day=None, time_tuple=None):
    """
    Mark a task as finished.
    task_id: string like "A1", "B3"
    day: day offset (default: 0)
    time_tuple: (hour, minute) tuple, defaults to current time
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]

        if day is None:
            day = 0
        if time_tuple is None:
            now = datetime.now()
            time_tuple = (now.hour, now.minute)

        internal_id = _task_id_for_display(p, task_id)
        if internal_id is None:
            return error_response(f"Invalid task ID: {task_id}", code=400)
        result = p.finish(internal_id, day, time_tuple)
        if result == -1:
            return error_response(f"Failed to mark task {task_id} as complete")
        return success_response(data={"plan_id": plan_id, "task_id": task_id, "completed": True})
    except Exception as e:
        return error_response(str(e))


def delete_task(plan_id, task_id):
    """Soft-delete a task."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        internal_id = _task_id_for_display(p, task_id)
        if internal_id is None:
            return error_response(f"Invalid task ID: {task_id}", code=400)
        result = p.del_plan(internal_id)
        if result == -1:
            return error_response(f"Invalid task ID: {task_id}")
        return success_response(data={"plan_id": plan_id, "task_id": task_id, "deleted": True})
    except Exception as e:
        return error_response(str(e))


# ==========================================
# Progress Log Operations
# ==========================================

def add_log(plan_id, day, task_id, time_input, content=""):
    """
    Add a progress log entry.
    task_id: "A1", "B3", or "base"
    time_input: "acc" (current time), "nacc" (current hour), or [hour, minute]
    content: log content
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        log_idx = p.add_log(day, task_id, time_input, content)
        return success_response(
            data={"plan_id": plan_id, "log_index": log_idx},
            code=201
        )
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(str(e))


def get_logs(plan_id):
    """Get all log entries for a plan."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        logs = []
        for i, log in enumerate(p.plan.get("log", [])):
            logs.append({
                "index": i,
                "day": log.get("day"),
                "plan": log.get("plan", "base"),
                "time": log.get("time"),
                "content": log.get("content", ""),
            })
        return success_response(data={"plan_id": plan_id, "logs": logs})
    except Exception as e:
        return error_response(str(e))


# ==========================================
# Persistence Operations
# ==========================================

def save_plan(plan_id, path):
    """Save a plan to a JSON file."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        p.save(path)
        return success_response(data={"plan_id": plan_id, "path": str(path)})
    except Exception as e:
        return error_response(str(e))


def load_plan(path, new_id=None):
    """Load a plan from a JSON file."""
    try:
        p = plan_module.Plan.read_json(path, new_id)
        return success_response(data=_serialize_plan(p), code=201)
    except FileNotFoundError:
        return error_response(f"File not found: {path}", code=404)
    except Exception as e:
        return error_response(str(e))


def save_registry(anchor=""):
    """Save all plans to registry."""
    try:
        plan_module.Plan.save_registry(anchor)
        return success_response(data={"message": "Registry saved", "anchor": str(anchor)})
    except Exception as e:
        return error_response(str(e))


def load_registry(anchor=""):
    """Load all plans from registry."""
    try:
        result = plan_module.Plan.load_registry(anchor)
        if result == -1:
            return error_response("Failed to load registry: file not found or corrupted")
        elif result == -2:
            return error_response("Failed to load registry: unknown error")
        return success_response(data={"message": "Registry loaded", "count": len(plan_module.Plan.registry)})
    except Exception as e:
        return error_response(str(e))


# ==========================================
# Statistics & Progress
# ==========================================

def get_progress(plan_id):
    """Get progress summary for a plan."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]

        total_tasks = 0
        completed_tasks = 0
        active_tasks = 0
        total_minutes = 0
        completed_minutes = 0

        for sec in p.plan["main"]:
            for task_idx, task in enumerate(sec.get("plan", [])):
                if task is None or task_idx == 0:
                    continue
                task_mins = round(task.get("t_m", 0) * 6, 1)
                total_minutes += task_mins
                if task.get("is_active", True):
                    active_tasks += 1
                    total_tasks += 1
                    if task.get("finish"):
                        completed_tasks += 1
                        completed_minutes += task_mins

        progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        time_h, time_6m = p.time_sum()
        total_h = time_h + (time_6m * 6) / 60

        return success_response(data={
            "plan_id": plan_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_tasks": active_tasks,
            "progress_percentage": round(progress_pct, 1),
            "total_minutes": round(total_minutes, 1),
            "completed_minutes": round(completed_minutes, 1),
            "estimated_hours": round(total_h, 1),
        })
    except Exception as e:
        return error_response(str(e))


def get_plan_full(plan_id):
    """Get complete plan data including all sections, tasks, groups, and logs."""
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        return success_response(data=_serialize_plan_full(p))
    except Exception as e:
        return error_response(str(e))


def export_registry():
    """Export active and archived raw plan snapshots without reshaping them."""
    try:
        plans = [copy.deepcopy(plan_obj.plan) for plan_obj in plan_module.Plan.registry.values()]
        archives = []
        archive_root = _archive_dir()
        if archive_root.exists():
            for archive_file in sorted(archive_root.glob("plan_*.json"), reverse=True):
                try:
                    with open(archive_file, "r", encoding="utf-8") as handle:
                        payload = json.load(handle)
                    if isinstance(payload, dict) and isinstance(payload.get("plan"), dict):
                        archives.append({"file": archive_file.name, "payload": payload})
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
        return success_response(data={
            "format": "plan-helper.raw.v1",
            "plans": plans,
            "count": len(plans),
            "archives": archives,
            "archive_count": len(archives),
        })
    except Exception as e:
        return error_response(str(e))


def add_group(plan_id, section_index, title, description="", start_index=0, end_index=0):
    """Add a non-crossing task range group while preserving nested groups."""
    try:
        plan_id = int(plan_id)
        section_index = int(section_index)
        start_index = int(start_index)
        end_index = int(end_index)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        if start_index < 0 or end_index <= start_index:
            return error_response("Group range must have end > start", code=400)
        if not str(title).strip():
            return error_response("Group title is required", code=400)
        p = plan_module.Plan.registry[plan_id]
        result = p.add_group(section_index, str(title).strip(), str(description or "").strip(), start_index, end_index)
        if result is False:
            return error_response("Group range crosses an existing group", code=409)
        return success_response(data={
            "plan_id": plan_id,
            "section_index": section_index,
            "key": f"{start_index}_{end_index}",
            "title": str(title).strip(),
            "description": str(description or "").strip(),
        }, code=201)
    except (IndexError, KeyError, TypeError, ValueError) as e:
        return error_response(str(e), code=400)


def update_group(plan_id, section_index, group_key, title=None, description=None):
    """Update group metadata without changing its range or nesting."""
    try:
        plan_id = int(plan_id)
        section_index = int(section_index)
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        group = p.plan["main"][section_index].get("group", {}).get(str(group_key))
        if group is None:
            return error_response("Group not found", code=404)
        if title is not None:
            if not str(title).strip():
                return error_response("Group title is required", code=400)
            group["title"] = str(title).strip()
        if description is not None:
            group["description"] = str(description).strip()
        return success_response(data={
            "plan_id": plan_id,
            "section_index": section_index,
            "key": str(group_key),
            "title": group.get("title", ""),
            "description": group.get("description", ""),
        })
    except (IndexError, KeyError, TypeError, ValueError) as e:
        return error_response(str(e), code=400)


def delete_group(plan_id, section_index, group_key):
    """Delete only group metadata; task slots and log references are untouched."""
    try:
        plan_id = int(plan_id)
        section_index = int(section_index)
        start_index, end_index = (int(part) for part in str(group_key).split("_", 1))
        if plan_id not in plan_module.Plan.registry:
            return error_response(f"Plan {plan_id} not found", code=404)
        p = plan_module.Plan.registry[plan_id]
        p.pur_group(section_index, start_index, end_index)
        return success_response(data={"plan_id": plan_id, "section_index": section_index, "key": str(group_key), "deleted": True})
    except (IndexError, KeyError, TypeError, ValueError) as e:
        return error_response(str(e), code=400)


def import_registry(plans, archives=None, replace=True):
    """Restore raw Plan.plan snapshots atomically.

    The raw structure is validated before touching the live registry.  This
    deliberately avoids reconstructing a plan through display summaries so
    soft-deleted slots, nested groups, and log references remain intact.
    """
    if not isinstance(plans, list):
        return error_response("plans must be a list")

    prepared = []
    seen_ids = set()
    try:
        for raw_plan in plans:
            if not isinstance(raw_plan, dict):
                return error_response("Each plan snapshot must be an object")
            head = raw_plan.get("head")
            main = raw_plan.get("main")
            logs = raw_plan.get("log")
            if not isinstance(head, dict) or not isinstance(main, list) or not isinstance(logs, list):
                return error_response("Invalid raw plan snapshot")
            plan_id = int(head.get("index"))
            if plan_id in seen_ids:
                return error_response(f"Duplicate plan ID: {plan_id}")
            seen_ids.add(plan_id)
            prepared.append(copy.deepcopy(raw_plan))
    except (TypeError, ValueError) as e:
        return error_response(f"Invalid plan ID: {e}")

    prepared_archives = None
    if archives is not None:
        if not isinstance(archives, list):
            return error_response("archives must be a list")
        prepared_archives = []
        seen_archive_files = set()
        for entry in archives:
            if not isinstance(entry, dict):
                return error_response("Each archive snapshot must be an object")
            raw_filename = str(entry.get("file", ""))
            filename = Path(raw_filename).name
            payload = entry.get("payload")
            if not raw_filename or filename != raw_filename or not filename.endswith(".json"):
                return error_response("Invalid archive filename")
            if filename in seen_archive_files:
                return error_response(f"Duplicate archive filename: {filename}")
            if not isinstance(payload, dict) or not isinstance(payload.get("plan"), dict):
                return error_response("Invalid archive snapshot")
            seen_archive_files.add(filename)
            prepared_archives.append((filename, copy.deepcopy(payload)))

    backup = plan_module.Plan.registry.copy()
    imported = []
    skipped = []
    archive_backup = None
    written_archives = []
    try:
        if replace:
            plan_module.Plan.registry.clear()
        for raw_plan in prepared:
            plan_id = int(raw_plan["head"]["index"])
            if plan_id in plan_module.Plan.registry:
                skipped.append(plan_id)
                continue
            plan_module.Plan.load_from_json(json.dumps(raw_plan, ensure_ascii=False), new_id=plan_id)
            imported.append(plan_id)

        if prepared_archives is not None:
            archive_root = _archive_dir()
            archive_root.mkdir(parents=True, exist_ok=True)
            archive_backup = archive_root / f".effilife-archive-backup-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            archive_backup.mkdir()
            for existing in archive_root.glob("plan_*.json"):
                existing.replace(archive_backup / existing.name)
            for filename, payload in prepared_archives:
                destination = archive_root / filename
                with open(destination, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2)
                written_archives.append(destination)
            shutil.rmtree(archive_backup)
            archive_backup = None
    except Exception as e:
        for destination in written_archives:
            destination.unlink(missing_ok=True)
        if archive_backup is not None and archive_backup.exists():
            for previous in archive_backup.glob("plan_*.json"):
                previous.replace(_archive_dir() / previous.name)
            archive_backup.rmdir()
        plan_module.Plan.registry.clear()
        plan_module.Plan.registry.update(backup)
        return error_response(f"Plan import rolled back: {e}")

    return success_response(data={
        "format": "plan-helper.raw.v1",
        "imported": imported,
        "skipped": skipped,
        "count": len(imported),
        "replaced": bool(replace),
        "archives": len(prepared_archives) if prepared_archives is not None else None,
    })


# ==========================================
# Internal Serialization Helpers
# ==========================================

def _serialize_plan(p):
    """Serialize a plan object to a dict."""
    return {
        "id": p.index,
        "name": p.plan["head"].get("name"),
        "date": list(p.plan["head"].get("date", ())),
        "sections_count": len(p.plan["main"]),
        "logs_count": len(p.plan["log"]),
    }


def _serialize_plan_summary(p):
    """Serialize plan summary for list view."""
    total_tasks = 0
    completed_tasks = 0
    total_minutes = 0

    for sec in p.plan["main"]:
        for task_idx, task in enumerate(sec.get("plan", [])):
            if task is None or task_idx == 0:
                continue
            if task.get("is_active", True):
                total_tasks += 1
                total_minutes += round(task.get("t_m", 0) * 6, 1)
                if task.get("finish"):
                    completed_tasks += 1

    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        "id": p.index,
        "name": p.plan["head"].get("name"),
        "date": list(p.plan["head"].get("date", ())),
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "progress_percentage": round(progress, 1),
        "estimated_minutes": round(total_minutes, 1),
    }


def _serialize_plan_full(p):
    """Serialize complete plan data."""
    sections = []
    for sec_idx, sec in enumerate(p.plan["main"]):
        tasks = []
        for task_idx, display_idx, task in _active_task_entries(p, sec_idx):
            internal_id = plan_module.Plan.syn_index(sec_idx, task_idx)
            display_id = plan_module.Plan.syn_index(sec_idx, display_idx)
            tasks.append({
                "index": display_idx,
                "display_index": display_idx,
                "display_id": display_id,
                "internal_index": task_idx,
                "internal_id": internal_id,
                "content": task.get("content", ""),
                "time_minutes": round(task.get("t_m", 0) * 6, 1),
                "is_active": True,
                "finish": task.get("finish"),
            })

        groups = {}
        for key, val in sec.get("group", {}).items():
            groups[key] = {
                "title": val.get("title", ""),
                "description": val.get("description", ""),
            }

        sections.append({
            "index": sec_idx,
            "letter": plan_module.Plan.num2char(sec_idx),
            "name": sec.get("name", ""),
            "info": sec.get("info", ""),
            "tasks": tasks,
            "groups": groups,
        })

    logs = []
    for i, log in enumerate(p.plan.get("log", [])):
        logs.append({
            "index": i,
            "day": log.get("day"),
            "plan": log.get("plan", "base"),
            "time": log.get("time"),
            "content": log.get("content", ""),
        })

    return {
        "id": p.index,
        "name": p.plan["head"].get("name"),
        "date": list(p.plan["head"].get("date", ())),
        "sections": sections,
        "logs": logs,
    }


def _validate_date_tuple(date_tuple):
    """Validate and normalize a [year, month, day] date tuple."""
    if not date_tuple or len(date_tuple) != 3:
        raise ValueError("Date must be year, month and day")
    try:
        date(int(date_tuple[0]), int(date_tuple[1]), int(date_tuple[2]))
    except (TypeError, ValueError):
        raise ValueError("Invalid date")
