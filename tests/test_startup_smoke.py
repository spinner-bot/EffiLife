from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "smoke_startup.py"


def test_startup_smoke_is_bounded_and_checks_both_unified_services():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"--no-browser"' in source
    assert "def wait_for_endpoint" in source
    assert "application-name" in source
    assert "EffiLife" in source
    assert '"service":"plan-helper"' in source
    assert '"status":"ok"' in source
    assert '"".join(body.split())' in source
    assert "stop_process_tree(process)" in source
    assert "wait_for_ports_to_close(ports)" in source


def test_startup_smoke_refuses_to_take_over_existing_ports():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "configured smoke-test ports are already in use" in source
    assert "occupied = [port for port in ports" in source
