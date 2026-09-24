import sys

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
    assert modules["1"]["cmd"][-3:] == ["--host", "127.0.0.1", "--strictPort"]
    assert modules["1"]["companions"][0]["name"] == "plan-helper API"


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
