"""to-dos legacy JSON 到统一待办数据集的无副作用迁移器。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ..api_gateway.adapters import TodoAdapter


class TodoMigrationError(ValueError):
    """严格迁移模式下包含条目错误的异常。"""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("待办迁移失败: " + "; ".join(errors))


def _parse_source(source: str | Mapping[str, Any] | list[Any]) -> tuple[Any, str | None, list[Any]]:
    if isinstance(source, str):
        try:
            source = json.loads(source)
        except json.JSONDecodeError as exc:
            raise ValueError("待办迁移输入不是有效 JSON") from exc

    if isinstance(source, list):
        return source, None, []
    if not isinstance(source, Mapping):
        raise ValueError("待办迁移输入必须是 JSON 对象或数组")

    todos = source.get("todos")
    version = str(source.get("version")) if source.get("version") is not None else None
    categories = source.get("categories", [])
    if not isinstance(todos, list):
        raise ValueError("待办迁移输入缺少 todos 数组")
    if not isinstance(categories, list):
        categories = []
    return todos, version, categories


def migrate_legacy_todos(
    source: str | Mapping[str, Any] | list[Any],
    *,
    strict: bool = True,
) -> dict[str, Any]:
    """将旧版 to-dos 导出转换为 canonical payload，不写入任何存储。

    宽松模式跳过非法条目并返回 warnings；严格模式遇到任何非法条目抛出
    :class:`TodoMigrationError`，确保上层不会误导入半套数据。
    """
    raw_todos, source_version, categories = _parse_source(source)
    migrated: list[dict[str, Any]] = []
    errors: list[str] = []

    for index, raw in enumerate(raw_todos):
        if not isinstance(raw, Mapping):
            errors.append(f"第 {index} 项不是对象")
            continue
        if not str(raw.get("id", "")).strip():
            errors.append(f"第 {index} 项缺少 id")
            continue
        if not str(raw.get("title", "")).strip():
            errors.append(f"第 {index} 项缺少 title")
            continue
        try:
            migrated.append(TodoAdapter.to_unified_todo(dict(raw)).to_dict())
        except (TypeError, ValueError, KeyError) as exc:
            errors.append(f"第 {index} 项无效: {exc}")

    if errors and strict:
        raise TodoMigrationError(errors)

    return {
        "todos": migrated,
        "categories": categories,
        "source_version": source_version,
        "warnings": errors,
    }
