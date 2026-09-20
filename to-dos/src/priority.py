"""
to-dos 优先排位分算法模块 (v0.5.0)

核心算法：计算待办事项的优先排位分，用于动态排序

特点：
- 全程使用对数域计算，避免大数溢出
- 综合考虑优先级、紧急度、重要度、时间充裕度
- 支持实时计算和格式化显示
"""

import math
from datetime import datetime
from typing import Optional

from .types import Todo, Category
from .utils import TimeHelper


def calc_priority_score(
    todo: Todo,
    category: Category,
    now: Optional[datetime] = None,
) -> int:
    """
    计算优先排位分，使用对数域避免大数

    参数：
        todo: 待办事项
        category: 所属分类
        now: 当前时间，默认为 datetime.now()

    返回：
        优先排位分（整数）

    算法说明：
        1. 校验：已过期返回 -inf，无效时间范围返回 0
        2. 计算时间差（分钟）：total_time, remaining_time
        3. 评估时间（对数域）：基于难度和优先级
        4. 评估充裕度：剩余时间 vs 评估时间
        5. 标定充裕度：剩余时间 vs 预估时间
        6. 时间充裕度：几何平均 + 调和平均组合
        7. 基础优先度：基于重要度和紧急度
        8. 优先排位分：对数域计算最终分数
        9. 软封顶：超过 1e10 使用对数压缩
    """
    if now is None:
        now = datetime.now()

    # 解析时间
    deadline_dt = TimeHelper.parse_iso(todo.deadline) if todo.deadline else None
    start_time_str = todo.start_time or todo.created_at
    start_dt = TimeHelper.parse_iso(start_time_str)

    # 校验：已过期
    if deadline_dt and deadline_dt <= now:
        return -1  # 已过期，返回 -1 表示最低优先级

    # 校验：无效时间范围
    if not deadline_dt or not start_dt or deadline_dt <= start_dt:
        return 0

    # 难度和优先级
    difficulty = category.difficulty
    priority = todo.priority_rank

    # 时间差（分钟）
    total_time = (deadline_dt - start_dt).total_seconds() / 60
    remaining_time = (deadline_dt - now).total_seconds() / 60

    # 评估时间（对数域）
    if difficulty == 0:
        log_eval_time = 0  # 瞬间完成
    else:
        base = 1 - (50 / (difficulty + 50)) ** priority
        if base <= 0:
            log_eval_time = math.log(0.001)  # 避免 log(0)
        else:
            log_eval_time = math.log(base) + math.log(total_time)

    # 评估充裕度
    log_eval_sufficiency = math.log(max(remaining_time, 0.001)) - log_eval_time

    # 标定时间
    estimated_time = todo.estimated_time or todo.time_estimate or 60
    calibrate_time = min(total_time, estimated_time)
    log_calibrate_sufficiency = (
        math.log(max(remaining_time, 0.001)) - math.log(max(calibrate_time, 0.001))
    )

    # 时间充裕度（几何平均 + 调和平均组合）
    eval_suff = math.exp(log_eval_sufficiency)
    calibrate_suff = math.exp(log_calibrate_sufficiency)

    time_sufficiency = (
        0.65 * math.exp(0.5 * log_eval_sufficiency + 0.5 * log_calibrate_sufficiency)
        + 0.7 * eval_suff * calibrate_suff / (eval_suff + calibrate_suff + 0.001)
    )

    # 基础优先度
    importance_score = (145 + difficulty) if todo.important else 0
    urgency_score = (1335 + 3 * difficulty) if todo.urgent else 1000
    base_priority = (importance_score + urgency_score) / max(time_sufficiency, 0.001)

    # 优先排位分（对数域）
    multiplier = 1.06 ** priority + 1.35 * (priority ** 1.5) - 1
    if multiplier <= 0:
        multiplier = 0.001

    log_score = math.log(max(base_priority, 0.001)) + math.log(max(multiplier, 0.001))
    score = math.exp(log_score)

    # 软封顶（对数压缩）
    if score > 1e10:
        score = int(1e10 + 100 * math.log10(score) + 0.5)
    else:
        score = int(score + 0.5)

    return score


def format_score_display(score: int) -> str:
    """
    格式化分数显示

    参数：
        score: 优先排位分

    返回：
        格式化后的分数字符串

    规则：
        - score >= 1e10: 显示为 EL{number}，number = (score - 1e10) / 100
        - score >= 1e8: 显示为 EL{log10(score)}
        - score < 1e8: 直接显示数字
        - score < 0: 显示 "过期"
    """
    if score < 0:
        return "过期"
    elif score == 0:
        return "0"
    elif score >= 1e10:
        number = (score - 1e10) / 100
        return f"EL{number:.1f}"
    elif score >= 1e8:
        number = math.log10(score)
        return f"EL{number:.1f}"
    else:
        return str(score)


def calc_category_score(
    todos: list,
    categories: list,
    now: Optional[datetime] = None,
) -> dict:
    """
    计算每个分类的优先排位分

    参数：
        todos: 待办列表
        categories: 分类列表
        now: 当前时间

    返回：
        分类 ID 到分数的映射 {category_id: score}

    算法：
        分类分数 = sum(该分类下所有待办的分数) / sqrt(待办数量)
    """
    if now is None:
        now = datetime.now()

    # 构建分类映射
    category_map = {c.id: c for c in categories}

    # 计算每个分类的分数
    category_scores = {}
    category_counts = {}

    for todo in todos:
        # 跳过已完成、已取消、已归档的待办
        if todo.status.value in ('completed', 'cancelled', 'archived'):
            continue

        cat_id = todo.category
        category = category_map.get(cat_id)
        if not category:
            continue

        score = calc_priority_score(todo, category, now)

        if cat_id not in category_scores:
            category_scores[cat_id] = 0
            category_counts[cat_id] = 0

        category_scores[cat_id] += score
        category_counts[cat_id] += 1

    # 计算最终分数：sum / sqrt(count)
    result = {}
    for cat_id, total_score in category_scores.items():
        count = category_counts[cat_id]
        if count > 0:
            result[cat_id] = total_score / math.sqrt(count)
        else:
            result[cat_id] = 0

    return result


def calc_all_scores(
    todos: list,
    categories: list,
    now: Optional[datetime] = None,
) -> dict:
    """
    计算所有待办的优先排位分

    参数：
        todos: 待办列表
        categories: 分类列表
        now: 当前时间

    返回：
        待办 ID 到分数的映射 {todo_id: score}
    """
    if now is None:
        now = datetime.now()

    # 构建分类映射
    category_map = {c.id: c for c in categories}

    scores = {}
    for todo in todos:
        category = category_map.get(todo.category)
        if category:
            scores[todo.id] = calc_priority_score(todo, category, now)
        else:
            scores[todo.id] = 0

    return scores
