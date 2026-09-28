import sys
from pathlib import Path

import launcher.start as launcher


def test_unified_launcher_mode_dispatches_to_main_workspace(monkeypatch):
    modules = {"1": {"name": "EffiLife unified workspace"}}
    calls = []
    monkeypatch.setattr(launcher, "build_modules", lambda: modules)
    monkeypatch.setattr(launcher, "run_module", lambda choice, available, **kwargs: calls.append((choice, available, kwargs)))
    monkeypatch.setattr(sys, "argv", ["start.py", "--unified"])
    launcher.main()
    assert calls == [("1", modules, {"open_browser": True})]


def test_release_check_is_read_only_and_short_circuits_startup(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "build_modules", lambda: (_ for _ in ()).throw(AssertionError("must not start modules")))
    monkeypatch.setattr(launcher, "release_check_command", lambda: True)
    monkeypatch.setattr(sys, "argv", ["start.py", "--release-check"])

    launcher.main()

    assert capsys.readouterr().out == ""


def test_launcher_defaults_to_unified_workspace_without_legacy_flag(monkeypatch):
    modules = {"1": {"name": "EffiLife unified workspace"}}
    calls = []
    monkeypatch.setattr(launcher, "build_modules", lambda: modules)
    monkeypatch.setattr(launcher, "run_module", lambda choice, available, **kwargs: calls.append((choice, available, kwargs)))
    monkeypatch.setattr(sys, "argv", ["start.py", "--no-browser"])

    launcher.main()

    assert calls == [("1", modules, {"open_browser": False})]


def test_launcher_keeps_legacy_menu_explicit(monkeypatch):
    import builtins

    modules = {"1": {"name": "workspace"}}
    shown = []
    monkeypatch.setattr(launcher, "build_modules", lambda: modules)
    monkeypatch.setattr(launcher, "show_menu", lambda available: shown.append(available))
    monkeypatch.setattr(builtins, "input", lambda _prompt: (_ for _ in ()).throw(EOFError()))
    monkeypatch.setattr(sys, "argv", ["start.py", "--legacy-menu"])

    launcher.main()

    assert shown == [modules]


def test_launcher_can_serve_prebuilt_workspace_without_node(monkeypatch, tmp_path):
    dist = tmp_path / "time-helper" / "desk" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher, "find_npm", lambda: None)
    monkeypatch.setattr(launcher, "find_node", lambda: None)
    command, url, setup = launcher.get_time_helper_cmd()
    assert command[:2] == [sys.executable, str(tmp_path / "launcher" / "static_server.py")]
    assert "--port" in command and "1420" in command


def test_launcher_packaged_mode_prefers_native_tauri_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"placeholder")
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])
    command, url, setup = launcher.get_time_helper_cmd()
    assert command == [str(binary)]
    assert url is None and setup is None


def test_launcher_packaged_mode_never_falls_back_to_npm(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])
    command, url, setup = launcher.get_time_helper_cmd()
    assert command is None
    assert url is None and setup is None
    assert "--directory" in command
    assert url == "http://127.0.0.1:1420"
    assert setup is None


def test_launcher_keeps_unified_workspace_as_first_menu_entry():
    modules = launcher.build_modules()
    assert modules["1"]["name"] == "EffiLife unified workspace"
    assert modules["1"]["url"] == "http://127.0.0.1:1420"
    assert modules["1"]["cmd"][-5:] == ["--host", "127.0.0.1", "--port", "1420", "--strictPort"]
    assert modules["1"]["companions"][0]["name"] == "plan-helper API"
    assert modules["1"]["companions"][0]["health_url"].endswith("/api/health")


def test_launcher_user_facing_brand_name_is_effilife():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert "EffLife" not in source


def test_launcher_assigns_the_legacy_todos_server_its_declared_port():
    modules = launcher.build_modules()
    assert modules["4"]["url"] == "http://127.0.0.1:1421"
    assert modules["4"]["cmd"][-5:] == ["--host", "127.0.0.1", "--port", "1421", "--strictPort"]


def test_launcher_forwards_configured_unified_data_dir_to_plan_helper(monkeypatch, tmp_path):
    monkeypatch.setenv("EFFILIFE_DATA_DIR", str(tmp_path / "effilife-data"))
    command = launcher.plan_helper_command()
    assert command[:2] == [sys.executable, "web/server.py"]
    assert command[-2:] == ["--data-dir", str(tmp_path / "effilife-data")]
    modules = launcher.build_modules()
    assert modules["1"]["companions"][0]["cmd"] == command
    assert modules["2"]["cmd"] == command


def test_launcher_keeps_legacy_data_location_when_no_data_dir_is_configured(monkeypatch):
    monkeypatch.delenv("EFFILIFE_DATA_DIR", raising=False)
    assert launcher.plan_helper_command() == [sys.executable, "web/server.py"]


def test_health_probe_requires_plan_helper_identity(monkeypatch):
    class Response:
        status = 200

        def __init__(self, body):
            self.body = body

        def read(self, _limit):
            return self.body.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    responses = iter([
        Response('{"success":true,"data":{"service":"other","status":"ok"}}'),
        Response('{"success":true,"data":{"service":"plan-helper","status":"ok"}}'),
    ])
    monkeypatch.setattr(launcher, "urlopen", lambda _url, timeout: next(responses))
    health_url = "http://127.0.0.1:8765/api/health"
    assert launcher.service_is_ready(health_url) is False
    assert launcher.service_is_ready(health_url) is True


def test_local_port_probe_reports_occupied_and_free_endpoints(monkeypatch):
    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(launcher.socket, "create_connection", lambda *_args, **_kwargs: FakeSocket())
    assert launcher.local_port_is_occupied("http://127.0.0.1:1420") is True
    monkeypatch.setattr(launcher.socket, "create_connection", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError()))
    assert launcher.local_port_is_occupied("http://127.0.0.1:1420") is False
    assert launcher.local_port_is_occupied("https://example.com:443") is False


def test_launcher_reports_port_conflict_without_starting_main(monkeypatch):
    terminated = []
    opened = []
    companion = object()
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [companion])
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda _url: True)
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))

    class UnexpectedPopen:
        def __init__(self, *args, **kwargs):
            raise AssertionError("the launcher must not start on an occupied port")

    monkeypatch.setattr(launcher.subprocess, "Popen", UnexpectedPopen)
    launcher.run_module("test", {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": "http://127.0.0.1:1420", "setup": None}})
    assert terminated == [companion]
    assert opened == []


def test_startup_timeout_is_bounded_and_configurable(monkeypatch):
    monkeypatch.setenv("EFFILIFE_STARTUP_TIMEOUT", "90")
    assert launcher.startup_timeout() == 90
    monkeypatch.setenv("EFFILIFE_STARTUP_TIMEOUT", "1")
    assert launcher.startup_timeout() == 5
    monkeypatch.setenv("EFFILIFE_STARTUP_TIMEOUT", "not-a-number")
    assert launcher.startup_timeout() == 30


def test_setup_timeout_is_bounded_and_configurable(monkeypatch):
    monkeypatch.setenv("EFFILIFE_SETUP_TIMEOUT", "120")
    assert launcher.setup_timeout() == 120
    monkeypatch.setenv("EFFILIFE_SETUP_TIMEOUT", "1")
    assert launcher.setup_timeout() == 30
    monkeypatch.setenv("EFFILIFE_SETUP_TIMEOUT", "9999")
    assert launcher.setup_timeout() == 900
    monkeypatch.setenv("EFFILIFE_SETUP_TIMEOUT", "not-a-number")
    assert launcher.setup_timeout() == 300


def test_launcher_returns_when_dependency_setup_times_out(monkeypatch):
    class TimeoutRun:
        def __call__(self, *args, **kwargs):
            assert kwargs["timeout"] == 300
            raise launcher.subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(launcher.subprocess, "run", TimeoutRun())
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [])
    module = {
        "name": "test",
        "available": True,
        "cmd": ["frontend"],
        "cwd": launcher.BASE_DIR,
        "url": None,
        "setup": ["npm", "install"],
        "needs_setup": True,
    }
    launcher.run_module("test", {"test": module})


def test_launcher_groups_owned_processes_for_shutdown():
    options = launcher.process_group_options()
    if launcher.os.name == "nt":
        assert "creationflags" in options
    else:
        assert options == {"start_new_session": True}


def test_posix_shutdown_targets_the_owned_process_group(monkeypatch):
    if launcher.os.name == "nt":
        return
    signals = []

    class RunningProcess:
        pid = 4242
        def poll(self):
            return None
        def wait(self, timeout=None):
            return None
        def terminate(self):
            raise AssertionError("process fallback should not be needed")

    monkeypatch.setattr(launcher.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    launcher.terminate_process(RunningProcess())
    assert signals == [(4242, launcher.signal.SIGTERM)]


def test_posix_launcher_uses_the_same_unified_entrypoint():
    script = (Path(launcher.BASE_DIR) / "launcher" / "start.sh").read_text(encoding="utf-8")
    assert "python3 launcher/start.py --unified" in script
    assert 'python3 launcher/start.py --unified "$@"' in script


def test_windows_launcher_forwards_extra_arguments():
    script = (Path(launcher.BASE_DIR) / "launcher" / "start.bat").read_text(encoding="utf-8")
    assert "launcher\\start.py --unified %*" in script


def test_launcher_cleans_up_when_companion_cannot_start(monkeypatch):
    terminated = []

    class FailingPopen:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError("python missing")

    monkeypatch.setattr(launcher.subprocess, "Popen", FailingPopen)
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))
    result = launcher.start_companions({"companions": [{"name": "test companion", "cmd": ["missing"], "cwd": launcher.BASE_DIR, "url": None}]}, {})
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
    launcher.run_module("test", {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": "http://127.0.0.1:1", "setup": None}})
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
    launcher.run_module("test", {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": "http://127.0.0.1:1420", "setup": None}})
    assert opened == ["http://127.0.0.1:1420"]
    assert terminated == []


def test_launcher_exits_when_reused_frontend_stops(monkeypatch):
    checks = iter([True, False])
    opened = []

    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [])
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: next(checks))
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))

    class UnexpectedPopen:
        def __init__(self, *args, **kwargs):
            raise AssertionError("the launcher must not start a duplicate frontend")

    monkeypatch.setattr(launcher.subprocess, "Popen", UnexpectedPopen)
    launcher.run_module("test", {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": "http://127.0.0.1:1420", "setup": None}})
    assert opened == ["http://127.0.0.1:1420"]


def test_launcher_diagnostics_are_read_only_and_report_module_state(monkeypatch):
    modules = {
        "1": {
            "name": "workspace",
            "available": True,
            "url": "http://127.0.0.1:1420",
            "needs_setup": False,
        },
        "2": {
            "name": "legacy",
            "available": False,
            "unavailable_reason": "missing runtime",
            "url": None,
            "needs_setup": False,
        },
    }
    monkeypatch.setattr(launcher, "find_node", lambda: "node.exe")
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda _url: True)
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: True)
    result = launcher.collect_diagnostics(modules)
    assert result["node"] == "node.exe"
    assert result["npm"] == "npm.cmd"
    assert result["version"] == (Path(launcher.BASE_DIR) / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    assert result["modules"]["1"]["port_occupied"] is True
    assert result["modules"]["1"]["service_ready"] is True
    assert result["modules"]["2"]["service_ready"] is False
    assert result["modules"]["2"]["unavailable_reason"] == "missing runtime"


def test_diagnose_output_uses_ascii_safe_json():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert "json.dumps(collect_diagnostics(modules), ensure_ascii=True" in source


def test_launcher_exposes_a_scriptable_version_command():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert 'if "--version" in sys.argv:' in source
    assert "print(app_version() or \"unknown\")" in source


def test_launcher_records_best_effort_jsonl_diagnostics(monkeypatch, tmp_path):
    monkeypatch.setenv("EFFILIFE_LOG_DIR", str(tmp_path))

    assert launcher.record_launcher_event("test_event", module="workspace", port=1420) is True

    log_path = tmp_path / "launcher.log"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = __import__("json").loads(lines[0])
    assert event["event"] == "test_event"
    assert event["module"] == "workspace"
    assert event["port"] == 1420
    assert event["version"]


def test_launcher_diagnostics_do_not_fail_when_log_directory_is_read_only(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "launcher_log_path", lambda: tmp_path / "missing" / "launcher.log")
    monkeypatch.setattr(launcher.Path, "mkdir", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("read only")))

    assert launcher.record_launcher_event("read_only") is False


def test_launcher_version_command_short_circuits_module_detection(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["start.py", "--version"])
    monkeypatch.setattr(launcher, "build_modules", lambda: calls.append(True))
    monkeypatch.setattr(launcher, "app_version", lambda: "9.9.9")
    launcher.main()
    assert calls == []


def test_launcher_verifies_workspace_bundle_without_starting_modules(monkeypatch, tmp_path, capsys):
    from common.data_exchange import export_workspace_bundle

    bundle = tmp_path / "workspace.efl"
    export_workspace_bundle(
        bundle,
        app={},
        records={},
        todos=[],
        todo_categories=[],
        plan_helper={"plans": []},
    )
    monkeypatch.setattr(sys, "argv", ["start.py", "--verify-bundle", str(bundle)])
    monkeypatch.setattr(launcher, "build_modules", lambda: (_ for _ in ()).throw(AssertionError("must stay read-only")))

    launcher.main()

    output = capsys.readouterr().out
    assert '"ok": true' in output
    assert '"integrity": "verified"' in output


def test_launcher_verify_bundle_requires_path(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["start.py", "--verify-bundle"])
    try:
        launcher.main()
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("missing bundle path should fail")


def test_unified_launcher_supports_no_browser_mode():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert "def run_module(choice, modules, open_browser=True)" in source
    assert 'open_browser="--no-browser" not in sys.argv' in source
    assert "if open_browser:" in source
