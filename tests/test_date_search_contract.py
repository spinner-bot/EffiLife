from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "services" / "dateSearch.ts").read_text(encoding="utf-8")


def test_date_search_emits_padded_and_unpadded_common_formats():
    assert "`${year}-${paddedMonth}-${paddedDay}`" in SOURCE
    assert "`${year}/${paddedMonth}/${paddedDay}`" in SOURCE
    assert "`${year}.${paddedMonth}.${paddedDay}`" in SOURCE
    assert "`${year}-${month}-${day}`" in SOURCE


def test_date_search_rejects_malformed_input_without_throwing():
    assert "if (!Array.isArray(date) || date.length < 3) return []" in SOURCE
    assert "!Number.isFinite(part) || !Number.isInteger(part)" in SOURCE
