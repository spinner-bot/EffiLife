from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
GATEWAY = (ROOT / "time-helper/desk/src/services/planGateway.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_builtin_plan_templates_use_localized_labels_and_custom_templates_keep_server_text():
    assert "function mobileTemplateSummary(template: MobileTemplateDefinition): PlanTemplateSummary" in GATEWAY
    assert "name: translate(template.nameKey)" in GATEWAY
    assert "description: translate(template.descriptionKey)" in GATEWAY
    for template_type in ("workday", "weekend", "exam"):
        assert f"plans.templateTypes.{template_type}Name" in GATEWAY
        assert f"plans.templateTypes.{template_type}Description" in GATEWAY
        assert I18N.count(f"'plans.templateTypes.{template_type}Name':") == 2
        assert I18N.count(f"'plans.templateTypes.{template_type}Description':") == 2
