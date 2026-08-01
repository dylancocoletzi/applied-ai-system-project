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
import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from src.guardrails import validate_profile
    from src.recommender import load_songs, recommend_songs
except ImportError:
    from guardrails import validate_profile
    from recommender import load_songs, recommend_songs

SONGS_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOGS_DIR / "agent_activity.log"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("vibefit_agent")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _handler = logging.FileHandler(LOG_FILE)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.propagate = False


def log_event(record: Dict) -> None:
    """Appends one JSON-Lines entry describing a single run_agent() call."""
    _logger.info(json.dumps(record))


def read_recent_activity(limit: int = 10) -> List[Dict]:
    """Returns up to the last `limit` logged interactions (oldest first),
    for the UI's Recent Activity panel. Never raises if the log is missing
    or a line is malformed — logging is a safety net, not a hard dependency."""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE) as f:
        lines = f.readlines()[-limit:]
    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


_songs_cache = None


def _get_songs() -> List[Dict]:
    """Loads data/songs.csv once and caches it for the life of the process."""
    global _songs_cache
    if _songs_cache is None:
        _songs_cache = load_songs(str(SONGS_CSV_PATH))
    return _songs_cache


_catalog_aggregates_cache = None


def _get_catalog_aggregates() -> Tuple[set, Dict[str, List[float]], Dict[str, List[float]]]:
    """
    Computes, once, the catalog facts the Check step needs to judge
    plausibility: every (genre, mood) pair that actually occurs, and each
    genre's acousticness/energy values. Derived straight from the real
    catalog via the unmodified load_songs(), never hardcoded.
    """
    global _catalog_aggregates_cache
    if _catalog_aggregates_cache is None:
        songs = _get_songs()
        genre_mood_pairs = {(s["genre"], s["mood"]) for s in songs}
        genre_acousticness = defaultdict(list)
        genre_energy = defaultdict(list)
        for s in songs:
            genre_acousticness[s["genre"]].append(s["acousticness"])
            genre_energy[s["genre"]].append(s["energy"])
        _catalog_aggregates_cache = (genre_mood_pairs, genre_acousticness, genre_energy)
    return _catalog_aggregates_cache

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


def critique(profile: Dict, confidence: Dict, recommendations: List) -> List[str]:
    """
    The Check step. Looks at the agent's own parse and results and flags
    anything that looks low-confidence or implausible against the real
    catalog — it never mutates the profile or the results, only surfaces
    warnings so the user sees an honest picture instead of false certainty.
    """
    warnings: List[str] = []
    genre_mood_pairs, genre_acousticness, genre_energy = _get_catalog_aggregates()

    genre_status = confidence["genre"]["status"]
    mood_status = confidence["mood"]["status"]
    acoustic_status = confidence["likes_acoustic"]["status"]
    acoustic_value = confidence["likes_acoustic"]["value"] if acoustic_status == "matched" else None
    genre = profile["genre"]
    mood = profile["mood"]

    if genre_status == "matched" and mood_status == "matched":
        if (genre, mood) not in genre_mood_pairs:
            warnings.append(
                f"'{genre}' + '{mood}' isn't a combination seen in this catalog — "
                "results may be a compromise between the two."
            )

    if genre_status == "matched" and genre in genre_acousticness:
        mean_acoustic = sum(genre_acousticness[genre]) / len(genre_acousticness[genre])
        if acoustic_value == "true" and mean_acoustic < 0.2:
            warnings.append(
                f"You asked for an acoustic sound, but '{genre}' songs in this catalog "
                f"average only {mean_acoustic:.2f} acousticness."
            )
        if acoustic_value == "false" and mean_acoustic > 0.8:
            warnings.append(
                f"You asked for a non-acoustic sound, but '{genre}' songs in this catalog "
                f"average {mean_acoustic:.2f} acousticness (quite acoustic)."
            )

    if genre_status == "matched" and genre in genre_energy:
        mean_energy = sum(genre_energy[genre]) / len(genre_energy[genre])
        if abs(profile["energy"] - mean_energy) > 0.4:
            warnings.append(
                f"Target energy ({profile['energy']:.2f}) is far from typical '{genre}' "
                f"energy in this catalog ({mean_energy:.2f})."
            )

    defaulted_fields = [field for field, c in confidence.items() if c["status"] == "defaulted"]
    ambiguous_fields = [field for field, c in confidence.items() if c["status"] == "ambiguous"]

    if len(defaulted_fields) >= 2:
        warnings.append(
            f"Couldn't confidently detect {', '.join(defaulted_fields)} from your text — "
            "results may be broad."
        )

    for field in ambiguous_fields:
        phrases = confidence[field]["matched_phrases"]
        warnings.append(
            f"Your text mentioned conflicting signals for {field} ({', '.join(phrases)}) — "
            "used the one mentioned first."
        )

    if recommendations:
        top_song, top_score, top_explanation = recommendations[0]
        if top_score < 0.5 or not top_explanation.strip():
            warnings.append(
                f"Even the top match ('{top_song['title']}', score {top_score:.2f}) isn't "
                "a strong fit — try adding more specific words."
            )

    return warnings


def run_agent(text: str, k: int = 5) -> Dict:
    """
    Runs the full Plan -> Guardrail -> Act -> Check pipeline for one piece
    of free text and returns everything the caller (Streamlit, the eval
    harness, tests) needs to show or check: the parsed profile, its
    confidence record, any guardrail corrections, critique warnings, and
    the top-k recommendations.
    """
    plan = parse_vibe_text(text)
    clean_profile, corrections = validate_profile(plan["profile"])

    songs = _get_songs()
    recommendations = recommend_songs(clean_profile, songs, k=k)
    warnings = critique(clean_profile, plan["confidence"], recommendations)

    top_result = None
    if recommendations:
        top_song, top_score, _ = recommendations[0]
        top_result = {"title": top_song["title"], "score": top_score}

    log_event({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_text": text,
        "parsed_profile": clean_profile,
        "confidence": plan["confidence"],
        "guardrail_corrections": corrections,
        "critique_flags": warnings,
        "top_result": top_result,
    })

    return {
        "input_text": text,
        "profile": clean_profile,
        "confidence": plan["confidence"],
        "guardrail_corrections": corrections,
        "critique_flags": warnings,
        "recommendations": recommendations,
    }
