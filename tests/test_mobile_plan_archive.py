from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = (ROOT / "time-helper/desk/src/services/planGateway.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_mobile_plan_snapshot_mutations_serialize_the_complete_read_modify_write_cycle():
    assert "let mobilePlanWriteQueue: Promise<unknown> = Promise.resolve()" in GATEWAY
    assert "function enqueueMobilePlanWrite<T>(operation: () => Promise<T>): Promise<T>" in GATEWAY
    assert "return enqueueMobilePlanWrite(async () =>" in GATEWAY
    assert GATEWAY.count("return enqueueMobilePlanWrite(async () =>") >= 2
    assert "await enqueueMobilePlanWrite(async () =>" in GATEWAY


def test_mobile_plan_task_minutes_preserve_fractional_six_minute_units():
    task_unit = GATEWAY.split("function mobileTaskUnit", 1)[1].split("}", 1)[0]
    assert "Number(minutes) || 0) / 6" in task_unit
    assert "Math.round" not in task_unit


def test_mobile_plan_logs_resolve_display_ids_to_stable_internal_ids():
    location = GATEWAY.split("function mobileTaskLocation", 1)[1].split("function mobileTaskUnit", 1)[0]
    log_block = GATEWAY.split("export async function addPlanLog", 1)[1]
    assert "internalId: string" in location
    assert "internalId: `${letter}${internalIndex}`" in location
    assert "mobileTaskLocation(plan, requestedTaskId)?.internalId" in log_block
    assert "plan: resolvedTaskId" in log_block


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
    assert "body: JSON.stringify({ linked_todos: linkedTodos })" in GATEWAY
    assert "restored.restored_from_id" in GATEWAY


def test_mobile_plan_archive_and_restore_roll_back_partial_snapshot_or_link_writes():
    assert "const previousPlans = cloneMobilePlans(plans)" in GATEWAY
    assert "const previousArchives = JSON.parse(JSON.stringify(archives)) as RawArchive[]" in GATEWAY
    assert "Failed to roll back mobile plan archive plans" in GATEWAY
    assert "const updatedTodos = todos.filter" in GATEWAY
    assert "Failed to roll back mobile restored plan todo link" in GATEWAY
    assert "Failed to roll back mobile restored plan:" in GATEWAY
    assert "const updatedTodoIds: string[] = []" in GATEWAY
    assert "Failed to roll back restored plan todo link" in GATEWAY


def test_mobile_archive_copy_is_localized_as_snapshot_capability():
    assert I18N.count("'settings.archive.mobilePlanDescription':") == 2
    assert "including active and archived plans" in I18N
    assert "包含活动计划与已归档计划" in I18N
