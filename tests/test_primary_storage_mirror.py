from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts"


def test_legacy_local_storage_mirror_cannot_fail_primary_writes():
    source = DATA_SERVICE.read_text(encoding="utf-8")
    assert "function writeLegacyMirror(key: string, value: unknown): void" in source
    mirror = source.split("function writeLegacyMirror", 1)[1].split("export const DataService", 1)[0]
    assert "try {" in mirror
    assert "localStorage.setItem(key, JSON.stringify(value))" in mirror
    assert "catch (error)" in mirror
    assert "console.warn(`Failed to update legacy storage mirror" in mirror


def test_canonical_saves_write_indexed_db_before_the_compatibility_mirror():
    source = DATA_SERVICE.read_text(encoding="utf-8")
    for marker in (
        "async saveConfig(config: Config)",
        "async savePlans(plans: Plans)",
        "async saveScheduleRules(rules: ScheduleRule[])",
        "async saveManualPlans(plans: ManualPlans)",
        "async saveRecord(record: TimeRecord, day?: string)",
    ):
        block = source.split(marker, 1)[1].split("\n  },", 1)[0]
        assert "await idbSet" in block
        assert "writeLegacyMirror" in block
        assert block.index("await idbSet") < block.index("writeLegacyMirror")
