# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This version is a content-based recommender: each song and each listener's stated taste profile (genre, mood, energy, acousticness) get turned into a single weighted score, the whole catalog gets ranked by that score, and the top few come back with a plain-English reason for each pick.

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
python -m src.main
```

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



