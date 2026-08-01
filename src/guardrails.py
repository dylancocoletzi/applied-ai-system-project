"""
Guardrail layer: pure data-hygiene validation for a raw user-profile dict.

This module has zero awareness of the song catalog and never judges whether a
value is a *good* one, only whether it is well-formed. It exists to guarantee
that whatever reaches recommender.py is a safe, typed profile, regardless of
what a caller (a keyword parser, a hand-typed dict, a UI form) handed it.

Required by tests/test_guardrails.py and src/agent.py.
"""
from typing import Any, Dict, List, Tuple

DEFAULT_PROFILE = {
    "genre": "",
    "mood": "",
    "energy": 0.5,
    "likes_acoustic": False,
}

TRUE_STRINGS = {"true", "yes", "1"}
FALSE_STRINGS = {"false", "no", "0", "none", ""}


def _coerce_likes_acoustic(raw: Any, corrections: List[str]) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        normalized = raw.strip().lower()
        if normalized in TRUE_STRINGS:
            if normalized != raw:
                corrections.append(f"likes_acoustic: normalized {raw!r} to True")
            return True
        if normalized in FALSE_STRINGS:
            corrections.append(f"likes_acoustic: coerced string {raw!r} to False (not the truthy non-empty string it would otherwise be)")
            return False
        corrections.append(f"likes_acoustic: unrecognized value {raw!r}, defaulted to False")
        return False
    corrections.append(f"likes_acoustic: unrecognized type {type(raw).__name__}, defaulted to False")
    return False


def _coerce_energy(raw: Any, corrections: List[str]) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        corrections.append(f"energy: could not parse {raw!r} as a number, defaulted to 0.5")
        return 0.5

    clamped = min(1.0, max(0.0, value))
    if clamped != value:
        corrections.append(f"energy: clamped {value} to {clamped} (must be within [0.0, 1.0])")
    return clamped


def _coerce_string_field(field: str, raw: Any, corrections: List[str]) -> str:
    if raw is None:
        return ""
    text = str(raw).strip().lower()
    if text != raw:
        corrections.append(f"{field}: normalized {raw!r} to {text!r}")
    return text


def validate_profile(raw_profile: Dict) -> Tuple[Dict, List[str]]:
    """
    Coerces a raw, untyped profile dict into a safe, typed one.

    Returns (clean_profile, corrections) where corrections is a list of
    human-readable strings describing every change that was made (empty if
    the input was already well-formed). Never raises on missing keys, wrong
    types, or out-of-range values.
    """
    corrections: List[str] = []
    profile = dict(raw_profile) if isinstance(raw_profile, dict) else {}

    if not isinstance(raw_profile, dict):
        corrections.append(f"profile: expected a dict, got {type(raw_profile).__name__}, using all defaults")

    for field in ("genre", "mood", "energy", "likes_acoustic"):
        if field not in profile:
            corrections.append(f"{field}: missing, defaulted to {DEFAULT_PROFILE[field]!r}")

    clean = {
        "genre": _coerce_string_field("genre", profile.get("genre"), corrections),
        "mood": _coerce_string_field("mood", profile.get("mood"), corrections),
        "energy": _coerce_energy(profile.get("energy", 0.5), corrections),
        "likes_acoustic": _coerce_likes_acoustic(profile.get("likes_acoustic", False), corrections),
    }

    return clean, corrections
