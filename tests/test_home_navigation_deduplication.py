from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"


def test_home_quick_actions_keep_only_the_checkin_action():
    source = HOME.read_text(encoding="utf-8")

    assert 'class="home-quick-actions"' in source
    assert "router.push('/checkin')" in source
    assert "router.push('/plans')" not in source.split('<nav class="home-quick-actions"', 1)[1].split('</nav>', 1)[0]
    assert "router.push('/time')" not in source.split('<nav class="home-quick-actions"', 1)[1].split('</nav>', 1)[0]
    assert "router.push('/tasks')" not in source.split('<nav class="home-quick-actions"', 1)[1].split('</nav>', 1)[0]
    assert "router.push('/settings')" not in source.split('<nav class="home-quick-actions"', 1)[1].split('</nav>', 1)[0]
    assert "class=\"nav-buttons\"" not in source


def test_home_click_actions_have_explicit_non_submit_types():
    source = HOME.read_text(encoding="utf-8")
    clickable_buttons = [line for line in source.splitlines() if '<button' in line and '@click' in line]
    assert clickable_buttons
    assert all('type="button"' in line for line in clickable_buttons)
