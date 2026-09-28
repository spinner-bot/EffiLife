import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def _frontend_constant(source: str, name: str) -> str:
    match = re.search(rf"const {name} = '([^']+)'", source)
    assert match is not None, f"missing frontend archive constant: {name}"
    return match.group(1)


def test_python_and_frontend_archive_protocol_constants_match():
    from common.data_exchange import CANONICAL_WORKSPACE_DATASETS, FORMAT_NAME, FORMAT_VERSION

    source = FRONTEND_ARCHIVE.read_text(encoding="utf-8")
    assert _frontend_constant(source, "ARCHIVE_FORMAT") == FORMAT_NAME
    assert _frontend_constant(source, "ARCHIVE_FORMAT_VERSION") == FORMAT_VERSION

    match = re.search(r"const CANONICAL_ARCHIVE_DATASETS = \[([^\]]+)\] as const", source)
    assert match is not None
    frontend_datasets = tuple(re.findall(r"'([^']+)'", match.group(1)))
    assert frontend_datasets == CANONICAL_WORKSPACE_DATASETS


def test_frontend_export_uses_the_declared_canonical_dataset_list():
    source = FRONTEND_ARCHIVE.read_text(encoding="utf-8")
    assert "const datasets = ['app', 'records', 'todos', 'todo_categories', 'plan_helper']" in source
    assert "data/${name}.json" in source
