from launcher import start


def test_invalid_launcher_ports_fall_back_to_stable_defaults(monkeypatch):
    monkeypatch.setenv("EFFILIFE_WORKSPACE_PORT", "80")
    monkeypatch.setenv("EFFILIFE_TODOS_PORT", "not-a-port")
    monkeypatch.setenv("EFFILIFE_PLAN_HELPER_PORT", "70000")

    assert start.workspace_port() == 1420
    assert start.todos_port() == 1421
    assert start.plan_helper_port() == 8765


def test_valid_launcher_ports_are_shared_by_urls_and_commands(monkeypatch):
    monkeypatch.setenv("EFFILIFE_WORKSPACE_PORT", "2420")
    monkeypatch.setenv("EFFILIFE_TODOS_PORT", "2421")
    monkeypatch.setenv("EFFILIFE_PLAN_HELPER_PORT", "8876")

    assert start.local_url(start.workspace_port()) == "http://127.0.0.1:2420"
    assert "--port" in start.plan_helper_command()
    assert start.plan_helper_command()[start.plan_helper_command().index("--port") + 1] == "8876"

    modules = start.build_modules()
    assert modules["1"]["companions"][0]["url"] == "http://127.0.0.1:8876"


def test_diagnostics_exposes_effective_ports(monkeypatch):
    monkeypatch.setenv("EFFILIFE_WORKSPACE_PORT", "3420")
    monkeypatch.setenv("EFFILIFE_TODOS_PORT", "3421")
    monkeypatch.setenv("EFFILIFE_PLAN_HELPER_PORT", "9876")

    report = start.collect_diagnostics(start.build_modules())

    assert report["ports"] == {"workspace": 3420, "todos": 3421, "plan_helper": 9876}
