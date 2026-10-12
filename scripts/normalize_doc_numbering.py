"""Normalize the three document namespaces without changing their content dates.

The document-management rule reserves stage 0 and uses a four-digit sequence.
This one-off migration keeps each directory independent, preserves 0000 rule
files, and compacts the remaining entries in their existing numeric order.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE_DIRS = (
    ROOT / "docs" / "设计方案",
    ROOT / "docs" / "进展报告",
    ROOT / "docs" / "progress",
)
NUMBERED = re.compile(r"^(?P<number>\d{4})-(?P<rest>.+)$")
TEXT_SUFFIXES = {".md", ".txt", ".rst", ".yml", ".yaml", ".json", ".toml", ".ts", ".vue", ".py", ".ps1"}


def entries(directory: Path) -> list[tuple[int, Path]]:
    result = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        match = NUMBERED.match(path.name)
        if match:
            result.append((int(match.group("number")), path))
    return sorted(result, key=lambda item: (item[0], item[1].name))


def build_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for directory in NAMESPACE_DIRS:
        numbered = [(number, path) for number, path in entries(directory) if number != 0]
        for sequence, (_old_number, path) in enumerate(numbered, start=1):
            new_name = f"{sequence:04d}-{path.name.split('-', 1)[1]}"
            if path.name != new_name:
                mapping[str(path.relative_to(ROOT))] = str((directory / new_name).relative_to(ROOT))
    return mapping


def update_text_references(mapping: dict[str, str]) -> int:
    changed = 0
    replacements = sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts or "target" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = original
        for old, new in replacements:
            updated = updated.replace(old.replace("\\", "/"), new.replace("\\", "/"))
            updated = updated.replace(old.replace("/", "\\"), new.replace("/", "\\"))
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="")
            changed += 1
    return changed


def update_design_headings(mapping: dict[str, str]) -> int:
    changed = 0
    for old, new in mapping.items():
        if not old.startswith("docs\\设计方案\\"):
            continue
        old_path = ROOT / old
        new_path = ROOT / new
        match = NUMBERED.match(Path(old).name)
        new_match = NUMBERED.match(Path(new).name)
        if not match or not new_match:
            continue
        content = new_path.read_text(encoding="utf-8")
        updated = re.sub(
            rf"(?m)^(#\s*){int(match.group('number')):04d}(?=\s|｜|\|)",
            rf"\g<1>{int(new_match.group('number')):04d}",
            content,
            count=1,
        )
        if updated != content:
            new_path.write_text(updated, encoding="utf-8", newline="")
            changed += 1
    return changed


def sync_numbered_headings() -> int:
    changed = 0
    for directory in NAMESPACE_DIRS:
        for _number, path in entries(directory):
            match = NUMBERED.match(path.name)
            if not match or int(match.group("number")) == 0:
                continue
            expected = int(match.group("number"))
            content = path.read_text(encoding="utf-8")
            updated = re.sub(
                rf"(?m)^(#\s*)\d{{4}}(?=\s|｜|\|)",
                rf"\g<1>{expected:04d}",
                content,
                count=1,
            )
            if updated != content:
                path.write_text(updated, encoding="utf-8", newline="")
                changed += 1
    return changed


def apply_mapping(mapping: dict[str, str]) -> None:
    staged: dict[Path, Path] = {}
    for old, new in mapping.items():
        old_path = ROOT / old
        temporary = old_path.with_name(f".__renumber__{old_path.name}")
        if temporary.exists():
            raise RuntimeError(f"temporary rename target already exists: {temporary}")
        old_path.rename(temporary)
        staged[temporary] = ROOT / new
    for temporary, new_path in staged.items():
        if new_path.exists():
            raise RuntimeError(f"final rename target already exists: {new_path}")
        temporary.rename(new_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping-out", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mapping = build_mapping()
    args.mapping_out.parent.mkdir(parents=True, exist_ok=True)
    args.mapping_out.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.apply:
        print(json.dumps({"renames": len(mapping), "mapping": str(args.mapping_out)}, ensure_ascii=False))
        return 0
    apply_mapping(mapping)
    changed = update_text_references(mapping)
    headings = update_design_headings(mapping)
    headings += sync_numbered_headings()
    print(json.dumps({"renames": len(mapping), "reference_files_changed": changed, "numbered_headings_changed": headings}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
