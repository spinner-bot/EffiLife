from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_unified_shell_keeps_three_independent_module_routes():
    router = (DESK / "router" / "index.ts").read_text(encoding="utf-8")
    home = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert "path: '/plans'" in router
    assert "path: '/time'" in router
    assert "path: '/tasks'" in router
    assert 'class="home-module-code">TH<' in home
    assert 'class="home-module-code">PH<' in home
    assert 'class="home-module-code">TD<' in home


def test_calendar_is_not_an_active_module_route():
    router = (DESK / "router" / "index.ts").read_text(encoding="utf-8")
    assert "path: '/calendar'" in router
    assert "redirect: '/records'" in router
    assert "component: () => import('@/views/Calendar" not in router


def test_plan_gateway_preserves_sections_groups_and_logs():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")
    assert "sections: PlanSection[]" in gateway
    assert "groups: Record<string" in gateway
    assert "logs: Array<" in gateway
    assert "internal_index" in gateway


def test_task_center_uses_todo_service_boundary_not_plan_gateway():
    task_center = (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "from '@/services/todoService'" in task_center
    assert "from '@/services/planGateway'" not in task_center
