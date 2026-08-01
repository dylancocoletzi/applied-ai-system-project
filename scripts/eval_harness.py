"""
Standalone reliability-evaluation script for the VibeFit Agent extension.

Runs the REAL pipeline (no mocks) against a battery of free-text and
structured-profile inputs, checks a set of invariants, and prints a
pass/fail summary. Exit code is 0 if everything passed, 1 otherwise.

Run from the repo root:
    python3 -m scripts.eval_harness
"""
import sys
from pathlib import Path

from src.agent import run_agent
from src.guardrails import validate_profile
from src.main import EDGE_CASE_PROFILES, USER_PROFILES
from src.recommender import load_songs, recommend_songs

SONGS_CSV = Path(__file__).resolve().parent.parent / "data" / "songs.csv"

FREE_TEXT_CASES = [
    "something upbeat pop for a workout",
    "sad acoustic songs for a rainy day",
    "deep intense rock",
    "",
    "asdkjfh qwoeiru zzz",
]

AMBIGUOUS_CASES = {
    "play me something": "low_confidence",
    "aggressive metal but keep it chill and acoustic": "contradiction",
}

MALFORMED_PROFILES = [
    {},
    None,
    {"genre": 123, "mood": None, "energy": "loud", "likes_acoustic": "maybe"},
    {"energy": "not a number"},
]


def check_determinism():
    for text in FREE_TEXT_CASES:
        first = run_agent(text, k=3)
        second = run_agent(text, k=3)
        first_ids = [s["id"] for s, _, _ in first["recommendations"]]
        second_ids = [s["id"] for s, _, _ in second["recommendations"]]
        assert first_ids == second_ids, f"non-deterministic output for {text!r}"
    return f"{len(FREE_TEXT_CASES)}/{len(FREE_TEXT_CASES)} cases"


def check_score_bounds():
    count = 0
    songs = load_songs(str(SONGS_CSV))
    all_profiles = list(USER_PROFILES.values()) + list(EDGE_CASE_PROFILES.values())
    for profile in all_profiles:
        clean, _ = validate_profile(profile)
        for _, score, _ in recommend_songs(clean, songs, k=5):
            assert 0.0 <= score <= 1.0, f"score {score} out of [0, 1] bounds"
            count += 1
    return f"{count} scores checked across {len(all_profiles)} profiles"


def check_no_crash_on_malformed_input():
    total = 0
    for text in FREE_TEXT_CASES:
        run_agent(text, k=3)
        total += 1
    for profile in MALFORMED_PROFILES:
        validate_profile(profile)
        total += 1
    return f"{total}/{total} inputs handled without raising"


def check_confidence_flags_fire():
    for text, expected in AMBIGUOUS_CASES.items():
        result = run_agent(text, k=3)
        flags = " ".join(result["critique_flags"]).lower()
        if expected == "low_confidence":
            assert "couldn't confidently detect" in flags, f"expected low-confidence flag for {text!r}"
        elif expected == "contradiction":
            assert any(
                phrase in flags
                for phrase in ("acoustic", "isn't a combination", "far from typical")
            ), f"expected a contradiction flag for {text!r}"
    return f"{len(AMBIGUOUS_CASES)}/{len(AMBIGUOUS_CASES)} known-ambiguous inputs correctly flagged"


def check_guardrail_fixes_acoustic_bug():
    raw = EDGE_CASE_PROFILES["String Acoustic Flag (truthy-string bug)"]
    assert bool(raw["likes_acoustic"]) is True  # confirms the bug would exist without the guardrail
    clean, corrections = validate_profile(raw)
    assert clean["likes_acoustic"] is False
    assert any("likes_acoustic" in c for c in corrections)
    return "likes_acoustic: 'false' (str) correctly resolves to False"


def check_catalog_integrity():
    songs = load_songs(str(SONGS_CSV))
    ids = [s["id"] for s in songs]
    assert len(songs) == 20
    assert len(set(ids)) == len(ids), "duplicate song ids in catalog"
    for s in songs:
        for field in ("energy", "valence", "danceability", "acousticness"):
            assert 0.0 <= s[field] <= 1.0, f"{field} out of range for song id {s['id']}"
    return f"{len(songs)}/20 songs, all ids unique, all numeric fields in range"


CHECKS = [
    ("Determinism", check_determinism),
    ("Score bounds", check_score_bounds),
    ("No crash on malformed input", check_no_crash_on_malformed_input),
    ("Confidence/contradiction flags fire on known-ambiguous inputs", check_confidence_flags_fire),
    ("Guardrail fixes likes_acoustic truthy-string bug", check_guardrail_fixes_acoustic_bug),
    ("Catalog integrity", check_catalog_integrity),
]


def run_all_checks():
    """Runs every check and returns a list of (name, passed, detail_or_error)."""
    results = []
    for name, fn in CHECKS:
        try:
            detail = fn()
            results.append((name, True, detail))
        except Exception as e:  # noqa: BLE001 - a check failing is data, not a crash
            results.append((name, False, str(e)))
    return results


def main() -> int:
    print("VibeFit Reliability Evaluation")
    print("=" * 32)
    results = run_all_checks()
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name} ({detail})")
    print("-" * 32)
    passed_count = sum(1 for _, passed, _ in results if passed)
    print(f"{passed_count}/{len(results)} checks passed")
    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
