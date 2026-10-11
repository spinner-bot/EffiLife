from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOTION = (ROOT / "time-helper" / "desk" / "src" / "motion" / "MotionManager.ts").read_text(encoding="utf-8")
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_motion_manager_reads_and_reacts_to_system_reduced_motion():
    assert "prefers-reduced-motion: reduce" in MOTION
    assert "addEventListener('change', onChange)" in MOTION
    assert "motionState.systemReducedMotion = event.matches" in MOTION


def test_system_reduced_motion_disables_all_javascript_motion_surfaces():
    assert "!motionState.systemReducedMotion" in MOTION
    assert "motionState.systemReducedMotion" in MOTION and "getFrameInterval" in MOTION
    assert MOTION.count("!motionState.systemReducedMotion") >= 3


def test_app_shell_applies_system_reduced_motion_to_css_surfaces():
    assert "animation-duration: .01ms !important" in APP
    assert "animation-iteration-count: 1 !important" in APP
    assert "transition-duration: .01ms !important" in APP
    assert "scroll-behavior: auto !important" in APP
    assert "*, *::before, *::after" in APP

