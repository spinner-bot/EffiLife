import sys
from pathlib import Path

import launcher.start as launcher


def test_unified_launcher_mode_dispatches_to_main_workspace(monkeypatch):
    modules = {"1": {"name": "EffiLife 统一工作台"}}
    calls = []

    monkeypatch.setattr(launcher, "build_modules", lambda: modules)
    monkeypatch.setattr(launcher, "run_module", lambda choice, available: calls.append((choice, available)))
    monkeypatch.setattr(sys, "argv", ["start.py", "--unified"])

    launcher.main()

    assert calls == [("1", modules)]


def test_launcher_keeps_unified_workspace_as_first_menu_entry():
    modules = launcher.build_modules()

    assert modules["1"]["name"] == "EffiLife 统一工作台"
    assert modules["1"]["url"] == "http://127.0.0.1:1420"
    assert modules["1"]["cmd"][-5:] == ["--host", "127.0.0.1", "--port", "1420", "--strictPort"]
    assert modules["1"]["companions"][0]["name"] == "plan-helper API"


def test_launcher_assigns_the_legacy_todos_server_its_declared_port():
    modules = launcher.build_modules()

    assert modules["4"]["url"] == "http://127.0.0.1:1421"
    assert modules["4"]["cmd"][-5:] == ["--host", "127.0.0.1", "--port", "1421", "--strictPort"]


def test_posix_launcher_uses_the_same_unified_entrypoint():
    script = (Path(launcher.BASE_DIR) / "launcher" / "start.sh").read_text(encoding="utf-8")

    assert "python3 launcher/start.py --unified" in script


def test_launcher_cleans_up_when_companion_cannot_start(monkeypatch):
    terminated = []

    class FailingPopen:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError("python missing")

    monkeypatch.setattr(launcher.subprocess, "Popen", FailingPopen)
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))

    result = launcher.start_companions({
        "companions": [{
            "name": "test companion",
            "cmd": ["missing"],
            "cwd": launcher.BASE_DIR,
            "url": None,
        }],
    }, {})

    assert result is None
    assert terminated == []


def test_launcher_stops_unhealthy_main_service_instead_of_waiting_forever(monkeypatch):
    terminated = []
    waited = []

    class RunningProcess:
        stdout = None
        returncode = None

        def poll(self):
            return None

        def wait(self):
            waited.append(True)

    process = RunningProcess()
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(launcher, "stream_output", lambda _process: None)
    monkeypatch.setattr(launcher, "wait_for_service", lambda _process, _url: False)
    monkeypatch.setattr(launcher, "terminate_process", lambda item: terminated.append(item))
    monkeypatch.setattr(launcher.webbrowser, "open", lambda _url: True)

    launcher.run_module("test", {
        "test": {
            "name": "test",
            "available": True,
            "cmd": ["test"],
            "cwd": launcher.BASE_DIR,
            "url": "http://127.0.0.1:1",
            "setup": None,
        },
    })

    assert terminated == [process]
    assert waited == []


def test_launcher_reuses_existing_main_service_without_starting_duplicate(monkeypatch):
    terminated = []
    opened = []

    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [])
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: True)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))

    class UnexpectedPopen:
        def __init__(self, *args, **kwargs):
            raise AssertionError("the launcher must not start a duplicate frontend")

    monkeypatch.setattr(launcher.subprocess, "Popen", UnexpectedPopen)

    launcher.run_module("test", {
        "test": {
            "name": "test",
            "available": True,
            "cmd": ["test"],
            "cwd": launcher.BASE_DIR,
            "url": "http://127.0.0.1:1420",
            "setup": None,
        },
    })

    assert opened == ["http://127.0.0.1:1420"]
    assert terminated == []
