from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOTION = ROOT / "time-helper" / "desk" / "src" / "motion" / "MotionManager.ts"
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "MotionSettingsView.vue"


def test_motion_settings_expose_only_supported_fps_presets():
    source = VIEW.read_text(encoding="utf-8")
    for value in ("value: 5", "value: 10", "value: 15", "value: 30"):
        assert value in source


def test_auto_recommendation_changes_only_target_fps():
    source = MOTION.read_text(encoding="utf-8")
    assert "const currentSettings = { ...motionState.settings }" in source
    assert "...currentSettings" in source
    assert "targetFps: recommendedFps" in source
    assert "particleCountMultiplier" not in source.split("private generateRecommendation", 1)[1].split("getBenchmarkResults", 1)[0]
