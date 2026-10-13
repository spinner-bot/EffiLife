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

        # HOTL/1 requires PH (whole plans) and TD (single quick todos) to be
        # independently discoverable, while the desktop home remains a
        # horizontally structured command center rather than a mobile-only
        # stack. Verify the shell and dashboard contract in a real browser.
        page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1200)
        home_startup_alert = page.locator('[role="alertdialog"]')
        if home_startup_alert.count():
            home_startup_alert.locator(".confirm-cancel").click(timeout=5000)
        desktop_nav = page.locator(".desktop-nav-links")
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
        workspace_module_separation = True
        desktop_dashboard_layout = True

        for route in ROUTES:
            page.goto(f"{base_url.rstrip('/')}{route}", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(250)
            if page.locator("#app").count() != 1 or not page.locator("#app").inner_text().strip():
                raise RuntimeError(f"route did not render an app shell: {route}")
            rendered_routes.append(route)

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
    args = parser.parse_args()
    try:
        result = run_smoke(
            args.url,
            headless=not args.headed,
            inject_write_failure=args.inject_write_failure,
            archive_roundtrip=args.archive_roundtrip,
        )
    except Exception as error:  # noqa: BLE001 - CLI should report a concise actionable failure
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result.__dict__}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
