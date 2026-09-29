"""统一数据交换包。

三个领域模块仍可保留自己的内部存储，但跨模块导入、导出和备份统一使用
一个带 manifest 的 ZIP 包。该模块只负责协议和文件安全，不负责解释各领域
数据，从而避免在迁移阶段破坏现有 plan-helper / time-helper / to-dos 数据。
"""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


FORMAT_NAME = "effilife.bundle"
FORMAT_VERSION = "1.0.0"
MANIFEST_NAME = "manifest.json"
DATA_PREFIX = "data/"
CANONICAL_WORKSPACE_DATASETS = (
    "app",
    "records",
    "todos",
    "todo_categories",
    "plan_helper",
)


def _validate_workspace_dataset_shapes(datasets: Mapping[str, Any]) -> None:
    """Validate the cross-runtime container shapes before migration writes."""
    if not isinstance(datasets.get("app"), Mapping):
        raise ValueError("Workspace dataset has invalid shape: app")

    records = datasets.get("records")
    if not isinstance(records, Mapping):
        raise ValueError("Workspace dataset has invalid shape: records")
    for date, bucket in records.items():
        if not isinstance(bucket, list):
            raise ValueError(f"Workspace records bucket is invalid: {date}")

    for name in ("todos", "todo_categories"):
        if not isinstance(datasets.get(name), list):
            raise ValueError(f"Workspace dataset has invalid shape: {name}")

    plan_helper = datasets.get("plan_helper")
    if not isinstance(plan_helper, Mapping):
        raise ValueError("Workspace dataset has invalid shape: plan_helper")
    if "plans" in plan_helper and not isinstance(plan_helper["plans"], list):
        raise ValueError("Workspace plan_helper plans must be an array")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_dataset_name(name: str) -> str:
    candidate = str(name).strip()
    if not candidate or candidate in {".", ".."}:
        raise ValueError("Dataset name is required")
    if any(part in {"", ".", ".."} for part in candidate.replace("\\", "/").split("/")):
        raise ValueError(f"Invalid dataset name: {name}")
    if not all(char.isalnum() or char in "-_" for char in candidate):
        raise ValueError(f"Invalid dataset name: {name}")
    return candidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def export_bundle(
    output_path: str | os.PathLike[str],
    datasets: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Export named JSON datasets into a portable EffiLife bundle.

    The write is performed through a temporary file in the target directory so
    an interrupted export does not leave a half-written bundle at the target.
    """
    if not isinstance(datasets, Mapping) or not datasets:
        raise ValueError("At least one dataset is required")

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = {_safe_dataset_name(name): value for name, value in datasets.items()}
    dataset_bytes = {name: _json_bytes(value) for name, value in normalized.items()}
    manifest = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "created_at": _utc_now(),
        "datasets": sorted(normalized),
        "dataset_sha256": {name: _sha256(dataset_bytes[name]) for name in sorted(normalized)},
        "metadata": dict(metadata or {}),
    }

    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr(MANIFEST_NAME, _json_bytes(manifest))
            for name in sorted(normalized):
                bundle.writestr(f"{DATA_PREFIX}{name}.json", dataset_bytes[name])
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)
    return target


def inspect_bundle(bundle_path: str | os.PathLike[str]) -> dict:
    """Validate and return the manifest without importing data."""
    path = Path(bundle_path)
    with zipfile.ZipFile(path, "r") as bundle:
        if MANIFEST_NAME not in bundle.namelist():
            raise ValueError("Bundle manifest is missing")
        try:
            manifest = json.loads(bundle.read(MANIFEST_NAME).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Bundle manifest is invalid") from exc
        if manifest.get("format") != FORMAT_NAME:
            raise ValueError("Unsupported bundle format")
        if manifest.get("format_version") != FORMAT_VERSION:
            raise ValueError(f"Unsupported bundle version: {manifest.get('format_version')}")
        if not isinstance(manifest.get("datasets"), list):
            raise ValueError("Bundle datasets declaration is invalid")
        normalized_names: list[str] = []
        checksums = manifest.get("dataset_sha256")
        if checksums is not None and not isinstance(checksums, dict):
            raise ValueError("Bundle dataset checksums declaration is invalid")
        for name in manifest["datasets"]:
            safe_name = _safe_dataset_name(name)
            if safe_name in normalized_names:
                raise ValueError("Bundle datasets declaration contains duplicates")
            normalized_names.append(safe_name)
            if f"{DATA_PREFIX}{safe_name}.json" not in bundle.namelist():
                raise ValueError(f"Dataset file is missing: {safe_name}")
            if checksums is not None:
                checksum = checksums.get(safe_name)
                if not isinstance(checksum, str) or len(checksum) != 64 or any(char not in "0123456789abcdef" for char in checksum):
                    raise ValueError(f"Bundle dataset checksum is invalid: {safe_name}")
        return manifest


def read_bundle(bundle_path: str | os.PathLike[str]) -> tuple[dict, dict[str, Any]]:
    """Read and validate all datasets from a bundle."""
    manifest = inspect_bundle(bundle_path)
    datasets: dict[str, Any] = {}
    with zipfile.ZipFile(bundle_path, "r") as bundle:
        for name in manifest["datasets"]:
            raw = bundle.read(f"{DATA_PREFIX}{name}.json")
            expected = manifest.get("dataset_sha256", {}).get(name)
            if expected and _sha256(raw) != expected:
                raise ValueError(f"Dataset checksum mismatch: {name}")
            try:
                datasets[name] = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"Dataset is invalid: {name}") from exc
    return manifest, datasets


def import_bundle(
    bundle_path: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    overwrite: bool = False,
) -> dict[str, Path]:
    """Materialize bundle datasets as JSON files in a controlled directory."""
    _manifest, datasets = read_bundle(bundle_path)
    target_dir = Path(destination)
    target_dir.mkdir(parents=True, exist_ok=True)
    targets = {name: target_dir / f"{name}.json" for name in datasets}
    if not overwrite:
        for target in targets.values():
            if target.exists():
                raise FileExistsError(f"Dataset already exists: {target}")

    staging_dir = Path(tempfile.mkdtemp(prefix=".effilife-import-", dir=target_dir))
    backup_dir: Path | None = None
    backups: dict[str, Path] = {}
    installed: list[str] = []
    try:
        for name, value in datasets.items():
            (staging_dir / f"{name}.json").write_bytes(_json_bytes(value))

        if overwrite:
            existing = [name for name, target in targets.items() if target.exists()]
            if existing:
                backup_dir = Path(tempfile.mkdtemp(prefix=".effilife-import-backup-", dir=target_dir))
                for name in existing:
                    backup_path = backup_dir / f"{name}.json"
                    os.replace(targets[name], backup_path)
                    backups[name] = backup_path

        written: dict[str, Path] = {}
        for name, target in targets.items():
            os.replace(staging_dir / f"{name}.json", target)
            installed.append(name)
            written[name] = target
        return written
    except Exception:
        # Restore the destination to its exact pre-import state.  A target
        # without an old backup was newly installed by this attempt.
        for name in installed:
            targets[name].unlink(missing_ok=True)
        for name, backup_path in backups.items():
            if backup_path.exists():
                os.replace(backup_path, targets[name])
        raise
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)


def export_workspace_bundle(
    output_path: str | os.PathLike[str],
    *,
    app: Any,
    records: Any,
    todos: Any,
    todo_categories: Any,
    plan_helper: Any,
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Export the canonical datasets used by the unified workspace.

    This adapter keeps Python-side migration and backup tools aligned with the
    browser/Tauri `.efl` archive without exposing module-specific storage
    layouts to callers.
    """
    return export_bundle(
        output_path,
        {
            "app": app,
            "records": records,
            "todos": todos,
            "todo_categories": todo_categories,
            "plan_helper": plan_helper,
        },
        metadata=metadata,
    )


def read_workspace_bundle(bundle_path: str | os.PathLike[str]) -> tuple[dict, dict[str, Any]]:
    """Read a unified workspace bundle and require all canonical datasets."""
    manifest, datasets = read_bundle(bundle_path)
    missing = [name for name in CANONICAL_WORKSPACE_DATASETS if name not in datasets]
    if missing:
        raise ValueError(f"Workspace bundle is missing datasets: {', '.join(missing)}")
    _validate_workspace_dataset_shapes(datasets)
    return manifest, datasets


def verify_workspace_bundle(bundle_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return a read-only health report for a canonical workspace bundle."""
    manifest, datasets = read_workspace_bundle(bundle_path)
    return {
        "format": manifest["format"],
        "format_version": manifest["format_version"],
        "integrity": "verified" if manifest.get("dataset_sha256") else "legacy",
        "datasets": sorted(datasets),
        "top_level_counts": {
            name: len(value) if isinstance(value, (dict, list)) else None
            for name, value in datasets.items()
        },
    }
