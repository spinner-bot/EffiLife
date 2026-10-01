from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_legacy_time_workspace_preserves_exact_midnight_boundary():
    assert "eh > 24 || (eh === 24 && em !== 0)" in VIEW
    assert "const endsAtMidnight = endMins === 24 * 60" in VIEW
    assert "endMinutes = endsAtMidnight ? 24 * 60 : endMins % (24 * 60)" in VIEW
    assert 'v-model="formEnd.h" min="0" max="24"' in VIEW


def test_legacy_time_workspace_rejects_cross_midnight_duration():
    assert "refMinutes + totalMinutes > 24 * 60" in VIEW
    assert "refMinutes - totalMinutes < 0" in VIEW
    assert "t('legacyPlan.validationCrossesMidnight')" in VIEW
    assert I18N.count("'legacyPlan.validationCrossesMidnight':") == 2
