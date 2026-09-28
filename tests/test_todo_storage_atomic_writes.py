import importlib.util
from pathlib import Path
import sys
import types


def create_storage(data_dir: Path):
    package_root = Path("to-dos")
    package_name = "to_dos_storage_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_root.resolve())]
    sys.modules[package_name] = package
    src_name = f"{package_name}.src"
    src_package = types.ModuleType(src_name)
    src_package.__path__ = [str((package_root / "src").resolve())]
    sys.modules[src_name] = src_package
    spec = importlib.util.spec_from_file_location(f"{src_name}.storage", package_root / "src" / "storage.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load to-dos storage module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.TodoStorage(str(data_dir))


SOURCE = Path("to-dos/src/storage.py").read_text(encoding="utf-8")


def test_todo_storage_uses_atomic_writer_for_active_and_archive_json():
    assert "def _atomic_write_json(path: Path, payload)" in SOURCE
    assert "os.replace(temporary_path, path)" in SOURCE
    assert "_atomic_write_json(self.todos_file" in SOURCE
    assert "_atomic_write_json(self.categories_file" in SOURCE
    assert "_atomic_write_json(archive_file" in SOURCE


def test_todo_storage_round_trip_and_archive_remain_compatible(tmp_path):
    storage = create_storage(tmp_path / "todos")
    todo = storage.create_todo("原子写入测试")
    assert storage.delete_todo(todo.id)

    restored = create_storage(tmp_path / "todos")
    archived = list((tmp_path / "todos" / "archive").rglob("todos.json"))
    assert restored.get_todo_by_id(todo.id).status.value == "archived"
    assert len(archived) == 1
