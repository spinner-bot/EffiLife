from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk"


def test_category_preview_uses_bounded_icon_registry():
    preview = (DESK / "src" / "components" / "CategoryIconPreview.vue").read_text(encoding="utf-8")
    registry = (DESK / "src" / "components" / "categoryIcons.ts").read_text(encoding="utf-8")

    assert "icons as lucideIcons" not in preview
    assert "categoryIconRegistry" in preview
    assert "export const categoryIcons" in registry


def test_task_center_lazy_loads_optional_category_editors():
    source = (DESK / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")

    assert "defineAsyncComponent" in source
    assert "import('@/components/CategoryIconPicker.vue')" in source
    assert "import('@/components/CategoryIconPreview.vue')" in source
