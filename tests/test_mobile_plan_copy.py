from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_mobile_home_empty_state_describes_snapshot_availability_not_missing_service():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("home.eventPlansUnavailableMobile") == 2
    assert "移动端事件计划服务尚未接入" not in source
    assert "Mobile event-plan service is not available yet" not in source
    assert "移动端暂无可用的本地事件计划快照" in source
    assert "No local event-plan snapshot is available on this device" in source
