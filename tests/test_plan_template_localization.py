from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_builtin_plan_templates_use_localized_labels_and_custom_templates_keep_server_text():
    assert "function templateName(template: PlanTemplateSummary): string" in VIEW
    assert "function templateDescription(template: PlanTemplateSummary): string" in VIEW
    assert "if (!template.built_in) return template.name" in VIEW
    assert "if (!template.built_in) return template.description" in VIEW
    for template_type in ("workday", "weekend", "exam"):
        assert f"plans.templateTypes.{template_type}Name" in VIEW
        assert f"plans.templateTypes.{template_type}Description" in VIEW
        assert I18N.count(f"'plans.templateTypes.{template_type}Name':") == 2
        assert I18N.count(f"'plans.templateTypes.{template_type}Description':") == 2
