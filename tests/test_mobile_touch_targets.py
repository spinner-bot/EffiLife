from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_primary_actions_have_touch_friendly_targets():
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    records = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    home = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")

    assert ".event-task-actions button, .group-action { min-width: 40px; min-height: 40px;" in plans
    assert ".task-complete { width: 32px; height: 32px; }" in plans
    assert ".icon-btn { width: 40px; height: 40px; }" in records
    assert ".task-item-actions > button, .task-rank-control button { min-width: 40px; min-height: 40px; }" in tasks
    assert ".category-row > button { min-width: 40px; min-height: 40px; }" in tasks
    assert ".today-todo-complete { width: 32px; height: 32px; }" in home
    assert ".today-todo-record { width: 40px; height: 40px; }" in home
