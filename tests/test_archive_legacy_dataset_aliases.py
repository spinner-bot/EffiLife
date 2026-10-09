from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")


def test_frontend_archive_accepts_first_protocol_dataset_aliases():
    assert "declaredDatasets.has('time_records')" in ARCHIVE
    assert "declaredDatasets.has('plans')" in ARCHIVE
    assert "declaredDatasets.has('planHelper')" in ARCHIVE
    assert "declaredDatasets.has('categories')" in ARCHIVE
    assert "datasets.records = datasets.records ?? datasets.time_records" in ARCHIVE
    assert "datasets.plan_helper = datasets.plan_helper || datasets.planHelper" in ARCHIVE
    assert "if (!('todo_categories' in datasets)) datasets.todo_categories = datasets.categories ?? []" in ARCHIVE


def test_frontend_archive_keeps_canonical_dataset_precedence():
    assert "datasets.records = datasets.records ?? datasets.time_records" in ARCHIVE
    assert "datasets.plan_helper = datasets.plan_helper || datasets.planHelper" in ARCHIVE
    assert "const rawPlanHelper = datasets.plan_helper || datasets.planHelper" in ARCHIVE


def test_legacy_archive_preserves_categories_field():
    assert "normalizeImportedCategories(legacy.categories, repairedPlanLinks.todos)" in ARCHIVE
