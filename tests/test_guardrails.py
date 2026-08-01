from src.guardrails import validate_profile
from src.main import EDGE_CASE_PROFILES


def test_missing_keys_get_safe_defaults():
    clean, corrections = validate_profile({})
    assert clean == {"genre": "", "mood": "", "energy": 0.5, "likes_acoustic": False}
    assert len(corrections) == 4


def test_non_dict_input_does_not_raise():
    clean, corrections = validate_profile(None)
    assert clean == {"genre": "", "mood": "", "energy": 0.5, "likes_acoustic": False}
    assert any("expected a dict" in c for c in corrections)


def test_typo_genre_case_mismatch_is_normalized():
    raw = EDGE_CASE_PROFILES["Typo Genre (case mismatch)"]
    clean, corrections = validate_profile(raw)
    assert clean["genre"] == "rock"
    assert clean["mood"] == "happy"
    assert any("genre" in c for c in corrections)


def test_overshoot_energy_is_clamped():
    raw = EDGE_CASE_PROFILES["Overshoot Energy (target > 1.0)"]
    clean, corrections = validate_profile(raw)
    assert clean["energy"] == 1.0
    assert any("clamped" in c for c in corrections)


def test_truthy_string_acoustic_bug_is_fixed():
    raw = EDGE_CASE_PROFILES["String Acoustic Flag (truthy-string bug)"]
    # Sanity-check the bug actually exists in raw Python before the fix:
    assert bool(raw["likes_acoustic"]) is True

    clean, corrections = validate_profile(raw)
    assert clean["likes_acoustic"] is False
    assert any("likes_acoustic" in c and "False" in c for c in corrections)


def test_well_formed_profile_gets_no_corrections():
    clean, corrections = validate_profile(
        {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    )
    assert clean == {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    assert corrections == []


def test_non_numeric_energy_defaults_to_midpoint():
    clean, corrections = validate_profile({"energy": "loud"})
    assert clean["energy"] == 0.5
    assert any("energy" in c for c in corrections)


def test_true_string_variants_map_to_true():
    for value in ("true", "Yes", "1"):
        clean, _ = validate_profile({"likes_acoustic": value})
        assert clean["likes_acoustic"] is True
