from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_plan_detail_editors_protect_route_navigation():
    assert "import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'" in VIEW
    assert "const planEditorInitialDraft = ref('')" in VIEW
    assert "function currentPlanEditorDraft(): string" in VIEW
    assert "function isPlanEditorDirty(): boolean" in VIEW
    assert "function startTaskCreate(sectionIndex: number): void" in VIEW
    assert "@click=\"startTaskCreate(section.index)\"" in VIEW
    assert "onBeforeRouteLeave(async () =>" in VIEW
    assert "t('plans.discardEditConfirm')" in VIEW


def test_plan_detail_discard_confirmation_is_localized():
    assert "'plans.discardEditConfirm': '当前计划编辑有未保存的修改，确定放弃吗？'" in I18N
    assert "'plans.discardEditConfirm': 'This plan has unsaved changes. Discard them?'" in I18N
