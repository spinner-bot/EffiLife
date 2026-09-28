from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
PREVIEW = ROOT / "time-helper" / "desk" / "src" / "components" / "CategoryIconPreview.vue"


def test_category_icon_preview_supports_lucide_and_ascii_fallbacks():
    source = PREVIEW.read_text(encoding="utf-8")
    assert "icons as lucideIcons" in source
    assert "toPascalCase" in source
    assert "v-if=\"ascii\"" in source
    assert "|| Circle" in source


def test_task_center_renders_category_icon_in_list_and_badge():
    source = TASKS.read_text(encoding="utf-8")
    assert source.count("<CategoryIconPreview") >= 2
    assert ":ascii=\"item.ascii_icon\"" in source
    assert ".task-category { display: inline-flex" in source
