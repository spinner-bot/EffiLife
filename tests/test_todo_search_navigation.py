from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_todo_deep_links_reveal_completed_and_archived_items_in_visible_filters():
    assert "if (target.status === 'completed') filter.value = 'completed'" in VIEW
    assert "else if (target.status === 'archived' || target.status === 'cancelled') filter.value = 'all'" in VIEW
    assert "else filter.value = 'active'" in VIEW

