# 🎵 Music Recommender Simulation

## Portfolio Note

[GitHub repo](https://github.com/dylancocoletzi/applied-ai-system-project.git)

This project is a reminder to me that "responsible AI" is a design decision,
not an afterthought — the choice to keep the VibeFit Agent fully
deterministic and API-free wasn't a limitation I ran into, it was a
trade-off I made on purpose so the system would stay reproducible and
gradeable without a hidden dependency on someone else's model or an API
key. Splitting the guardrail (which fixes bad data) from the self-check
step (which judges whether a request even makes sense) taught me to
separate "is this input well-formed" from "is this output trustworthy" —
two questions I used to conflate. And catching a real, previously-hidden
bug simply by running the code instead of reading it reinforced something
I want to carry into every project: testing isn't a formality tacked onto
the end, it's how you find out what you actually believe about your own
system versus what's actually true.

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This version is a content-based recommender: each song and each listener's stated taste profile (genre, mood, energy, acousticness) get turned into a single weighted score, the whole catalog gets ranked by that score, and the top few come back with a plain-English reason for each pick.

---

# Extended System: VibeFit Agent (Project 4)

## Original Project

This extends **VibeFit 1.0**, the content-based music recommender described
in full below ("How The System Works"). In its original form, VibeFit 1.0
compares each of 20 songs in `data/songs.csv` against a user's *hand-typed*
genre/mood/energy/acoustic preferences using a fixed weighted formula, ranks
the catalog by that score, and returns the top few with a plain-English
explanation. It contains **no AI/ML model of any kind** — it's deterministic
comparison arithmetic over structured fields the user must already know how
to fill in (`src/main.py`'s `USER_PROFILES`/`EDGE_CASE_PROFILES`).
`src/main.py` and `src/recommender.py` are unmodified by this extension.

## Title and Summary

**VibeFit Agent** lets a user describe what they want in plain English
(e.g. *"something upbeat for a workout"*) instead of hand-picking
structured fields. A new multi-step pipeline parses that free text, cleans
it, runs it through the original scorer unmodified, and — critically —
checks its own interpretation and flags anything that looks
low-confidence or implausible before showing results. It matters because
it's the difference between a recommender that only works if you already
know its exact input vocabulary, and one that meets a user where they are
while staying honest about how well it actually understood the request.

## Architecture Overview

Full diagram source: [`diagrams/architecture.mmd`](diagrams/architecture.mmd).

The system has three parts. The **base project** (`src/main.py`) still
feeds its hand-typed structured profiles straight into the recommender's
scorer, unchanged. Layered on top, the **extended agent pipeline** takes
free text through the Streamlit UI and runs it through four stages: **Plan**
(`parse_vibe_text`) turns the text into a structured profile plus a
per-field confidence label; **Guardrail** (`validate_profile`) type-checks
and clamps that profile; **Act** hands it to the same original, untouched
scorer to rank the catalog; and **Check** (`critique`) compares the parse
and the results against the real catalog to flag anything implausible,
before the result is logged and shown. The third part is a **verification
layer** that sits alongside the request path rather than inside it:
`pytest`/`scripts/eval_harness.py` exercise every pipeline stage with known
and adversarial inputs, and the human user is the final checkpoint — they
see the interpretation table, guardrail notes, and self-check warnings in
the UI and decide whether to trust a result or refine their request.

## Setup Instructions

Same dependencies as above (no new ones — `streamlit` was already listed
but unused):

```bash
pip install -r requirements.txt

# Base project CLI (unchanged)
python3 src/main.py

# Extended agent UI
streamlit run src/app.py

# Reliability evaluation harness
python3 -m scripts.eval_harness

# All tests (base + extension)
pytest
```

## Sample Interactions

Real output from `run_agent(...)`, captured verbatim (not fabricated):

```
=== "something upbeat pop for a workout" ===

Interpreted profile: {'genre': 'pop', 'mood': '', 'energy': 0.85, 'likes_acoustic': False}
  genre: matched (pop)
  mood: defaulted
  energy: matched (upbeat, workout)
  likes_acoustic: defaulted
Self-check notes:
  - Couldn't confidently detect mood, likes_acoustic from your text — results may be broad.

Recommendations:
1. Gym Hero — Max Pulse  (score: 0.72)
     - matches your favorite genre (pop)
     - energy (0.93) is close to your target (0.85)
     - energetic, non-acoustic sound fits your preference
2. Sunrise City — Neon Echo  (score: 0.72)
     - matches your favorite genre (pop)
     - energy (0.82) is close to your target (0.85)
     - energetic, non-acoustic sound fits your preference
3. Concrete Kingdom — MC Ledger  (score: 0.39)
     - energy (0.85) is close to your target (0.85)
     - energetic, non-acoustic sound fits your preference

=== "sad acoustic songs for a rainy day" ===

Interpreted profile: {'genre': '', 'mood': 'melancholic', 'energy': 0.3, 'likes_acoustic': True}
  genre: defaulted
  mood: matched (sad)
  energy: matched (rainy day)
  likes_acoustic: matched (acoustic)

Recommendations:
1. Riverbed Blues — Otis Marrow  (score: 0.55)
     - matches your favorite mood (melancholic)
     - energy (0.45) is close to your target (0.30)
2. Spacewalk Thoughts — Orbit Bloom  (score: 0.38)
     - energy (0.28) is close to your target (0.30)
     - acoustic sound fits your preference
3. Quiet Constellations — Elian Voss  (score: 0.37)
     - energy (0.22) is close to your target (0.30)
     - acoustic sound fits your preference

=== "aggressive metal but keep it chill and acoustic" ===

Interpreted profile: {'genre': 'metal', 'mood': 'aggressive', 'energy': 0.5, 'likes_acoustic': True}
  genre: matched (metal)
  mood: ambiguous (aggressive, chill)
  energy: defaulted
  likes_acoustic: matched (acoustic)
Self-check notes:
  - You asked for an acoustic sound, but 'metal' songs in this catalog average only 0.03 acousticness.
  - Target energy (0.50) is far from typical 'metal' energy in this catalog (0.97).
  - Your text mentioned conflicting signals for mood (aggressive, chill) — used the one mentioned first.

Recommendations:
1. Iron Verdict — Grey Anvil  (score: 0.74)
     - matches your favorite genre (metal)
     - matches your favorite mood (aggressive)
2. Coffee Shop Stories — Slow Stereo  (score: 0.35)
     - energy (0.37) is close to your target (0.50)
     - acoustic sound fits your preference
3. Focus Flow — LoRoom  (score: 0.34)
     - energy (0.40) is close to your target (0.50)
     - acoustic sound fits your preference
```

The same pipeline is exposed interactively in `streamlit run src/app.py`,
which shows the interpretation table, guardrail/self-check notes, and
results for whatever you type, plus a "Recent Activity" sidebar sourced
from `logs/agent_activity.log`.

## Design Decisions

- **No LLM or external API anywhere in this pipeline** — a deliberate
  choice, not a limitation we ran into. It keeps the whole system
  deterministic and reproducible (same input always gives the same
  output — verified by the eval harness below) and removes any dependency
  on an API key or network access to run or grade this project. The
  trade-off is real: a real language model would understand phrasing far
  more flexibly than keyword matching does (see Limitations).
- **Guardrails and self-check are two separate mechanisms, not one
  reused twice.** `validate_profile` is deliberately dumb — it only fixes
  malformed *data* (wrong types, out-of-range numbers) and has no idea
  what the song catalog even contains. `critique` is the opposite — it
  never changes a value, only judges *plausibility* against the real
  catalog. Keeping them separate means a caller can trust the guardrail
  output unconditionally while still getting an honest, separate opinion
  about whether the request made sense.
- **`src/main.py`/`src/recommender.py` were left completely untouched.**
  The one exception is a single import-statement fix (see Testing
  Summary) required so other modules could import from it — no scoring
  logic changed. Keeping the original file byte-for-byte otherwise
  preserves it as a clean "before" artifact.
- **Streamlit over a custom web frontend** — it was already an unused
  dependency in `requirements.txt`, and it let the UI stay a thin,
  readable wrapper around `run_agent()` rather than its own project.

## Testing Summary

- `pytest` — 27/27 tests passing across the original 2 base-project tests
  plus new tests for the guardrail, the parser, the agent pipeline, and
  the eval harness.
- **What worked:** the Plan→Guardrail→Act→Check pipeline is fully
  deterministic — the eval harness confirms identical input always
  produces identical output — and the self-check step correctly flags
  every deliberately-contradictory test case (e.g. "metal" + "acoustic"),
  without ever altering the underlying recommendation.
- **What didn't work initially:** while validating the build plan,
  running `python -m src.main` (the command this README originally
  documented) crashed with `ModuleNotFoundError` — `main.py`'s import only
  resolved when run directly, not when imported as a module. This also
  blocked the new eval harness and tests from importing
  `USER_PROFILES`/`EDGE_CASE_PROFILES` from `src.main`. Fixed with a
  one-line dual-import pattern; both `python3 src/main.py` and
  `python -m src.main` now work, and no scoring logic changed. Separately,
  an early parser test assumed the phrase "non-acoustic" would resolve to
  `False` — it didn't, because the parser has no negation handling by
  design. The test was wrong, not the parser; fixed by rewriting the test.
- **What we learned:** see the Reliability section below for the guardrail
  before/after and the full evaluation harness output.

## Reliability, Evaluation, and Guardrails

Two **distinct** mechanisms, deliberately kept separate (see Design
Decisions above):

| | Guardrails (`src/guardrails.py`) | Self-check (`src/agent.py`'s `critique`) |
|---|---|---|
| Input | raw, untyped profile dict | profile + confidence + catalog + scored results |
| Output | corrected dict + correction log | advisory warning strings only |
| On a problem | **silently coerces** to a safe value | **never mutates** — only flags |
| Catalog-aware? | No — pure type/range hygiene | Yes — judges plausibility against real song data |

**Guardrail before/after** (real output) — this is the fix for the
`likes_acoustic` bug this project's own model card previously just listed
as a known limitation:

```
Raw input: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': 'false'}
bool(raw['likes_acoustic']) in plain Python: True   <- the bug: a non-empty string is always truthy

After validate_profile():
Clean profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': False}
Corrections:
 - likes_acoustic: coerced string 'false' to False (not the truthy non-empty string it would otherwise be)
```

**Evaluation harness** (`python3 -m scripts.eval_harness`) runs the real
pipeline — not mocks — against free-text and structured-profile inputs and
checks determinism, score bounds, malformed-input handling, that
confidence/contradiction flags actually fire on known-ambiguous inputs, the
guardrail fix above, and catalog integrity. Real captured output:

```
VibeFit Reliability Evaluation
================================
[PASS] Determinism (5/5 cases)
[PASS] Score bounds (50 scores checked across 10 profiles)
[PASS] No crash on malformed input (9/9 inputs handled without raising)
[PASS] Confidence/contradiction flags fire on known-ambiguous inputs (2/2 known-ambiguous inputs correctly flagged)
[PASS] Guardrail fixes likes_acoustic truthy-string bug (likes_acoustic: 'false' (str) correctly resolves to False)
[PASS] Catalog integrity (20/20 songs, all ids unique, all numeric fields in range)
--------------------------------
6/6 checks passed
```

**Human evaluation** — beyond the automated checks above, these are real
outputs I manually judged against a stated criterion (not just "did it
run"), including one deliberately chosen to fail so this isn't just a list
of passes:

| Test Input | Evaluation Criteria | Result |
|---|---|---|
| "something upbeat pop for a workout, electric sound" | Clear, unambiguous request resolves confidently with zero critique flags | ✅ Pass |
| "aggressive metal but keep it chill and acoustic" | Contradictory request (acoustic + metal, conflicting moods) is flagged rather than silently producing a confident-looking result | ✅ Pass — 3 distinct flags fired (acoustic/genre, energy/genre, ambiguous mood) |
| "play me something" | Near-empty request triggers a low-confidence warning instead of pretending certainty | ✅ Pass |
| "sad acoustic songs for a rainy day" | Natural phrasing, not exact catalog words ("sad"→melancholic, "rainy day"→low energy), still resolves correctly | ✅ Pass |
| "something upbeat pop for a workout, non-acoustic" | Negated request ("non-acoustic") should resolve `likes_acoustic: False` | ❌ **Fail** — resolves to `True`; the parser has no negation handling (documented limitation, not a bug we missed). The self-check step partially compensates by warning that pop songs average low acousticness, but for the wrong underlying reason — it doesn't know the user's real intent was the opposite. |

## Limitations of the New Agent

- **Keyword matching, not language understanding.** `parse_vibe_text` only
  reacts to literal words present — it cannot handle negation (e.g.
  "not too sad" still matches "sad"), sarcasm, or complex multi-clause
  requests.
- **Finite, hand-curated synonym dictionary.** Phrasing outside the lists
  in `src/agent.py` simply defaults, with that reflected honestly in the
  confidence status — it doesn't silently guess.
- **Common-word collisions are possible** — e.g. "house" (the genre) can't
  be distinguished from ordinary uses of the word "house" in a sentence.
- **Ambiguity resolution is a simple heuristic** (first value mentioned
  wins), not a real disambiguation strategy — flagged honestly to the user
  rather than hidden, but not resolved.

## Reflection

This project's graded reflection on AI collaboration, system design, and
limitations lives in [`model_card.md`](model_card.md) (see "Reflection on
AI Collaboration and System Design"), alongside the base project's own
reflection. Briefly: building the self-check step made it obvious how much
of "trustworthy AI" is really about being honest when a request doesn't fit
the data well, rather than about getting every answer right.

---

## How The System Works

**Real-world context:** Spotify/YouTube blend *collaborative filtering* (recommend based on similar users' behavior) with *content-based filtering* (recommend based on item attributes). Collaborative filtering needs lots of user history and struggles with new users/songs; content-based doesn't. This project implements the **content-based** half only — simpler and cold-start-friendly, but unable to break out of a user's stated tastes the way "similar users liked this" can.

**Song features used:** `genre`, `mood`, `energy`, `acousticness`. (We skip `tempo_bpm` and `danceability` in scoring — they correlate strongly with `energy`, r ≈ 0.86–0.96, so including them would just triple-count the same signal.)

**UserProfile stores:** `favorite_genre`, `favorite_mood`, `target_energy` (0–1), `likes_acoustic` (bool).

**Scoring rule (`score_song`)** — one weighted score per song, in isolation:
- `0.35 ×` genre match (exact)
- `0.25 ×` mood match (exact)
- `0.25 ×` energy closeness: `1 - abs(target_energy - song.energy)` — rewards being *close to* the target, not just high/low
- `0.15 ×` acoustic fit: `acousticness` if `likes_acoustic` else `1 - acousticness`

Genre is weighted highest as the most stable taste signal; mood/energy are situational refinements; acousticness is a niche preference.

**Ranking rule (`recommend_songs`):** scoring judges one song at a time; ranking needs the whole catalog to decide order. We sort all songs by score, descending, and return the top `k`.

### Finalized Algorithm Recipe

```
score = 0.35 · genre_match
      + 0.25 · mood_match
      + 0.25 · (1 - abs(target_energy - song.energy))
      + 0.15 · (acousticness if likes_acoustic else 1 - acousticness)
```

**Data flow:** `user_prefs` (dict) + `load_songs()` → **loop** every song through `score_song` in isolation (Scoring Rule) → **sort** the scored list descending and slice top `k` (Ranking Rule) → `(song, score, explanation)` results.

**Expected biases:**
- Fixed weights apply to every user the same way — the recipe can't learn that one person actually weighs mood over genre.
- Because there's no collaborative signal, recommendations can't break out of a user's stated `genre`/`mood`, which risks a filter-bubble effect (never surfacing something outside declared taste).
- Genres/moods with more songs in the catalog have a better chance of landing an exact match; thinner genres are underrepresented in top-k results purely from smaller supply, not lower relevance.

---

## Sample Recommendation Output

Output of `python3 src/main.py` for the starter profile (`genre=pop, mood=happy, energy=0.8, likes_acoustic=False`):

```
Top recommendations for profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8, 'likes_acoustic': False}

1. Sunrise City — Neon Echo  (score: 0.97)
     - matches your favorite genre (pop)
     - matches your favorite mood (happy)
     - energy (0.82) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference

2. Gym Hero — Max Pulse  (score: 0.71)
     - matches your favorite genre (pop)
     - energy (0.93) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference

3. Rooftop Lights — Indigo Parade  (score: 0.59)
     - matches your favorite mood (happy)
     - energy (0.76) is close to your target (0.80)

4. Concrete Kingdom — MC Ledger  (score: 0.38)
     - energy (0.85) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference

5. Broken Compass — Nine Hollow  (score: 0.36)
     - energy (0.88) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference
```

---

## Edge Case Output

```
=== Typo Genre (case mismatch) ===

Top recommendations for profile: {'genre': 'Rock', 'mood': 'Happy', 'energy': 0.7, 'likes_acoustic': False}

1. Night Drive Loop — Neon Echo  (score: 0.35)
     - energy (0.75) is close to your target (0.70)
     - energetic, non-acoustic sound fits your preference

2. Concrete Kingdom — MC Ledger  (score: 0.35)
     - energy (0.85) is close to your target (0.70)
     - energetic, non-acoustic sound fits your preference

3. Sunrise City — Neon Echo  (score: 0.34)
     - energy (0.82) is close to your target (0.70)
     - energetic, non-acoustic sound fits your preference

=== Overshoot Energy (target > 1.0) ===

Top recommendations for profile: {'genre': 'pop', 'mood': 'happy', 'energy': 1.4, 'likes_acoustic': False}

1. Sunrise City — Neon Echo  (score: 0.83)
     - matches your favorite genre (pop)
     - matches your favorite mood (happy)
     - energetic, non-acoustic sound fits your preference

2. Gym Hero — Max Pulse  (score: 0.62)
     - matches your favorite genre (pop)
     - energetic, non-acoustic sound fits your preference

3. Rooftop Lights — Indigo Parade  (score: 0.44)
     - matches your favorite mood (happy)

=== String Acoustic Flag (truthy-string bug) ===

Top recommendations for profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': 'false'}

1. Library Rain — Paper Lanterns  (score: 0.97)
     - matches your favorite genre (lofi)
     - matches your favorite mood (chill)
     - energy (0.35) is close to your target (0.40)
     - acoustic sound fits your preference

2. Midnight Coding — LoRoom  (score: 0.95)
     - matches your favorite genre (lofi)
     - matches your favorite mood (chill)
     - energy (0.42) is close to your target (0.40)
     - acoustic sound fits your preference

3. Focus Flow — LoRoom  (score: 0.72)
     - matches your favorite genre (lofi)
     - energy (0.40) is close to your target (0.40)
     - acoustic sound fits your preference

=== Unknown Genre (not in catalog) ===

Top recommendations for profile: {'genre': 'k-pop', 'mood': 'euphoric', 'energy': 0.8, 'likes_acoustic': False}

1. Warehouse Pulse — Kilo Static  (score: 0.53)
     - matches your favorite mood (euphoric)
     - energetic, non-acoustic sound fits your preference

2. Concrete Kingdom — MC Ledger  (score: 0.38)
     - energy (0.85) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference

3. Sunrise City — Neon Echo  (score: 0.37)
     - energy (0.82) is close to your target (0.80)
     - energetic, non-acoustic sound fits your preference

=== Contradiction (no real match exists) ===

Top recommendations for profile: {'genre': 'metal', 'mood': 'chill', 'energy': 0.1, 'likes_acoustic': True}

1. Spacewalk Thoughts — Orbit Bloom  (score: 0.59)
     - matches your favorite mood (chill)
     - acoustic sound fits your preference

2. Library Rain — Paper Lanterns  (score: 0.57)
     - matches your favorite mood (chill)
     - acoustic sound fits your preference

3. Midnight Coding — LoRoom  (score: 0.53)
     - matches your favorite mood (chill)
     - acoustic sound fits your preference
```

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python3 src/main.py
```

   (`python -m src.main` also works — `main.py`'s import was fixed to
   support both invocation styles while building the extension below.)

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

- **Doubled the energy weight (0.25→0.50) and halved the genre weight (0.35→0.175):** for "Deep Intense Rock," the bottom three results reordered purely from amplified energy differences — Iron Verdict dropped from #3 to #5 despite having the best acoustic fit, because its energy match was slightly worse than Broken Compass's. For "High-Energy Pop," Rooftop Lights overtook Gym Hero — Gym Hero's edge (a genre match) got weaker while Rooftop Lights' edge (a closer energy match) got stronger.
- **Set the mood weight to 0** to see how much it mattered: for "Deep Intense Rock" the ranking didn't change (both top songs happened to match the target mood, so both lost equally). For "High-Energy Pop," the #1 pick flipped from Sunrise City to Gym Hero — only Sunrise City had a mood match, so removing mood's weight erased its entire advantage.
- **Ran 5 real user profiles + 5 adversarial edge-case profiles** (see Sample Recommendation Output and Edge Case Output above) — different profiles reliably pulled toward opposite ends of the energy/acoustic scale (e.g. Chill Lofi → soft/acoustic picks, Deep Intense Rock → loud/electric picks), confirming the scoring recipe is actually sensitive to the inputs it's supposed to be sensitive to.

---

## Limitations and Risks

- Small catalog (20 songs), and 10 of the 20 genres have only one song each — a niche taste has no backup match if its one song is a poor fit.
- No songs below 0.2 energy, so very-calm listeners can never get a close energy match.
- `genre` is a high-weight, all-or-nothing match, so the system rarely recommends outside a user's stated genre — a real filter-bubble risk.
- Doesn't understand lyrics, language, or popularity — and has no collaborative signal (no notion of "other users"), so it can't recommend anything outside what a user explicitly states.

Full depth on this — including exact numbers and an experiment that exposed a real fragility — is in the model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this made it clear that a "recommendation" isn't magic — it's just data (song attributes) and a taste profile compared through fixed arithmetic, then sorted. Every prediction can be traced back to exactly which weighted components matched, which is both the system's strength (fully explainable) and its ceiling (it can never suggest anything the math didn't already point to).

Bias shows up in quiet ways: a high, all-or-nothing weight on genre means the system rarely recommends outside a user's stated genre, and thin catalog coverage (many genres have just one song) means a niche taste gets one shot at a good match instead of several. Our weight-tuning experiment made this concrete — zeroing out the mood weight was enough to flip the "best" recommendation for one profile entirely, showing how much a single design choice, invisible to the end user, can decide what gets called "personalized."



