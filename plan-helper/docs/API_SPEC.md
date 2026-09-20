# plan-helper API Specification

> Version: 0.2.0 | Updated: 2026-09-20

---

## Overview

The plan-helper API provides a unified interface for plan management, task tracking, and progress logging. All API functions return `APIResponse` objects with a consistent structure.

### Module: `modules.api`

```python
from modules import api
```

---

## Response Format

All API responses follow this structure:

```json
{
    "success": true,
    "code": 200,
    "timestamp": "2026-09-20T14:30:00.000000",
    "data": { ... }
}
```

### Error Response

```json
{
    "success": false,
    "code": 404,
    "timestamp": "2026-09-20T14:30:00.000000",
    "error": "Plan 999 not found"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 409 | Conflict (ID already in use) |

---

## Plan Operations

### `create_plan(name=None, date_tuple=None, plan_id=None)`

Create a new plan.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | str | None | Plan name |
| date_tuple | tuple | today | (year, month, day) |
| plan_id | int | auto | Preferred plan ID |

**Returns**: Plan data including id, name, date.

```python
resp = api.create_plan(name="Study Plan", date_tuple=(2026, 9, 20))
# resp.data = {"id": 1, "name": "Study Plan", "date": [2026, 9, 20], ...}
```

---

### `get_plan(plan_id)`

Get plan summary by ID.

```python
resp = api.get_plan(1)
```

---

### `list_plans()`

List all plans in registry.

```python
resp = api.list_plans()
# resp.data = {"plans": [...], "count": 3}
```

---

### `update_plan_name(plan_id, name)`

Update plan name.

```python
resp = api.update_plan_name(1, "New Name")
```

---

### `delete_plan(plan_id)`

Remove plan from registry.

```python
resp = api.delete_plan(1)
```

---

## Section Operations

### `add_section(plan_id, name, info="")`

Add a section (chapter) to a plan.

```python
resp = api.add_section(1, "Math Review", "Calculus and Linear Algebra")
```

---

### `get_sections(plan_id)`

List all sections with task counts.

```python
resp = api.get_sections(1)
# resp.data = {"sections": [{"index": 0, "name": "...", "letter": "A", "task_count": 5}, ...]}
```

---

### `delete_section(plan_id, section_index)`

Soft-delete a section (marks all tasks as inactive).

```python
resp = api.delete_section(1, 0)
```

---

## Task Operations

### `add_task(plan_id, section_index, content, time_minutes)`

Add a task to a section.

| Parameter | Type | Description |
|-----------|------|-------------|
| plan_id | int | Plan ID |
| section_index | int | Section index (0-based) |
| content | str | Task description |
| time_minutes | float | Estimated time in minutes |

```python
resp = api.add_task(1, 0, "Complete calculus exercises", 45)
# resp.data = {"task_id": "A6", ...}
```

---

### `get_tasks(plan_id, section_index=None)`

Get tasks, optionally filtered by section.

```python
resp = api.get_tasks(1)  # All tasks
resp = api.get_tasks(1, section_index=0)  # Only section A
```

---

### `complete_task(plan_id, task_id, day=None, time_tuple=None)`

Mark a task as finished.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| task_id | str | required | Task ID like "A1", "B3" |
| day | int | 0 | Day offset from plan start |
| time_tuple | tuple | current time | (hour, minute) |

```python
resp = api.complete_task(1, "A1", day=0, time_tuple=(10, 30))
```

---

### `delete_task(plan_id, task_id)`

Soft-delete a task.

```python
resp = api.delete_task(1, "A2")
```

---

## Log Operations

### `add_log(plan_id, day, task_id, time_input, content="")`

Add a progress log entry.

| Parameter | Type | Description |
|-----------|------|-------------|
| day | int | Day offset (0 = plan start day) |
| task_id | str | "A1", "B3", or "base" |
| time_input | str/list | "acc" (current time), "nacc" (current hour), or [h, m] |
| content | str | Log content |

```python
resp = api.add_log(1, 0, "A1", "acc", "Started working on calculus")
resp = api.add_log(1, 0, "base", [9, 0], "Morning study session")
```

---

### `get_logs(plan_id)`

Get all log entries for a plan.

```python
resp = api.get_logs(1)
```

---

## Persistence

### `save_plan(plan_id, path)`

Save a single plan to a JSON file.

```python
api.save_plan(1, "plans/my_plan.json")
```

---

### `load_plan(path, new_id=None)`

Load a plan from a JSON file.

```python
resp = api.load_plan("plans/my_plan.json")
```

---

### `save_registry(anchor="")`

Save all plans to the registry directory structure.

```python
api.save_registry("data")
```

---

### `load_registry(anchor="")`

Load all plans from registry.

```python
resp = api.load_registry("data")
```

---

## Statistics

### `get_progress(plan_id)`

Get progress summary for a plan.

```python
resp = api.get_progress(1)
# resp.data = {
#     "total_tasks": 12,
#     "completed_tasks": 8,
#     "progress_percentage": 66.7,
#     "total_minutes": 480,
#     "completed_minutes": 320,
#     "estimated_hours": 8.0
# }
```

---

### `get_plan_full(plan_id)`

Get complete plan data including all sections, tasks, groups, and logs.

```python
resp = api.get_plan_full(1)
```

---

## Usage with Other Modules

### From time-helper

```python
from modules import api

# Get today's plan summary
plans = api.list_plans()
for plan in plans.data["plans"]:
    progress = api.get_progress(plan["id"])
    print(f"Plan {plan['name']}: {progress.data['progress_percentage']}% done")
```

### From to-dos

```python
from modules import api

# Create a plan based on pending tasks
resp = api.create_plan(name="Task-driven Plan")
api.add_section(resp.data["id"], "Priority Tasks")
api.add_task(resp.data["id"], 0, "Complete report", 60)
```

---

## Data Model Reference

### Plan Structure

```json
{
    "head": {
        "index": 1,
        "name": "Study Plan",
        "date": [2026, 9, 20]
    },
    "main": [
        {
            "name": "Section A",
            "info": "Description",
            "plan": [null, {"is_active": true, "content": "Task 1", "t_m": 5}],
            "group": {}
        }
    ],
    "log": [
        {"day": 0, "plan": "A1", "time": [10, 30], "content": "Started"}
    ]
}
```

### Task ID Format

Task IDs combine section letter + task number:
- `A1` = first task in section A (first section)
- `B3` = third task in section B (second section)

### Time Storage

- `t_m`: Time measured in 6-minute blocks. Actual minutes = `t_m * 6`
- Log time: `[hour, minute]` where minute=99 means fuzzy time (hour-level precision)
