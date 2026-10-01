from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/RecordsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_duration_records_reject_crossing_midnight_in_both_reference_modes():
    assert "if (refMinutes + totalMinutes > 24 * 60)" in VIEW
    assert "if (refMinutes - totalMinutes < 0)" in VIEW
    assert "t('records.validation.crossesMidnight')" in VIEW


def test_time_records_preserve_exact_midnight_as_a_valid_end_boundary():
    assert "eh > 24 || (eh === 24 && em !== 0)" in VIEW
    assert "const endsAtMidnight = endMins === 24 * 60" in VIEW
    assert "endMinutes = endsAtMidnight ? 24 * 60 : endMins % (24 * 60)" in VIEW
    assert 'v-model="formEnd.h" min="0" max="24"' in VIEW


def test_cross_midnight_record_validation_is_localized():
    assert "'records.validation.crossesMidnight':" in I18N
    assert I18N.count("'records.validation.crossesMidnight':") == 2
