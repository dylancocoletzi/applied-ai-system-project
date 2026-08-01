"""
VibeFit Agent: a rule-based, multi-step pipeline that lets a user describe a
"vibe" in free text (e.g. "something upbeat for a workout") instead of
picking structured fields by hand.

Pipeline (see diagrams/architecture.mmd):
  Plan (parse_vibe_text)   -> turn free text into a structured profile + a
                               per-field confidence record (matched /
                               defaulted / ambiguous, with which words fired).
  Guardrail (guardrails.py) -> type-coerce and sanity-clamp that profile.
  Act (recommender.py)      -> score and rank the catalog, unmodified.
  Check (critique)          -> flag low confidence or catalog-implausible
                               combinations, without changing the result.

No AI/ML model or external API is used anywhere in this pipeline — every
step is deterministic, reproducible Python, by design (see model_card.md).
"""
import re
from typing import Dict, List

# --- Catalog vocabulary -----------------------------------------------------
# Canonical value -> phrases that should resolve to it. Order within a list
# doesn't matter; longer / multi-word phrases are preferred automatically by
# the matcher below, so "indie pop" doesn't get double-counted as a hit for
# both "indie pop" and the separate "pop" genre.

GENRE_SYNONYMS: Dict[str, List[str]] = {
    "pop": ["pop"],
    "lofi": ["lofi", "lo-fi", "lo fi", "study music", "chillhop"],
    "rock": ["rock"],
    "ambient": ["ambient"],
    "jazz": ["jazz"],
    "synthwave": ["synthwave", "synth wave", "retrowave"],
    "indie pop": ["indie pop", "indie"],
    "hip-hop": ["hip hop", "hip-hop", "rap"],
    "folk": ["folk"],
    "metal": ["metal"],
    "classical": ["classical"],
    "r&b": ["r&b", "rnb", "r and b", "r n b"],
    "country": ["country"],
    "reggae": ["reggae"],
    "house": ["house music", "house"],
    "punk": ["punk"],
    "blues": ["blues"],
}

MOOD_SYNONYMS: Dict[str, List[str]] = {
    "happy": ["happy", "joyful", "cheerful"],
    "chill": ["chill", "chilled", "laid back", "laidback"],
    "intense": ["intense"],
    "moody": ["moody"],
    "focused": ["focused", "focus"],
    "nostalgic": ["nostalgic", "nostalgia"],
    "aggressive": ["aggressive", "angry", "rage", "furious"],
    "dreamy": ["dreamy", "dreamlike"],
    "romantic": ["romantic", "romance", "love song"],
    "wistful": ["wistful", "bittersweet"],
    "uplifting": ["uplifting", "inspiring", "motivational", "motivating"],
    "euphoric": ["euphoric", "ecstatic", "blissful"],
    "anxious": ["anxious", "nervous", "on edge"],
    "melancholic": ["melancholic", "melancholy", "sad", "down", "heartbroken"],
    "relaxed": ["relaxed", "mellow", "easygoing", "easy going"],
    "energetic": ["energetic", "energizing"],
}

ENERGY_CUES: Dict[str, List[str]] = {
    "high": [
        "workout", "gym", "hype", "pump up", "pumped", "cardio", "rave",
        "party", "running", "run", "upbeat", "high energy", "high-energy",
    ],
    "low": [
        "chill out", "relax", "sleep", "study", "rainy day", "calm",
        "wind down", "unwind", "slow down", "mellow out", "low energy",
        "low-energy",
    ],
}

ACOUSTIC_CUES: Dict[str, List[str]] = {
    "true": ["acoustic", "unplugged", "stripped down", "organic sound"],
    "false": ["electronic", "synth heavy", "synthesizer", "edm", "digital sound", "electric"],
}

ENERGY_VALUES = {"high": 0.85, "low": 0.3}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s&-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _find_spans(normalized_text: str, synonym_map: Dict[str, List[str]]):
    spans = []  # (start, end, canonical, phrase)
    for canonical, phrases in synonym_map.items():
        for phrase in phrases:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            for m in re.finditer(pattern, normalized_text):
                spans.append((m.start(), m.end(), canonical, phrase))
    return spans


def _match_keywords(normalized_text: str, synonym_map: Dict[str, List[str]]) -> Dict:
    """
    Matches every phrase in synonym_map against normalized_text and resolves
    overlaps by preferring longer spans (so multi-word phrases win over a
    shorter phrase that happens to be a substring of them).

    Returns {"status": "matched"|"defaulted"|"ambiguous", "value": ...,
    "matched_phrases": [...]}. "value" is a single canonical string when
    matched, a list of canonicals (in the order first mentioned) when
    ambiguous, and None when defaulted.
    """
    spans = _find_spans(normalized_text, synonym_map)
    spans.sort(key=lambda s: (s[1] - s[0]), reverse=True)

    def overlaps(a, b):
        return a[0] < b[1] and b[0] < a[1]

    kept = []
    for span in spans:
        if not any(overlaps(span, k) for k in kept):
            kept.append(span)

    kept.sort(key=lambda s: s[0])  # restore left-to-right order for readability

    canonicals_in_order = []
    for span in kept:
        canonical = span[2]
        if canonical not in canonicals_in_order:
            canonicals_in_order.append(canonical)
    matched_phrases = [span[3] for span in kept]

    if len(canonicals_in_order) == 0:
        return {"status": "defaulted", "value": None, "matched_phrases": []}
    if len(canonicals_in_order) == 1:
        return {"status": "matched", "value": canonicals_in_order[0], "matched_phrases": matched_phrases}
    return {"status": "ambiguous", "value": canonicals_in_order, "matched_phrases": matched_phrases}


def _first_value(match: Dict):
    """Collapses a possibly-ambiguous match down to the single value used to
    build the profile (the first one mentioned in the text)."""
    value = match["value"]
    if isinstance(value, list):
        return value[0]
    return value


def parse_vibe_text(text: str) -> Dict:
    """
    The Plan step. Turns free text into a structured profile plus a
    per-field confidence record.

    This is intentionally limited to literal keyword matching — it cannot
    handle negation ("not too sad"), sarcasm, or multi-clause requests
    beyond simple word co-occurrence. That scoping is documented in
    model_card.md, not hidden.
    """
    normalized = _normalize(text or "")

    genre_match = _match_keywords(normalized, GENRE_SYNONYMS)
    mood_match = _match_keywords(normalized, MOOD_SYNONYMS)
    energy_match = _match_keywords(normalized, ENERGY_CUES)
    acoustic_match = _match_keywords(normalized, ACOUSTIC_CUES)

    genre_value = _first_value(genre_match) or ""
    mood_value = _first_value(mood_match) or ""
    energy_choice = _first_value(energy_match)
    acoustic_choice = _first_value(acoustic_match)

    profile = {
        "genre": genre_value,
        "mood": mood_value,
        "energy": ENERGY_VALUES.get(energy_choice, 0.5),
        "likes_acoustic": acoustic_choice == "true",
    }
    confidence = {
        "genre": genre_match,
        "mood": mood_match,
        "energy": energy_match,
        "likes_acoustic": acoustic_match,
    }
    return {"profile": profile, "confidence": confidence}
