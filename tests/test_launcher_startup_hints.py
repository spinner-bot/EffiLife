from pathlib import Path

import launcher.start as launcher


def test_startup_failure_hint_points_to_both_diagnostics_modes(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "launcher_log_path", lambda: tmp_path / "launcher.log")

    launcher.print_startup_failure_hint()

    output = capsys.readouterr().out
    assert "--doctor" in output
    assert "--diagnose" in output
    assert str(tmp_path / "launcher.log") in output


def test_port_conflict_prints_actionable_hint(monkeypatch, capsys):
    companion = object()
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [companion])
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda _url: True)
    terminated = []
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))

    result = launcher.run_module(
        "test",
        {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": Path.cwd(), "url": "http://127.0.0.1:1420", "setup": None}},
    )

    assert result == 1
    assert terminated == [companion]
    assert "--doctor" in capsys.readouterr().out

