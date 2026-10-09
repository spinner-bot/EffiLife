from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_mobile_home_empty_state_describes_snapshot_availability_not_missing_service():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("home.eventPlansUnavailableMobile") == 2
    assert "移动端事件计划服务尚未接入" not in source
    assert "Mobile event-plan service is not available yet" not in source
    assert "移动端暂无可用的本地计划快照" in source
    assert "No local plan snapshot is available on this device" in source


def test_mobile_plan_capability_copy_does_not_claim_read_only_or_unavailable_editing():
    source = I18N.read_text(encoding="utf-8")
    assert "移动端暂未接入兼容原始 plan 模型的本地计划服务" not in source
    assert "Mobile plan service support for the original plan model is not available yet" not in source
    assert "编辑会直接写回本地快照" in source
    assert "Edits are saved locally" in source


def test_mobile_plan_archive_panel_explains_desktop_archive_boundary():
    view = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert view.count("archive-capability-note") == 1
    assert "v-if=\"mobilePlanRuntime\" class=\"plans-readonly-note archive-capability-note\"" in view
    assert "const canArchivePlan = computed(() => canEditPlan.value)" in view
    assert "archive and restore require the desktop plan service" not in view
    assert "v-else-if=\"archives.length === 0\"" in view
