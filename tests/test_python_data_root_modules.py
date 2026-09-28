import importlib.util
from pathlib import Path
import sys
import types

from common.auth import AuthManager
from common.bootstrap import EffiLifeIntegration
from common.data_manager import DataManager


def load_todo_storage():
    package_root = Path("to-dos")
    package_name = "to_dos_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(package_root.resolve())]
    sys.modules[package_name] = package
    src_name = f"{package_name}.src"
    src_package = types.ModuleType(src_name)
    src_package.__path__ = [str((package_root / "src").resolve())]
    sys.modules[src_name] = src_package
    spec = importlib.util.spec_from_file_location(
        f"{src_name}.storage",
        package_root / "src" / "storage.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load to-dos storage module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.TodoStorage()


def test_auth_manager_follows_unified_data_root(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    monkeypatch.setenv("EFFILIFE_DATA_DIR", str(root))

    manager = AuthManager()

    assert manager.data_dir == root / "user"


def test_todo_storage_follows_unified_data_root(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    monkeypatch.setenv("EFFILIFE_DATA_DIR", str(root))

    storage = load_todo_storage()

    assert storage.data_dir == root / "modules" / "to-dos"


def test_integration_explicit_root_is_forwarded_to_auth(monkeypatch, tmp_path):
    monkeypatch.delenv("EFFILIFE_DATA_DIR", raising=False)
    AuthManager.reset_instance()

    integration = EffiLifeIntegration(data_root=str(tmp_path / "explicit"))

    assert integration.auth_manager.data_dir == tmp_path / "explicit" / "user"
    AuthManager.reset_instance()


def test_integration_registers_modules_under_configured_root(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    monkeypatch.setenv("EFFILIFE_DATA_DIR", str(root))
    DataManager.reset_instance()
    AuthManager.reset_instance()

    integration = EffiLifeIntegration()
    integration.initialize()

    for module in ("time-helper", "to-dos", "plan-helper"):
        assert integration.data_manager.get_module_data_dir(module) == str(root / "modules" / module)
    DataManager.reset_instance()
    AuthManager.reset_instance()
