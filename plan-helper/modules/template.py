"""
    ====== modules/template.py ======
    Template system for plan-helper.
    Provides pre-defined plan templates (workday, weekend, custom),
    quick copy functionality, smart suggestions, and conflict detection.
        by spinner-bot
"""

import json
import copy
from datetime import datetime, date, timedelta
from pathlib import Path
from . import plan as plan_module
from . import api


# ==========================================
# Built-in Templates
# ==========================================

WORKDAY_TEMPLATE = {
    "name": "工作日计划",
    "description": "标准工作日计划模板，包含学习、工作、休息时间段",
    "type": "workday",
    "sections": [
        {
            "name": "上午 - 核心工作",
            "info": "高效时间段，安排重要任务",
            "tasks": [
                {"content": "晨间规划与回顾", "time_minutes": 15},
                {"content": "核心任务 1（深度工作）", "time_minutes": 90},
                {"content": "短暂休息", "time_minutes": 15},
                {"content": "核心任务 2（深度工作）", "time_minutes": 90},
            ],
            "groups": [
                {"title": "上午深度工作", "description": "集中精力完成核心任务", "start": 1, "end": 4}
            ]
        },
        {
            "name": "下午 - 协作与执行",
            "info": "适合会议、沟通、常规工作",
            "tasks": [
                {"content": "午餐与休息", "time_minutes": 60},
                {"content": "常规任务处理", "time_minutes": 60},
                {"content": "会议/沟通时间", "time_minutes": 45},
                {"content": "项目推进", "time_minutes": 60},
            ],
            "groups": []
        },
        {
            "name": "晚间 - 学习与复盘",
            "info": "低强度但高价值的活动",
            "tasks": [
                {"content": "学习新技能/阅读", "time_minutes": 45},
                {"content": "当日复盘与明日规划", "time_minutes": 20},
            ],
            "groups": []
        }
    ]
}

WEEKEND_TEMPLATE = {
    "name": "休息日计划",
    "description": "休息日计划模板，注重平衡与充电",
    "type": "weekend",
    "sections": [
        {
            "name": "上午 - 个人成长",
            "info": "利用清醒头脑进行自我提升",
            "tasks": [
                {"content": "运动/锻炼", "time_minutes": 60},
                {"content": "阅读/学习", "time_minutes": 90},
                {"content": "个人项目", "time_minutes": 60},
            ],
            "groups": []
        },
        {
            "name": "下午 - 休闲与社交",
            "info": "放松身心，保持社交",
            "tasks": [
                {"content": "休闲活动", "time_minutes": 120},
                {"content": "社交/家庭时间", "time_minutes": 120},
            ],
            "groups": []
        },
        {
            "name": "晚间 - 放松",
            "info": "为新一周做准备",
            "tasks": [
                {"content": "轻松娱乐", "time_minutes": 90},
                {"content": "下周计划预览", "time_minutes": 20},
            ],
            "groups": []
        }
    ]
}

EXAM_PREP_TEMPLATE = {
    "name": "备考冲刺计划",
    "description": "考试冲刺阶段高强度复习计划",
    "type": "exam",
    "sections": [
        {
            "name": "上午 - 重点突破",
            "info": "攻克薄弱科目",
            "tasks": [
                {"content": "知识点回顾", "time_minutes": 30},
                {"content": "专题训练 1", "time_minutes": 90},
                {"content": "休息", "time_minutes": 10},
                {"content": "专题训练 2", "time_minutes": 90},
            ],
            "groups": [
                {"title": "上午冲刺", "description": "高强度专题训练", "start": 1, "end": 4}
            ]
        },
        {
            "name": "下午 - 模拟练习",
            "info": "真题模拟与错题分析",
            "tasks": [
                {"content": "模拟考试", "time_minutes": 120},
                {"content": "错题分析", "time_minutes": 60},
            ],
            "groups": []
        },
        {
            "name": "晚间 - 巩固",
            "info": "轻量复习，保证睡眠",
            "tasks": [
                {"content": "轻松复习笔记", "time_minutes": 45},
                {"content": "整理明日重点", "time_minutes": 15},
            ],
            "groups": []
        }
    ]
}


# ==========================================
# Template Registry
# ==========================================

TEMPLATES = {
    "workday": WORKDAY_TEMPLATE,
    "weekend": WEEKEND_TEMPLATE,
    "exam": EXAM_PREP_TEMPLATE,
}

CUSTOM_TEMPLATES = {}


def list_templates():
    """List all available templates."""
    result = []
    for key, tmpl in TEMPLATES.items():
        result.append({
            "id": key,
            "name": tmpl["name"],
            "description": tmpl["description"],
            "type": tmpl["type"],
            "built_in": True,
        })
    for key, tmpl in CUSTOM_TEMPLATES.items():
        result.append({
            "id": key,
            "name": tmpl["name"],
            "description": tmpl.get("description", ""),
            "type": tmpl.get("type", "custom"),
            "built_in": False,
        })
    return api.success_response(data={"templates": result, "count": len(result)})


def get_template(template_id):
    """Get a template by ID."""
    if template_id in TEMPLATES:
        return api.success_response(data={"template": TEMPLATES[template_id]})
    elif template_id in CUSTOM_TEMPLATES:
        return api.success_response(data={"template": CUSTOM_TEMPLATES[template_id]})
    else:
        return api.error_response(f"Template '{template_id}' not found", code=404)


def save_custom_template(template_id, template_data):
    """Save a custom template."""
    try:
        if template_id in TEMPLATES:
            return api.error_response(f"Cannot overwrite built-in template '{template_id}'", code=409)
        CUSTOM_TEMPLATES[template_id] = template_data
        return api.success_response(
            data={"template_id": template_id, "saved": True},
            code=201
        )
    except Exception as e:
        return api.error_response(str(e))


def delete_custom_template(template_id):
    """Delete a custom template."""
    if template_id in TEMPLATES:
        return api.error_response("Cannot delete built-in templates", code=403)
    if template_id in CUSTOM_TEMPLATES:
        CUSTOM_TEMPLATES.pop(template_id)
        return api.success_response(data={"template_id": template_id, "deleted": True})
    return api.error_response(f"Template '{template_id}' not found", code=404)


# ==========================================
# Apply Template
# ==========================================

def apply_template(template_id, plan_name=None, plan_date=None, plan_id=None):
    """
    Create a new plan from a template.
    Returns APIResponse with the created plan data.
    """
    try:
        # Get template
        if template_id in TEMPLATES:
            tmpl = TEMPLATES[template_id]
        elif template_id in CUSTOM_TEMPLATES:
            tmpl = CUSTOM_TEMPLATES[template_id]
        else:
            return api.error_response(f"Template '{template_id}' not found", code=404)

        # Create plan
        resp = api.create_plan(
            name=plan_name or tmpl["name"],
            date_tuple=plan_date,
            plan_id=plan_id
        )
        if not resp.success:
            return resp

        plan_id_val = resp.data["id"]

        # Add sections and tasks
        for sec_data in tmpl.get("sections", []):
            sec_resp = api.add_section(plan_id_val, sec_data["name"], sec_data.get("info", ""))
            if not sec_resp.success:
                continue

            sec_idx = sec_resp.data["section_index"]

            for task_data in sec_data.get("tasks", []):
                api.add_task(plan_id_val, sec_idx, task_data["content"], task_data["time_minutes"])

            # Add groups
            for group_data in sec_data.get("groups", []):
                p = plan_module.Plan.registry.get(plan_id_val)
                if p:
                    p.add_group(
                        sec_idx,
                        group_data["title"],
                        group_data.get("description", ""),
                        group_data["start"],
                        group_data["end"]
                    )

        return api.get_plan_full(plan_id_val)
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Quick Copy (复制昨日计划)
# ==========================================

def copy_plan(source_plan_id, new_name=None, new_date=None, new_id=None):
    """
    Copy an existing plan to create a new one.
    Deep copies all sections, tasks, and groups (but not logs).
    """
    try:
        source_plan_id = int(source_plan_id)
        if source_plan_id not in plan_module.Plan.registry:
            return api.error_response(f"Source plan {source_plan_id} not found", code=404)

        source = plan_module.Plan.registry[source_plan_id]
        source_data = copy.deepcopy(source.plan)

        # Create new plan
        if new_date is None:
            today = date.today()
            new_date = (today.year, today.month, today.day)
        if new_name is None:
            new_name = source_data["head"].get("name", "Copied Plan") + " (副本)"

        resp = api.create_plan(name=new_name, date_tuple=new_date, plan_id=new_id)
        if not resp.success:
            return resp

        new_plan_id = resp.data["id"]
        new_plan = plan_module.Plan.registry[new_plan_id]

        # Copy sections and tasks
        for sec in source_data.get("main", []):
            new_plan.add_section(sec.get("name", ""), sec.get("info", ""))
            sec_idx = len(new_plan.plan["main"]) - 1

            for task_idx, task in enumerate(sec.get("plan", [])):
                if task is None or task_idx == 0:
                    continue
                new_plan.add_plan(sec_idx, task.get("content", ""), task.get("t_m", 0))

            # Copy groups
            for key, val in sec.get("group", {}).items():
                try:
                    pre, last = map(int, key.split("_"))
                    new_plan.add_group(sec_idx, val.get("title", ""), val.get("description", ""), pre, last)
                except (ValueError, KeyError):
                    continue

        return api.get_plan_full(new_plan_id)
    except Exception as e:
        return api.error_response(str(e))


def copy_yesterday_plan(anchor_date=None, new_id=None):
    """
    Find yesterday's plan and copy it.
    Looks through registry for plans dated yesterday.
    """
    try:
        if anchor_date is None:
            yesterday = date.today() - timedelta(days=1)
        else:
            yesterday = date(*anchor_date) - timedelta(days=1)

        yesterday_tuple = (yesterday.year, yesterday.month, yesterday.day)

        # Find plan(s) from yesterday
        candidates = []
        for idx, p in plan_module.Plan.registry.items():
            plan_date = p.plan["head"].get("date")
            if plan_date and tuple(plan_date) == yesterday_tuple:
                candidates.append(p)

        if not candidates:
            return api.error_response("No plan found for yesterday", code=404)

        # Copy the first match (or the one with most tasks)
        best = max(candidates, key=lambda p: sum(
            sum(1 for t in s.get("plan", []) if t and t.get("is_active"))
            for s in p.plan["main"]
        ))

        today = date.today()
        return copy_plan(
            best.index,
            new_name=best.plan["head"].get("name", "计划") + f" ({today.month}/{today.day})",
            new_date=(today.year, today.month, today.day),
            new_id=new_id
        )
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Smart Suggestions
# ==========================================

def suggest_plan_based_on_history(days=7):
    """
    Analyze recent plan history and suggest a plan template.
    Based on:
    - What days of week have the most plans
    - Which templates are used most
    - Common sections and tasks
    """
    try:
        all_plans = list(plan_module.Plan.registry.values())
        if not all_plans:
            return api.success_response(data={
                "suggestion": None,
                "message": "No plan history available. Try creating a plan first!",
                "recommended_template": "workday"
            })

        # Analyze patterns
        task_frequency = {}
        section_frequency = {}
        total_plans = len(all_plans)

        for p in all_plans:
            for sec in p.plan.get("main", []):
                sec_name = sec.get("name", "")
                section_frequency[sec_name] = section_frequency.get(sec_name, 0) + 1

                for task_idx, task in enumerate(sec.get("plan", [])):
                    if task is None or task_idx == 0:
                        continue
                    content = task.get("content", "")
                    if content:
                        task_frequency[content] = task_frequency.get(content, 0) + 1

        # Top recurring tasks
        top_tasks = sorted(task_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        top_sections = sorted(section_frequency.items(), key=lambda x: x[1], reverse=True)[:3]

        # Determine day of week pattern
        weekday_count = 0
        weekend_count = 0
        for p in all_plans:
            plan_date = p.plan["head"].get("date")
            if plan_date:
                try:
                    d = date(*plan_date)
                    if d.weekday() < 5:
                        weekday_count += 1
                    else:
                        weekend_count += 1
                except (ValueError, TypeError):
                    pass

        recommended = "workday" if weekday_count >= weekend_count else "weekend"

        return api.success_response(data={
            "suggestion": {
                "total_plans": total_plans,
                "recommended_template": recommended,
                "top_recurring_tasks": [{"content": t, "count": c} for t, c in top_tasks],
                "top_sections": [{"name": s, "count": c} for s, c in top_sections],
                "weekday_plans": weekday_count,
                "weekend_plans": weekend_count,
            },
            "message": f"Based on {total_plans} plans, I recommend a {recommended} template."
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Conflict Detection
# ==========================================

def detect_conflicts(plan_id):
    """
    Detect scheduling conflicts within a plan.
    Checks for:
    1. Time overlap between tasks (if total time > available hours)
    2. Duplicate task content
    3. Unreasonable time allocation (> 4 hours single task)
    """
    try:
        plan_id = int(plan_id)
        if plan_id not in plan_module.Plan.registry:
            return api.error_response(f"Plan {plan_id} not found", code=404)

        p = plan_module.Plan.registry[plan_id]
        conflicts = []
        warnings = []

        for sec_idx, sec in enumerate(p.plan["main"]):
            section_letter = chr(ord('A') + sec_idx)
            section_tasks = []
            task_contents = {}

            for task_idx, task in enumerate(sec.get("plan", [])):
                if task is None or task_idx == 0:
                    continue
                if not task.get("is_active", True):
                    continue

                content = task.get("content", "")
                time_mins = round(task.get("t_m", 0) * 6, 1)
                task_id = plan_module.Plan.syn_index(sec_idx, task_idx)

                section_tasks.append({
                    "id": task_id,
                    "content": content,
                    "time_minutes": time_mins,
                })

                # Check for duplicate content
                if content in task_contents:
                    conflicts.append({
                        "type": "duplicate_task",
                        "section": section_letter,
                        "message": f"任务 '{content}' 在章节 {section_letter} 中重复出现 (已有 {task_contents[content]})",
                        "tasks": [task_contents[content], task_id],
                    })
                else:
                    task_contents[content] = task_id

                # Check for unreasonable time allocation
                if time_mins > 240:  # > 4 hours
                    warnings.append({
                        "type": "long_task",
                        "section": section_letter,
                        "task_id": task_id,
                        "message": f"任务 {task_id} 预计耗时 {time_mins} 分钟，超过 4 小时，建议拆分",
                        "time_minutes": time_mins,
                    })

            # Check section time overflow (> 10 hours in one section)
            section_total = sum(t["time_minutes"] for t in section_tasks)
            if section_total > 600:
                warnings.append({
                    "type": "section_overflow",
                    "section": section_letter,
                    "message": f"章节 {section_letter} 总时长 {section_total} 分钟 ({round(section_total/60, 1)} 小时)，超过 10 小时",
                    "total_minutes": section_total,
                })

        # Check overall plan time
        total_h, total_6m = p.time_sum()
        total_hours = total_h + (total_6m * 6) / 60
        if total_hours > 16:
            warnings.append({
                "type": "plan_overflow",
                "message": f"计划总时长 {round(total_hours, 1)} 小时，超过 16 小时，请确认是否合理",
                "total_hours": round(total_hours, 1),
            })

        return api.success_response(data={
            "plan_id": plan_id,
            "conflicts": conflicts,
            "warnings": warnings,
            "conflict_count": len(conflicts),
            "warning_count": len(warnings),
            "has_issues": len(conflicts) > 0 or len(warnings) > 0,
        })
    except Exception as e:
        return api.error_response(str(e))


# ==========================================
# Template Persistence
# ==========================================

def save_templates_to_file(path="data/templates/custom_templates.json"):
    """Save custom templates to disk."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(CUSTOM_TEMPLATES, f, indent=2, ensure_ascii=False)
        return api.success_response(data={"path": str(path), "count": len(CUSTOM_TEMPLATES)})
    except Exception as e:
        return api.error_response(str(e))


def load_templates_from_file(path="data/templates/custom_templates.json"):
    """Load custom templates from disk."""
    try:
        p = Path(path)
        if not p.exists():
            return api.success_response(data={"message": "No custom templates file found", "count": 0})
        with open(p, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        CUSTOM_TEMPLATES.update(loaded)
        return api.success_response(data={"loaded": len(loaded), "total": len(CUSTOM_TEMPLATES)})
    except Exception as e:
        return api.error_response(str(e))
