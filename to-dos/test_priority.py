"""
    ============ test_priority.py ============
    to-dos v0.5.0 优先排位分算法测试
        by spinner-bot
"""

import sys
import math
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from src.types import Todo, Category, Priority, TodoStatus
from src.priority import (
    calc_priority_score,
    format_score_display,
    calc_category_score,
    calc_all_scores,
)


def run_tests():
    print("=" * 50)
    print("  to-dos v0.5.0 优先排位分算法测试")
    print("=" * 50)

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

    # ========== 辅助函数 ==========

    def make_todo(cat_id=None, **kwargs):
        defaults = {
            'id': 'TODO-20260920-0001',
            'title': '测试任务',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'priority': Priority.NORMAL,
            'category': cat_id or 'default',
            'status': TodoStatus.PENDING,
            'priority_rank': 0,
            'urgent': False,
            'important': False,
            'estimated_time': 60,
        }
        defaults.update(kwargs)
        return Todo(**defaults)

    def make_category(**kwargs):
        defaults = {
            'id': 'default',
            'name': '默认',
            'color': '#6366f1',
            'icon': 'circle',
            'difficulty': 5,
        }
        defaults.update(kwargs)
        return Category(**defaults)

    # ========== 测试 calc_priority_score ==========

    print("\n--- calc_priority_score ---")

    # 测试已过期待办
    now = datetime.now()
    todo_expired = make_todo(
        deadline=(now - timedelta(hours=1)).isoformat(),
        start_time=(now - timedelta(hours=2)).isoformat(),
    )
    cat = make_category()
    score = calc_priority_score(todo_expired, cat, now)
    check("已过期待办返回 -1", score == -1)

    # 测试无效时间范围
    todo_invalid = make_todo(
        deadline=(now + timedelta(hours=1)).isoformat(),
        start_time=(now + timedelta(hours=2)).isoformat(),
    )
    score = calc_priority_score(todo_invalid, cat, now)
    check("无效时间范围返回 0", score == 0)

    # 测试无截止日期
    todo_no_deadline = make_todo(deadline=None)
    score = calc_priority_score(todo_no_deadline, cat)
    check("无截止日期返回 0", score == 0)

    # 测试难度=0
    todo_zero_diff = make_todo(
        start_time=(now - timedelta(minutes=30)).isoformat(),
        deadline=(now + timedelta(hours=1)).isoformat(),
        priority_rank=2,
        urgent=True,
        important=True,
    )
    cat_zero = make_category(difficulty=0)
    score = calc_priority_score(todo_zero_diff, cat_zero, now)
    check("难度=0 正常计算", score > 0)

    # 测试优先级影响
    start = (now - timedelta(minutes=30)).isoformat()
    deadline = (now + timedelta(hours=2)).isoformat()

    todo_low = make_todo(start_time=start, deadline=deadline,
                         priority_rank=0, urgent=True, important=True)
    todo_high = make_todo(id='TODO-0002', start_time=start, deadline=deadline,
                          priority_rank=5, urgent=True, important=True)
    cat5 = make_category(difficulty=5)

    score_low = calc_priority_score(todo_low, cat5, now)
    score_high = calc_priority_score(todo_high, cat5, now)
    check("高优先级得到更高分", score_high > score_low)

    # 测试紧急+重要加分
    todo_normal = make_todo(start_time=start, deadline=deadline,
                            urgent=False, important=False)
    todo_ui = make_todo(id='TODO-0003', start_time=start, deadline=deadline,
                        urgent=True, important=True)

    score_normal = calc_priority_score(todo_normal, cat5, now)
    score_ui = calc_priority_score(todo_ui, cat5, now)
    check("紧急+重要有额外加分", score_ui > score_normal)

    # 测试不同难度
    todo_diff = make_todo(start_time=start, deadline=deadline,
                          priority_rank=3, urgent=True, important=True)
    cat_easy = make_category(id='easy', difficulty=1)
    cat_hard = make_category(id='hard', difficulty=10)

    score_easy = calc_priority_score(todo_diff, cat_easy, now)
    score_hard = calc_priority_score(todo_diff, cat_hard, now)
    check("不同难度产生不同分数", score_easy != score_hard)
    check("难度=1 分数 > 0", score_easy > 0)
    check("难度=10 分数 > 0", score_hard > 0)

    # ========== 测试 format_score_display ==========

    print("\n--- format_score_display ---")

    check("负数显示 '过期'", format_score_display(-1) == "过期")
    check("零分显示 '0'", format_score_display(0) == "0")
    check("小分数直接显示", format_score_display(1234) == "1234")
    check("小分数直接显示", format_score_display(999999) == "999999")

    result_large = format_score_display(500000000)  # 5e8
    check("大分数使用 EL 前缀", result_large.startswith("EL"))

    score_huge = int(1e10) + 500
    result_huge = format_score_display(score_huge)
    check("超大分数使用 EL 前缀", result_huge.startswith("EL"))
    check("超大分数包含 5.0", "5.0" in result_huge)

    # ========== 测试 calc_category_score ==========

    print("\n--- calc_category_score ---")

    todos_cat = [
        make_todo('work', start_time=start, deadline=deadline,
                  urgent=True, important=True),
        make_todo('work', id='TODO-work-0002',
                  start_time=start, deadline=deadline, urgent=True),
    ]
    categories = [make_category(id='work', name='工作', difficulty=5)]

    scores = calc_category_score(todos_cat, categories, now)
    check("分类在结果中", 'work' in scores)
    check("分类分数 > 0", scores.get('work', 0) > 0)

    # 测试排除已完成待办
    todos_mixed = [
        make_todo('work', start_time=start, deadline=deadline),
        make_todo('work', id='TODO-work-0003',
                  status=TodoStatus.COMPLETED,
                  start_time=start, deadline=deadline),
    ]
    scores = calc_category_score(todos_mixed, categories, now)
    check("已完成待办不参与计算", 'work' in scores)

    # 测试空分类
    scores_empty = calc_category_score([], categories)
    check("空分类不在结果中", 'work' not in scores_empty)

    # ========== 测试 calc_all_scores ==========

    print("\n--- calc_all_scores ---")

    todos_all = [
        Todo(
            id='TODO-001', title='A',
            created_at=now.isoformat(), updated_at=now.isoformat(),
            category='work', start_time=start, deadline=deadline,
        ),
        Todo(
            id='TODO-002', title='B',
            created_at=now.isoformat(), updated_at=now.isoformat(),
            category='study', start_time=start, deadline=deadline,
        ),
    ]
    categories_all = [
        make_category(id='work', name='工作', difficulty=5),
        make_category(id='study', name='学习', difficulty=3),
    ]

    all_scores = calc_all_scores(todos_all, categories_all, now)
    check("返回所有待办分数", 'TODO-001' in all_scores and 'TODO-002' in all_scores)

    # ========== 测试数据模型新字段 ==========

    print("\n--- 数据模型新字段 ---")

    todo_new = Todo(
        id='TODO-NEW',
        title='新字段测试',
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
        priority_rank=3,
        urgent=True,
        important=False,
        start_time=now.isoformat(),
        estimated_time=120,
    )
    check("priority_rank 字段", todo_new.priority_rank == 3)
    check("urgent 字段", todo_new.urgent is True)
    check("important 字段", todo_new.important is False)
    check("start_time 字段", todo_new.start_time is not None)
    check("estimated_time 字段", todo_new.estimated_time == 120)

    d = todo_new.to_dict()
    check("to_dict 包含新字段", 'priority_rank' in d and 'urgent' in d and 'important' in d)

    todo_restored = Todo.from_dict(d)
    check("from_dict 恢复新字段", todo_restored.priority_rank == 3)
    check("from_dict 恢复 urgent", todo_restored.urgent is True)

    cat_new = Category(
        id='test',
        name='测试',
        difficulty=7,
        ascii_icon='T',
        pinned=True,
    )
    check("Category difficulty", cat_new.difficulty == 7)
    check("Category ascii_icon", cat_new.ascii_icon == 'T')
    check("Category pinned", cat_new.pinned is True)

    cat_d = cat_new.to_dict()
    check("Category to_dict 包含新字段", 'difficulty' in cat_d and 'ascii_icon' in cat_d)

    cat_restored = Category.from_dict(cat_d)
    check("Category from_dict 恢复新字段", cat_restored.difficulty == 7)
    check("Category from_dict 恢复 ascii_icon", cat_restored.ascii_icon == 'T')

    # ========== 测试日期格式 ==========

    print("\n--- 日期格式 ---")

    from src.utils import TimeHelper

    check("DATE_FORMAT 是 yyyy/mm/dd", TimeHelper.DATE_FORMAT == '%Y/%m/%d')
    check("today_str 使用 /", '/' in TimeHelper.today_str())

    dt = datetime(2026, 9, 20, 14, 30)
    check("format_date", TimeHelper.format_date(dt) == "2026/09/20")
    check("format_datetime", TimeHelper.format_datetime(dt) == "2026/09/20 14:30")

    parsed = TimeHelper.parse_display("2026/09/20")
    check("parse_display 日期", parsed is not None and parsed.year == 2026)

    parsed2 = TimeHelper.parse_display("2026/09/20 14:30")
    check("parse_display 日期时间", parsed2 is not None and parsed2.hour == 14)

    iso_str = "2026-09-20T14:30:00"
    display = TimeHelper.iso_to_display(iso_str)
    check("iso_to_display", display == "2026/09/20 14:30")

    display_str = "2026/09/20 14:30"
    iso_result = TimeHelper.display_to_iso(display_str)
    check("display_to_iso", iso_result is not None and "2026-09-20" in iso_result)

    # ========== 汇总 ==========

    print("\n" + "=" * 50)
    print(f"  测试完成: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
