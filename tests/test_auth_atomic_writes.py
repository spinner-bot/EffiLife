from pathlib import Path

from common.auth import AuthManager


SOURCE = Path("common/auth/manager.py").read_text(encoding="utf-8")


def test_auth_json_outputs_use_atomic_writer():
    assert "def _atomic_write_json(path: Path, payload)" in SOURCE
    assert "os.replace(temporary_path, path)" in SOURCE
    assert "_atomic_write_json(self.users_file" in SOURCE
    assert "_atomic_write_json(self.session_file" in SOURCE


def test_auth_user_and_session_round_trip(tmp_path):
    first = AuthManager(tmp_path / "user")
    result = first.register("atomic", "password")
    assert result["success"]
    assert first.login("atomic", "password")["success"]

    second = AuthManager(tmp_path / "user")
    second.load()
    assert second.is_logged_in()
    assert second.get_current_user().username == "atomic"
