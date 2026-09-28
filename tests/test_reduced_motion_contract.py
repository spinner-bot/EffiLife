from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOTION = (ROOT / "time-helper" / "desk" / "src" / "motion" / "MotionManager.ts").read_text(encoding="utf-8")


def test_motion_manager_reads_and_reacts_to_system_reduced_motion():
    assert "prefers-reduced-motion: reduce" in MOTION
    assert "addEventListener('change', onChange)" in MOTION
    assert "motionState.systemReducedMotion = event.matches" in MOTION


def test_system_reduced_motion_disables_all_javascript_motion_surfaces():
    assert "!motionState.systemReducedMotion" in MOTION
    assert "motionState.systemReducedMotion" in MOTION and "getFrameInterval" in MOTION
    assert MOTION.count("!motionState.systemReducedMotion") >= 3

