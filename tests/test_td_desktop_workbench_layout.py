from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")


def test_td_wide_layout_separates_controls_from_task_results():
    assert ".task-content { display: grid; grid-template-columns: minmax(270px, .36fr) minmax(0, 1fr);" in VIEW
    assert ".task-create, .task-toolbar, .task-category-nav, .category-manager { grid-column: 1; }" in VIEW
    assert ".task-list, .task-result-state { grid-column: 2; grid-row: 1 / span 4;" in VIEW


def test_td_result_states_keep_a_named_layout_target():
    assert 'class="task-empty task-result-state theme-card"' in VIEW
    assert 'class="task-empty task-result-state task-unavailable theme-card"' in VIEW
