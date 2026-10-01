import json
import sys
from pathlib import Path

import launcher.start as launcher


def test_launcher_reads_custom_node_directory_at_lookup_time(monkeypatch, tmp_path):
    node_dir = tmp_path / "node-runtime"
    node_dir.mkdir()
    (node_dir / launcher.node_tool_filename("node")).write_bytes(b"node")
    (node_dir / launcher.node_tool_filename("npm")).write_text("@echo off", encoding="utf-8")

    # The launcher module is imported before the environment is configured in
    # embedded/packaged hosts. It must still agree with diagnostics afterward.
    monkeypatch.setenv("EFFILIFE_NODE_DIR", str(node_dir))
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)

    assert launcher.find_node() == str(node_dir / launcher.node_tool_filename("node"))
    assert launcher.find_npm() == str(node_dir / launcher.node_tool_filename("npm"))
    assert str(node_dir) in launcher.node_environment()["PATH"]


def test_dependencies_ready_requires_actual_frontend_entry_points(tmp_path):
    desk = tmp_path / "time-helper" / "desk"
    bin_dir = desk / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    vite_name = "vite.cmd" if launcher.os.name == "nt" else "vite"
    typecheck_name = "vue-tsc.cmd" if launcher.os.name == "nt" else "vue-tsc"
    (bin_dir / vite_name).write_text("vite", encoding="utf-8")

    assert launcher.dependencies_ready(desk) is False
    (bin_dir / typecheck_name).write_text("vue-tsc", encoding="utf-8")
    assert launcher.dependencies_ready(desk) is True


def test_dependencies_ready_accepts_vite_for_compatibility_ui(tmp_path):
    ui = tmp_path / "to-dos" / "ui"
    bin_dir = ui / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    vite_name = "vite.cmd" if launcher.os.name == "nt" else "vite"
    (bin_dir / vite_name).write_text("vite", encoding="utf-8")

    assert launcher.dependencies_ready(ui) is True


def test_launcher_ignores_blank_custom_node_directory(monkeypatch):
    monkeypatch.setenv("EFFILIFE_NODE_DIR", "   ")
    expected = launcher.CUSTOM_NODE_DIR if launcher.os.name == "nt" else None
    assert launcher.custom_node_dir() == expected


def test_launcher_reads_custom_node_directory_on_posix(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher.os, "name", "posix")
    assert launcher.node_tool_filename("node") == "node"
    assert launcher.node_tool_filename("npm") == "npm"


def test_unified_launcher_mode_dispatches_to_main_workspace(monkeypatch):
    modules = {"1": {"name": "EffiLife unified workspace"}}
    calls = []
    monkeypatch.setattr(launcher, "build_modules", lambda: modules)
    monkeypatch.setattr(launcher, "run_module", lambda choice, available, **kwargs: calls.append((choice, available, kwargs)))
    monkeypatch.setattr(sys, "argv", ["start.py", "--unified"])
    launcher.main()
    assert calls == [("1", modules, {"open_browser": True})]


def test_launcher_help_does_not_start_workspace(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "build_modules", lambda: (_ for _ in ()).throw(AssertionError("must not start modules")))
    monkeypatch.setattr(sys, "argv", ["start.py", "--help"])

    launcher.main()

    output = capsys.readouterr().out
    assert "EffiLife launcher" in output
    assert "--diagnose" in output


def test_release_check_is_read_only_and_short_circuits_startup(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "build_modules", lambda: (_ for _ in ()).throw(AssertionError("must not start modules")))
    monkeypatch.setattr(launcher, "release_check_command", lambda: True)
    monkeypatch.setattr(sys, "argv", ["start.py", "--release-check"])

    launcher.main()

    assert capsys.readouterr().out == ""


def test_release_check_reports_desktop_and_mobile_boundaries(capsys):
    assert launcher.release_check_command() is True

    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert "build_ready" in report
    assert report["checks"]["desktop"]["ok"] is True
    assert report["checks"]["mobile"]["ok"] is True
    assert set(report["environment"]) == {"desktop", "android", "ios"}
    assert "missing" in report["environment"]["desktop"]


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
    assert "--directory" in command
    assert url == "http://127.0.0.1:1420"
    assert setup is None


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


def test_launcher_discovers_posix_style_tauri_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher.os, "name", "posix")
    binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"placeholder")
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


def test_launcher_packaged_mode_never_uses_debug_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    debug_binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "debug" / "efflife-desk.exe"
    debug_binary.parent.mkdir(parents=True)
    debug_binary.write_bytes(b"debug-placeholder")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    command, url, setup = launcher.get_time_helper_cmd()

    assert command is None
    assert url is None and setup is None


def test_compatibility_todos_web_packaged_mode_never_falls_back_to_npm(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    command, url, setup = launcher.get_todos_web_cmd()

    assert command is None
    assert url is None and setup is None


def test_compatibility_todos_web_packaged_mode_uses_valid_static_build(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    dist = tmp_path / "to-dos" / "ui" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    command, url, setup = launcher.get_todos_web_cmd()

    assert command[:2] == [sys.executable, str(tmp_path / "launcher" / "static_server.py")]
    assert url == "http://127.0.0.1:1421"
    assert setup is None


def test_launcher_ignores_empty_packaged_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"")
    dist = tmp_path / "time-helper" / "desk" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_bytes(b"")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    command, url, setup = launcher.get_time_helper_cmd()

    assert command is None
    assert url is None and setup is None


def test_launcher_diagnostics_distinguish_existing_and_usable_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"")

    result = launcher.collect_diagnostics({})
    candidate = next(item for item in result["time_helper_binaries"] if item["path"] == str(binary))

    assert candidate["exists"] is True
    assert candidate["usable"] is False


def test_launcher_reports_actionable_reason_when_packaged_artifact_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    modules = launcher.build_modules()

    assert modules["1"]["available"] is False
    assert modules["1"]["unavailable_reason"] == "Packaged mode requires a Tauri binary or built dist/index.html"


def test_launcher_packaged_mode_can_also_be_selected_by_environment(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["start.py"])
    monkeypatch.setenv("EFFILIFE_LAUNCH_MODE", "packaged")

    assert launcher.packaged_mode() is True


def test_launcher_does_not_start_external_plan_helper_for_native_tauri(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    binary = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "efflife-desk.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"native-binary")
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged"])

    modules = launcher.build_modules()

    assert modules["1"]["cmd"] == [str(binary)]
    assert modules["1"]["url"] is None
    assert modules["1"]["companions"] == []


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


def test_frontend_probe_requires_effilife_identity(monkeypatch):
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
        Response("<html><title>Other service</title></html>"),
        Response('<meta name="application-name" content="EffiLife">'),
    ])
    monkeypatch.setattr(launcher, "urlopen", lambda _url, timeout: next(responses))
    frontend_url = "http://127.0.0.1:1420"
    assert launcher.service_is_ready(frontend_url) is False
    assert launcher.service_is_ready(frontend_url) is True


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
    result = launcher.run_module("test", {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": "http://127.0.0.1:1420", "setup": None}})
    assert result == 1
    assert terminated == [companion]
    assert opened == []


def test_launcher_reports_companion_port_conflict_before_starting_it(monkeypatch):
    terminated = []
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda _url: True)
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))

    class UnexpectedPopen:
        def __init__(self, *args, **kwargs):
            raise AssertionError("the launcher must not start on a companion port conflict")

    monkeypatch.setattr(launcher.subprocess, "Popen", UnexpectedPopen)
    result = launcher.start_companions({
        "companions": [{
            "name": "plan-helper API",
            "cmd": ["python", "web/server.py"],
            "cwd": launcher.BASE_DIR,
            "url": "http://127.0.0.1:8765",
            "health_url": "http://127.0.0.1:8765/api/health",
        }],
    }, {})

    assert result is None
    assert terminated == []


def test_launcher_reuses_external_healthy_workspace_without_waiting_forever(monkeypatch):
    opened = []
    started = []
    def fake_start_companions(_module, _env):
        started.append(True)
        return []

    monkeypatch.setattr(launcher, "start_companions", fake_start_companions)
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: True)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))

    launcher.run_module(
        "test",
        {"test": {
            "name": "test",
            "available": True,
            "cmd": ["test"],
            "cwd": launcher.BASE_DIR,
            "url": "http://127.0.0.1:1420",
            "setup": None,
        }},
    )

    assert opened == ["http://127.0.0.1:1420"]
    assert started == [True]


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


def test_launcher_marks_dependency_setup_complete_for_reused_module(monkeypatch):
    setup_calls = []

    class CompletedRun:
        returncode = 0

    class FinishedProcess:
        stdout = None
        returncode = 0

        def poll(self):
            return 0

        def wait(self):
            return 0

    monkeypatch.setattr(launcher.subprocess, "run", lambda command, **_kwargs: setup_calls.append(command) or CompletedRun())
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *_args, **_kwargs: FinishedProcess())
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [])
    monkeypatch.setattr(launcher, "stream_output", lambda _process: None)
    module = {
        "name": "compatibility web",
        "available": True,
        "cmd": ["frontend"],
        "cwd": launcher.BASE_DIR,
        "url": None,
        "setup": ["npm", "install"],
        "needs_setup": True,
    }

    launcher.run_module("test", {"test": module}, open_browser=False)

    assert setup_calls == [["npm", "install"]]
    assert module["needs_setup"] is False


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
    assert 'PYTHON_BIN="python3"' in script
    assert 'PYTHON_BIN="$EFFILIFE_PYTHON"' in script
    assert 'exec "$PYTHON_BIN" launcher/start.py --unified "$@"' in script
    assert 'exit 127' in script


def test_windows_launcher_forwards_extra_arguments():
    script = (Path(launcher.BASE_DIR) / "launcher" / "start.bat").read_text(encoding="utf-8")
    assert "launcher\\start.py --unified %*" in script


def test_windows_launcher_supports_explicit_python_and_noninteractive_exit():
    script = (Path(launcher.BASE_DIR) / "launcher" / "start.bat").read_text(encoding="utf-8")
    assert 'if defined EFFILIFE_PYTHON' in script
    assert '"%EFFILIFE_PYTHON%" launcher\\start.py --unified %*' in script
    assert 'if not exist "%EFFILIFE_PYTHON%"' in script
    assert "EFFILIFE_PYTHON does not exist:" in script
    assert 'if /i not "%EFFILIFE_NO_PAUSE%"=="1" pause' in script
    assert "exit /b %EFFILIFE_LAUNCH_EXIT%" in script


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


def test_launcher_propagates_child_exit_code(monkeypatch):
    class FinishedProcess:
        stdout = None
        returncode = 7

        def poll(self):
            return self.returncode

        def wait(self):
            return self.returncode

    monkeypatch.setattr(launcher.subprocess, "Popen", lambda *args, **kwargs: FinishedProcess())
    monkeypatch.setattr(launcher, "stream_output", lambda _process: None)

    result = launcher.run_module(
        "test",
        {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": launcher.BASE_DIR, "url": None, "setup": None}},
        open_browser=False,
    )

    assert result == 7


def test_launcher_returns_nonzero_when_module_command_is_missing(monkeypatch):
    class MissingPopen:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError("module command missing")

    monkeypatch.setattr(launcher.subprocess, "Popen", MissingPopen)
    result = launcher.run_module(
        "test",
        {"test": {"name": "test", "available": True, "cmd": ["missing"], "cwd": launcher.BASE_DIR, "url": None, "setup": None}},
        open_browser=False,
    )

    assert result == 1


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


def test_launcher_starts_missing_companion_for_existing_frontend_and_tracks_lifecycle(monkeypatch):
    terminated = []
    opened = []
    companion = object()
    checks = iter([True, False])
    module = {
        "name": "workspace",
        "available": True,
        "cmd": ["frontend"],
        "cwd": launcher.BASE_DIR,
        "url": "http://127.0.0.1:1420",
        "setup": None,
        "companions": [{"name": "plan-helper", "url": "http://127.0.0.1:8765"}],
    }
    monkeypatch.setattr(launcher, "service_is_ready", lambda url: next(checks) if url.endswith(":1420") else False)
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [companion])
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url))
    monkeypatch.setattr(launcher.time, "sleep", lambda _seconds: None)

    launcher.run_module("test", {"test": module})

    assert opened == ["http://127.0.0.1:1420"]
    assert terminated == [companion]


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
            "cwd": Path("F:/workspace"),
            "cmd": ["npm", "run", "dev"],
            "setup": ["npm", "install"],
            "available": True,
            "url": "http://127.0.0.1:1420",
            "needs_setup": True,
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
    assert result["modules"]["1"]["runtime_state"] == "ready"
    assert result["modules"]["1"]["cwd"] == str(Path("F:/workspace"))
    assert result["modules"]["1"]["command"] == ["npm", "run", "dev"]
    assert result["modules"]["1"]["setup"] == ["npm", "install"]
    assert result["modules"]["1"]["needs_setup"] is True
    assert result["modules"]["2"]["service_ready"] is False
    assert result["modules"]["2"]["runtime_state"] == "unavailable"
    assert result["modules"]["2"]["unavailable_reason"] == "missing runtime"
    assert result["modules"]["2"]["cwd"] is None
    assert result["modules"]["2"]["command"] == []
    assert result["modules"]["2"]["setup"] == []


def test_launcher_diagnostics_include_nested_companion_health(monkeypatch):
    modules = {
        "1": {
            "name": "workspace",
            "available": True,
            "url": "http://127.0.0.1:1420",
            "companions": [{
                "name": "plan-helper API",
                "cwd": Path("F:/plan-helper"),
                "cmd": ["python", "web/server.py"],
                "url": "http://127.0.0.1:8765",
                "health_url": "http://127.0.0.1:8765/api/health",
            }],
        },
    }
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda url: url.endswith(":8765/api/health"))
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)

    result = launcher.collect_diagnostics(modules)

    companion = result["companions"]["1.1"]
    assert companion["name"] == "plan-helper API"
    assert companion["parent_module"] == "1"
    assert companion["health_url"].endswith("/api/health")
    assert companion["port_occupied"] is True
    assert companion["service_ready"] is False
    assert companion["runtime_state"] == "port-conflict"
    assert any(item["code"] == "companion-port-conflict" for item in result["issues"])


def test_launcher_diagnostics_report_launch_mode_and_binary_candidates(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["start.py", "--packaged", "--diagnose"])
    monkeypatch.setattr(launcher, "find_rust_tool", lambda name: f"{name}.exe")
    result = launcher.collect_diagnostics({})
    assert result["launch_mode"] == "packaged"
    assert result["time_helper_binaries"]
    assert all("path" in item and "exists" in item and "usable" in item for item in result["time_helper_binaries"])
    assert result["rust_toolchain"] == {
        "cargo": "cargo.exe",
        "rustc": "rustc.exe",
        "available": True,
    }
    assert result["installer_artifacts"]
    assert all("path" in item and "exists" in item and "non_empty" in item for item in result["installer_artifacts"])


def test_launcher_diagnostics_distinguish_binary_from_installer(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher.os, "name", "nt")
    bundle = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "bundle" / "nsis"
    bundle.mkdir(parents=True)
    installer = bundle / "EffiLife-setup.exe"
    installer.write_bytes(b"installer")

    result = launcher.collect_diagnostics({})

    assert result["installer_artifacts"] == [{
        "path": str(installer),
        "exists": True,
        "non_empty": True,
        "size": len(b"installer"),
        "artifact_version": None,
        "version_matches": True,
    }]
    assert not any(item["code"] == "installer-artifact-missing" for item in result["hints"])


def test_launcher_marks_old_version_installer_as_stale(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher.os, "name", "nt")
    bundle = tmp_path / "time-helper" / "desk" / "src-tauri" / "target" / "release" / "bundle" / "nsis"
    bundle.mkdir(parents=True)
    installer = bundle / "EffiLife_1.0.11_x64-setup.exe"
    installer.write_bytes(b"installer")

    result = launcher.collect_diagnostics({})

    artifact = result["installer_artifacts"][0]
    assert artifact["artifact_version"] == "1.0.11"
    assert artifact["version_matches"] is False
    assert any(item["code"] == "installer-artifact-stale" for item in result["hints"])
    assert not any(item["code"] == "installer-artifact-missing" for item in result["hints"])


def test_launcher_reports_missing_installer_without_blocking_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "BASE_DIR", tmp_path)
    monkeypatch.setattr(launcher.os, "name", "nt")

    result = launcher.collect_diagnostics({})

    assert result["installer_artifacts"]
    assert any(item["code"] == "installer-artifact-missing" for item in result["hints"])
    assert all(item["severity"] != "error" or item["code"] != "installer-artifact-missing" for item in result["issues"])


def test_launcher_diagnostics_explain_blockers_and_release_hints(monkeypatch):
    modules = {
        "1": {
            "name": "workspace",
            "available": False,
            "unavailable_reason": "missing packaged artifact",
            "url": "http://127.0.0.1:1420",
            "needs_setup": False,
        },
        "2": {
            "name": "companion",
            "available": True,
            "url": "http://127.0.0.1:8765",
            "needs_setup": True,
        },
    }
    monkeypatch.setattr(launcher, "find_node", lambda: None)
    monkeypatch.setattr(launcher, "find_npm", lambda: None)
    monkeypatch.setattr(launcher, "find_rust_tool", lambda _name: None)
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda url: url.endswith(":8765"))
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)

    result = launcher.collect_diagnostics(modules)
    issue_codes = {item["code"] for item in result["issues"]}
    hint_codes = {item["code"] for item in result["hints"]}
    assert "workspace-unavailable" in issue_codes
    assert "port-conflict" in issue_codes
    assert "rust-toolchain-missing" in hint_codes
    assert "dependencies-pending" in hint_codes


def test_launcher_diagnostics_expose_platform_native_toolchain_hints(monkeypatch):
    monkeypatch.setattr(launcher.os, "name", "nt")
    monkeypatch.setattr(launcher, "find_node", lambda: "node.exe")
    monkeypatch.setattr(launcher, "find_npm", lambda: "npm.cmd")
    monkeypatch.setattr(launcher, "find_rust_tool", lambda _name: None)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)

    result = launcher.collect_diagnostics({})

    assert result["native_toolchain"]["android"]["ready"] is False
    assert result["native_toolchain"]["ios"]["platform_supported"] is False
    hint_codes = {item["code"] for item in result["hints"]}
    assert "android-toolchain-missing" in hint_codes
    assert "ios-toolchain-missing" in hint_codes


def test_diagnose_output_uses_ascii_safe_json():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert "json.dumps(collect_diagnostics(modules), ensure_ascii=True" in source


def test_launcher_doctor_renders_actionable_human_output(capsys):
    report = {
        "version": "1.7.0",
        "launch_mode": "development",
        "python": "python.exe",
        "node": None,
        "npm": None,
        "modules": {"1": {"available": False, "url": "http://127.0.0.1:1420"}},
        "issues": [{"message": "workspace missing", "hint": "Install Node.js/npm"}],
        "hints": [{"message": "Rust is only needed for installers"}],
    }
    assert launcher.print_doctor_report(report) is False
    output = capsys.readouterr().out
    assert "EffiLife launcher doctor" in output
    assert "Blocking issues:" in output
    assert "Next: Install Node.js/npm" in output
    assert "Result: BLOCKED" in output


def test_launcher_doctor_distinguishes_stale_installer(capsys):
    report = {
        "version": "1.7.0",
        "launch_mode": "development",
        "python": "python.exe",
        "node": "node.exe",
        "npm": "npm.cmd",
        "installer_artifacts": [{"exists": True, "non_empty": True, "version_matches": False}],
        "modules": {"1": {"available": True, "url": "http://127.0.0.1:1420"}},
        "issues": [],
        "hints": [],
    }
    assert launcher.print_doctor_report(report) is True
    assert "Native installer: stale (version mismatch)" in capsys.readouterr().out


def test_launcher_doctor_identifies_stale_installer_details(capsys):
    report = {
        "version": "1.7.0",
        "launch_mode": "development",
        "python": "python.exe",
        "node": "node.exe",
        "npm": "npm.cmd",
        "installer_artifacts": [{
            "path": "target/release/bundle/nsis/EffiLife_1.0.11_x64-setup.exe",
            "exists": True,
            "non_empty": True,
            "artifact_version": "1.0.11",
            "version_matches": False,
        }],
        "modules": {"1": {"available": True, "url": "http://127.0.0.1:1420"}},
        "issues": [],
        "hints": [],
    }

    assert launcher.print_doctor_report(report) is True
    output = capsys.readouterr().out
    assert "target/release/bundle/nsis/EffiLife_1.0.11_x64-setup.exe" in output
    assert "artifact 1.0.11, current 1.7.0" in output


def test_launcher_doctor_is_wired_before_normal_startup():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")
    assert 'if "--doctor" in sys.argv:' in source
    assert "print_doctor_report(collect_diagnostics(modules))" in source


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
