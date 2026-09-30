from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = (ROOT / "time-helper/desk/src/services/planGateway.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_mobile_gateway_lists_and_mutates_local_plan_archives():
    assert "async function getMobileRawArchives()" in GATEWAY
    assert "if (getPlanRuntime() === 'mobile-unavailable')" in GATEWAY
    assert "archives.push({" in GATEWAY
    assert "await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives', archives)" in GATEWAY
    assert "const sourcePlan = archive?.payload?.plan" in GATEWAY
    assert "const sourceIdIsFree = Number.isInteger(sourceId)" in GATEWAY
    assert "const nextId = sourceIdIsFree" in GATEWAY
    assert "restored.head = { ...(restored.head || {}), index: nextId }" in GATEWAY
    assert "linked_todos: linkedTodos" in GATEWAY
    assert "archive.payload?.linked_todos" in GATEWAY
    assert "related_plan_id: String(nextId)" in GATEWAY


def test_mobile_archive_copy_is_localized_as_snapshot_capability():
    assert I18N.count("'settings.archive.mobilePlanDescription':") == 2
    assert "including active and archived plans" in I18N
    assert "包含活动计划与已归档计划" in I18N
