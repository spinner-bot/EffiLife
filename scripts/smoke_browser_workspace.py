"""Run a small real-browser smoke test against a running EffiLife web build.

This intentionally does not start a dev server. The caller supplies a running
URL so the same check can be used against a local Vite server or a packaged
static preview. Playwright is an optional verification dependency, not an
application runtime dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


ROUTES = ("/time", "/plans", "/tasks", "/records", "/settings")


@dataclass
class SmokeResult:
    routes: list[str]
    workspace_module_separation: bool
    desktop_dashboard_layout: bool
    theme_cards: int
    theme_save_buttons: int
    theme_exit_confirmed: bool
    theme_persistence_verified: bool
    locale_persistence_verified: bool
    ph_plan_flow_verified: bool
    td_task_flow_verified: bool
    td_focus_flow_verified: bool
    td_cross_window_focus_verified: bool
    th_record_flow_verified: bool
    th_quick_capture_verified: bool
    th_quick_capture_shortcut_verified: bool
    ph_td_link_flow_verified: bool
    storage_write_failure_handled: bool
    archive_roundtrip: bool
    mobile_navigation: bool
    confirm_keyboard_accessible: bool


def run_smoke(
    base_url: str,
    *,
    headless: bool = True,
    inject_write_failure: bool = False,
    archive_roundtrip: bool = False,
    ph_plan_flow: bool = False,
    td_task_flow: bool = False,
    td_focus_flow: bool = False,
    th_record_flow: bool = False,
) -> SmokeResult:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:  # pragma: no cover - exercised by the CLI environment
        raise RuntimeError(
            "Playwright is required for browser smoke tests; install it in the verification environment"
        ) from error

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context()
        # First-run onboarding is outside this smoke test. Mark it complete so
        # it cannot intercept the route and theme controls being verified.
        context.add_init_script("localStorage.setItem('efflife_guide_completed', 'true')")
        page = context.new_page()
        rendered_routes: list[str] = []
        ph_plan_flow_verified = False
        td_task_flow_verified = False
        td_focus_flow_verified = False
        td_cross_window_focus_verified = False
        th_record_flow_verified = False
        th_quick_capture_verified = False
        th_quick_capture_shortcut_verified = False
        ph_td_link_flow_verified = False

        # HOTL/1 requires PH (whole plans) and TD (single quick todos) to be
        # independently discoverable, while the desktop home remains a
        # horizontally structured command center rather than a mobile-only
        # stack. Verify the shell and dashboard contract in a real browser.
        page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
        page.locator(".overview-grid").wait_for(state="visible", timeout=15000)
        page.wait_for_timeout(300)
        home_startup_alert = page.locator('[role="alertdialog"]')
        if home_startup_alert.count() and home_startup_alert.first.is_visible():
            home_startup_alert.first.locator(".confirm-cancel").click(timeout=5000)
        desktop_nav = page.locator(".desktop-nav-links")
        desktop_nav.wait_for(state="visible", timeout=10000)
        if not desktop_nav.is_visible():
            raise RuntimeError("desktop navigation is not visible at the default viewport")
        desktop_nav_links = desktop_nav.locator(".global-nav-link")
        if desktop_nav_links.count() < 6:
            raise RuntimeError("desktop navigation does not expose the full workspace")
        nav_hrefs = [desktop_nav_links.nth(index).get_attribute("href") for index in range(desktop_nav_links.count())]
        if "/plans" not in nav_hrefs or "/tasks" not in nav_hrefs or "/plans" == "/tasks":
            raise RuntimeError("PH and TD do not have distinct desktop navigation entries")
        if page.locator('.workflow-summary-item').count() != 3:
            raise RuntimeError("dashboard does not expose separate TH, PH and TD summary entries")
        summary_codes = page.locator('.workflow-summary-icon small')
        if [summary_codes.nth(index).inner_text() for index in range(summary_codes.count())] != ["TH", "PH", "TD"]:
            raise RuntimeError("dashboard module summary order or labels are incorrect")
        if page.locator('.overview-grid').count() != 1:
            raise RuntimeError("desktop dashboard is missing its multi-column overview region")
        page.bring_to_front()
        page.locator("body").click(position={"x": 8, "y": 8})
        # Chromium reserves Control+Shift+T for reopening a closed tab. Use
        # the browser-safe application fallback while keeping the native
        # desktop shortcut covered by the app-shell contract tests.
        page.keyboard.press("Alt+Shift+t")
        page.wait_for_timeout(700)
        if "/time" not in page.url or page.locator(".pv-modal").count() != 1:
            raise RuntimeError("TH keyboard shortcut did not open the time-record form")
        page.keyboard.press("Escape")
        page.locator(".pv-modal").wait_for(state="hidden", timeout=3000)
        th_quick_capture_shortcut_verified = True
        page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
        page.locator(".desktop-nav-links").wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(300)
        quick_record = page.locator('.home-time-action')
        if quick_record.count() != 1:
            raise RuntimeError("dashboard does not expose the TH quick record action")
        quick_record.click(timeout=5000)
        page.wait_for_timeout(700)
        if "/time" not in page.url or page.locator(".pv-modal").count() != 1:
            raise RuntimeError("TH quick record action did not open the time-record form")
        if "compose=1" in page.url:
            raise RuntimeError("TH quick record deep link query was not consumed")
        if not page.evaluate("Boolean(document.activeElement?.closest('.pv-modal'))"):
            raise RuntimeError("TH quick record form did not receive focus")
        page.keyboard.press("Escape")
        page.locator(".pv-modal").wait_for(state="hidden", timeout=3000)
        if page.locator(".pv-modal").is_visible():
            raise RuntimeError("TH quick record form did not close with Escape")
        th_quick_capture_verified = True
        page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(300)
        workspace_module_separation = True
        desktop_dashboard_layout = True

        for route in ROUTES:
            page.goto(f"{base_url.rstrip('/')}{route}", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(250)
            if page.locator("#app").count() != 1 or not page.locator("#app").inner_text().strip():
                raise RuntimeError(f"route did not render an app shell: {route}")
            rendered_routes.append(route)

        if ph_plan_flow:
            # This opt-in path requires a running Plan Helper endpoint. It is
            # kept separate from the browser-only smoke so CI can choose the
            # appropriate service boundary explicitly.
            page.goto(f"{base_url.rstrip('/')}/plans", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1200)
            plan_startup_alert = page.locator('[role="alertdialog"]')
            if plan_startup_alert.count():
                plan_startup_alert.locator(".confirm-cancel").click(timeout=5000)
            create_button = page.locator(".plan-entry-actions button.plans-primary")
            if create_button.count() != 1:
                raise RuntimeError("PH plan flow did not expose the new-plan entry")
            create_button.click(timeout=5000)
            create_modal = page.locator(".create-modal")
            create_modal.wait_for(state="visible", timeout=5000)
            create_inputs = create_modal.locator("input")
            if create_inputs.count() < 5:
                raise RuntimeError("PH create dialog did not expose plan, section and task fields")
            expected_today = page.evaluate("(() => { const date = new Date(); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}` })()")
            if create_inputs.nth(1).input_value() != expected_today:
                raise RuntimeError("PH create dialog did not default its date to today")
            create_inputs.nth(0).fill("Smoke whole plan")
            create_inputs.nth(2).fill("Smoke section")
            create_inputs.nth(4).fill("Smoke plan task")
            create_modal.locator("button.plans-primary").click(timeout=5000)
            page.wait_for_timeout(1000)
            if create_modal.is_visible():
                raise RuntimeError(f"PH create dialog remained open after submit: {create_modal.inner_text()[:500]}")
            if page.locator(".plan-detail-layout").count() != 1 or page.get_by_text("Smoke plan task", exact=True).count() != 1:
                raise RuntimeError("PH create flow did not produce a plan with content")
            page.locator(".detail-actions button.plans-secondary").first.click(timeout=5000)
            meta_editor = page.locator(".meta-editor")
            meta_editor.wait_for(state="visible", timeout=5000)
            meta_editor.locator("input").first.fill("Smoke whole plan edited")
            meta_editor.locator("button.plans-primary").click(timeout=5000)
            page.wait_for_timeout(700)
            if page.locator(".plans-header h1").get_by_text("Smoke whole plan edited", exact=True).count() != 1:
                raise RuntimeError("PH edit flow did not persist plan metadata")
            page.locator(".plan-todo-action").click(timeout=5000)
            link_confirm = page.locator('[role="alertdialog"]')
            link_confirm.wait_for(state="visible", timeout=5000)
            link_confirm.locator(".confirm-submit").click(timeout=5000)
            page.wait_for_timeout(700)
            page.goto(f"{base_url.rstrip('/')}/tasks", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            linked_task = page.locator("article.task-item").filter(has_text="Smoke plan task")
            linked_task.wait_for(state="visible", timeout=5000)
            if linked_task.locator("button.task-plan-reference").count() != 1:
                raise RuntimeError("PH-to-TD link was not visible in the task center")
            ph_td_link_flow_verified = True
            ph_plan_flow_verified = True

        if td_task_flow:
            # TD uses the workspace's local data store and intentionally does
            # not require Plan Helper. Keep this flow independent from PH so
            # a single quick todo remains a first-class item.
            page.goto(f"{base_url.rstrip('/')}/tasks", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            task_input = page.locator("#new-task-title")
            task_input.wait_for(state="visible", timeout=5000)
            task_input.fill("Smoke quick todo")
            page.locator("form.task-create button.task-add").click(timeout=5000)
            task_item = page.locator("article.task-item").filter(has_text="Smoke quick todo")
            task_item.wait_for(state="visible", timeout=5000)
            task_item.locator("button.task-check").click(timeout=5000)
            page.locator("#tasks-tab-completed").click(timeout=5000)
            page.wait_for_timeout(400)
            if page.locator("article.task-item.completed").filter(has_text="Smoke quick todo").count() != 1:
                raise RuntimeError("TD complete flow did not retain the completed quick todo")
            td_task_flow_verified = True

        if td_focus_flow:
            page.goto(f"{base_url.rstrip('/')}/tasks", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            task_input = page.locator("#new-task-title")
            task_input.fill("Smoke focus todo")
            page.locator("form.task-create button.task-add").click(timeout=5000)
            task_item = page.locator("article.task-item").filter(has_text="Smoke focus todo")
            task_item.wait_for(state="visible", timeout=5000)
            page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            home_todo = page.locator(".today-todo-row").filter(has_text="Smoke focus todo")
            home_todo.wait_for(state="visible", timeout=5000)
            home_todo.locator("button.today-todo-focus").click(timeout=5000)
            page.locator(".active-focus-bar").wait_for(state="visible", timeout=5000)
            cross_window_page = context.new_page()
            cross_window_page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
            cross_window_page.locator(".active-focus-bar").wait_for(state="visible", timeout=7000)
            cross_window_page.locator(".active-focus-stop").click(timeout=5000)
            page.locator(".active-focus-bar").wait_for(state="hidden", timeout=10000)
            cross_window_page.locator(".active-focus-bar").wait_for(state="hidden", timeout=10000)
            cross_window_page.close()
            td_cross_window_focus_verified = True
            if "/tasks" not in page.url:
                raise RuntimeError("active focus stop did not return to TD")
            td_focus_flow_verified = True

        if th_record_flow:
            # TH records stay in the unified local data store and are
            # independent from both PH plans and TD tasks.
            page.goto(f"{base_url.rstrip('/')}/time", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            page.locator("button.pv-add-btn").click(timeout=5000)
            record_modal = page.locator(".pv-modal")
            record_modal.wait_for(state="visible", timeout=5000)
            content_input = record_modal.locator("input.pv-text-input").first
            content_input.fill("Smoke time record")
            record_modal.locator(".pv-modal-footer .pv-primary-btn").click(timeout=5000)
            record_card = page.locator(".pv-record-card").filter(has_text="Smoke time record")
            record_card.wait_for(state="visible", timeout=5000)
            page.reload(wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(700)
            if page.locator(".pv-record-card").filter(has_text="Smoke time record").count() != 1:
                raise RuntimeError("TH time record was not durable after reload")
            th_record_flow_verified = True

        mobile_page = context.new_page()
        mobile_page.set_viewport_size({"width": 390, "height": 844})
        mobile_page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
        mobile_page.wait_for_timeout(1200)
        mobile_startup_alert = mobile_page.locator('[role="alertdialog"]')
        if mobile_startup_alert.count():
            mobile_startup_alert.locator(".confirm-cancel").click(timeout=5000)
        mobile_nav = mobile_page.locator(".mobile-bottom-nav")
        mobile_nav.wait_for(state="visible", timeout=10000)
        if mobile_page.locator(".desktop-nav-links").is_visible():
            raise RuntimeError("desktop navigation remained visible at mobile viewport")
        if mobile_page.locator(".mobile-bottom-nav-link").count() != 6:
            raise RuntimeError("mobile navigation does not expose all six workspace entries")
        if not mobile_page.locator(".mobile-quick-capture").is_visible():
            raise RuntimeError("mobile quick capture is not visible above bottom navigation")
        if not mobile_page.locator(".home-time-action").is_visible():
            raise RuntimeError("mobile dashboard does not expose the TH quick record action")
        mobile_page.close()

        page.goto(f"{base_url.rstrip('/')}/settings", wait_until="domcontentloaded", timeout=15000)
        settings_items = page.locator("button.settings-item")
        page.wait_for_timeout(1200)
        startup_alert = page.locator('[role="alertdialog"]')
        if startup_alert.count():
            startup_alert.locator(".confirm-cancel").click(timeout=5000)
        try:
            settings_items.first.wait_for(state="visible", timeout=10000)
        except Exception as error:  # noqa: BLE001 - convert locator timeout to a smoke failure
            raise RuntimeError("settings main view did not render its entries") from error
        if settings_items.count() < 2:
            raise RuntimeError("settings main view did not expose the theme entry")
        locale_select = page.locator(".locale-switcher select")
        if locale_select.count() != 1:
            raise RuntimeError("settings main view did not expose the language selector")
        original_locale = locale_select.input_value()
        locale_select.select_option("en-US")
        page.wait_for_timeout(200)
        if page.locator("html").get_attribute("lang") != "en-US":
            raise RuntimeError("language selector did not update the document locale")
        page.reload(wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1200)
        reload_startup_alert = page.locator('[role="alertdialog"]')
        if reload_startup_alert.count():
            reload_startup_alert.locator(".confirm-cancel").click(timeout=5000)
        if page.locator(".locale-switcher select").input_value() != "en-US":
            raise RuntimeError("language selection was not durable after reload")
        locale_persistence_verified = True
        page.locator(".locale-switcher select").select_option(original_locale)
        page.wait_for_timeout(150)
        settings_items.nth(1).click(timeout=5000)
        page.wait_for_timeout(300)

        cards = page.locator("button.theme-card")
        save_buttons = page.locator("button.btn.primary")
        theme_card_count = cards.count()
        theme_save_button_count = save_buttons.count()
        theme_persistence_verified = False
        if theme_card_count < 2:
            raise RuntimeError("theme view exposes fewer than two themes")
        if theme_save_button_count != 0:
            raise RuntimeError("theme view unexpectedly exposes a save button")

        active_index = next(
            (index for index in range(theme_card_count) if cards.nth(index).get_attribute("aria-pressed") == "true"),
            None,
        )
        if active_index is None:
            raise RuntimeError("theme view has no selected theme")
        cards.nth(0 if active_index != 0 else 1).click(timeout=5000)
        page.wait_for_timeout(200)
        if page.locator('button.theme-card[aria-pressed="true"]').count() != 1:
            raise RuntimeError("theme selection did not settle on exactly one active card")

        if inject_write_failure:
            # The application has already initialized IndexedDB. Fail only
            # the next object-store write so this exercises the transaction
            # error path rather than the database-open fallback path.
            page.evaluate(
                "void (IDBObjectStore.prototype.put = function () { throw new Error('injected indexeddb write failure') })"
            )

        page.locator("button.back-btn").click(timeout=5000)
        page.wait_for_timeout(300)
        alert = page.locator('[role="alertdialog"]')
        if alert.count() != 1:
            raise RuntimeError("leaving a dirty theme editor did not show an alert dialog")
        if not alert.get_attribute("aria-labelledby") or not alert.get_attribute("aria-describedby"):
            raise RuntimeError("theme exit alert dialog is missing accessible name or description")
        if page.evaluate("document.activeElement?.className") != "confirm-cancel":
            raise RuntimeError("alert dialog did not move focus to its cancel action")
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement?.className") != "confirm-submit":
            raise RuntimeError("alert dialog Tab order did not reach its confirm action")
        page.keyboard.press("Shift+Tab")
        if page.evaluate("document.activeElement?.className") != "confirm-cancel":
            raise RuntimeError("alert dialog focus trap did not return to cancel action")
        alert.locator(".confirm-submit").click(timeout=5000)
        page.wait_for_timeout(500)
        if inject_write_failure:
            if page.locator("button.theme-card").count() == 0:
                raise RuntimeError("failed theme save incorrectly left the theme editor")
            if page.locator(".toast-error").count() == 0:
                raise RuntimeError("failed theme save did not expose an error toast")
        elif page.locator("button.settings-item").count() < 2:
            raise RuntimeError("confirmed theme exit did not return to settings")
        else:
            # Re-enter the editor after the save and verify the durable
            # selection is the same one that was confirmed. This catches the
            # historical bug where the preview changed but reload restored
            # the previous theme.
            page.locator("button.settings-item").nth(1).click(timeout=5000)
            page.wait_for_timeout(300)
            persisted_active = page.locator('button.theme-card[aria-pressed="true"]')
            if persisted_active.count() != 1 or cards.nth(0 if active_index != 0 else 1).get_attribute("aria-pressed") != "true":
                raise RuntimeError("confirmed theme selection was not durable after re-entering the editor")
            theme_persistence_verified = True
            page.locator("button.back-btn").click(timeout=5000)
            page.wait_for_timeout(200)

        if archive_roundtrip:
            # Export and import the same archive through the browser file
            # picker. This exercises the actual .efl delivery path without
            # introducing synthetic archive data into the user's workspace.
            page.locator("button.settings-item").nth(5).click(timeout=5000)
            page.locator(".archive-actions button").first.wait_for(state="visible", timeout=10000)
            with page.expect_download(timeout=15000) as download_info:
                page.locator(".archive-actions button").nth(0).click(timeout=5000)
            archive_path = download_info.value.path()
            if not archive_path:
                raise RuntimeError("browser archive export did not provide a file path")
            page.locator('input[type="file"]').first.set_input_files(archive_path)
            page.wait_for_timeout(800)
            import_confirm = page.locator('[role="alertdialog"]')
            if import_confirm.count() != 1:
                raise RuntimeError("archive import did not show its preview confirmation")
            import_confirm.locator(".confirm-submit").click(timeout=5000)
            page.wait_for_timeout(1200)
            reload_confirm = page.locator('[role="alertdialog"]')
            if reload_confirm.count():
                reload_confirm.locator(".confirm-cancel").click(timeout=5000)
            if page.locator(".toast-success").count() == 0:
                raise RuntimeError("archive roundtrip did not report success")

        browser.close()

    return SmokeResult(
        routes=rendered_routes,
        workspace_module_separation=workspace_module_separation,
        desktop_dashboard_layout=desktop_dashboard_layout,
        theme_cards=theme_card_count,
        theme_save_buttons=theme_save_button_count,
        theme_exit_confirmed=not inject_write_failure,
        theme_persistence_verified=theme_persistence_verified,
        locale_persistence_verified=locale_persistence_verified,
        ph_plan_flow_verified=ph_plan_flow_verified,
        td_task_flow_verified=td_task_flow_verified,
        td_focus_flow_verified=td_focus_flow_verified,
        td_cross_window_focus_verified=td_cross_window_focus_verified,
        th_record_flow_verified=th_record_flow_verified,
        th_quick_capture_verified=th_quick_capture_verified,
        th_quick_capture_shortcut_verified=th_quick_capture_shortcut_verified,
        ph_td_link_flow_verified=ph_td_link_flow_verified,
        storage_write_failure_handled=inject_write_failure,
        archive_roundtrip=archive_roundtrip,
        mobile_navigation=True,
        confirm_keyboard_accessible=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:4173", help="running EffiLife web URL")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument(
        "--inject-write-failure",
        action="store_true",
        help="fail the next IndexedDB object-store write and verify error recovery",
    )
    parser.add_argument(
        "--archive-roundtrip",
        action="store_true",
        help="export and re-import a browser .efl archive through the file picker",
    )
    parser.add_argument(
        "--ph-plan-flow",
        action="store_true",
        help="verify PH create-with-content and edit flow; requires a running Plan Helper service",
    )
    parser.add_argument(
        "--td-task-flow",
        action="store_true",
        help="verify TD quick-capture and completion flow in isolated browser storage",
    )
    parser.add_argument(
        "--td-focus-flow",
        action="store_true",
        help="verify TD focus sessions survive route changes and stop through the shell",
    )
    parser.add_argument(
        "--th-record-flow",
        action="store_true",
        help="verify TH time-record creation and reload persistence in isolated browser storage",
    )
    args = parser.parse_args()
    try:
        result = run_smoke(
            args.url,
            headless=not args.headed,
            inject_write_failure=args.inject_write_failure,
            archive_roundtrip=args.archive_roundtrip,
            ph_plan_flow=args.ph_plan_flow,
            td_task_flow=args.td_task_flow,
            td_focus_flow=args.td_focus_flow,
            th_record_flow=args.th_record_flow,
        )
    except Exception as error:  # noqa: BLE001 - CLI should report a concise actionable failure
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result.__dict__}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
