# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFit 1.0**

---

## 2. Intended Use  

Generates a ranked list of songs from a small, fixed catalog that best match a stated taste profile (genre, mood, energy, acoustic preference). It assumes the user's preferences are accurate, singular, and stable — one favorite genre, one favorite mood, one energy target — not a mix of moods or evolving tastes. This is a **classroom simulation**, built to demonstrate how content-based scoring works, not a production recommender for real listeners.

---

## 3. How the Model Works  

Each song is described by its genre, mood, energy level, and whether it sounds acoustic. Each user describes what they want the same way. The system compares a song to what the user wants and hands out partial credit on four things: matching genre (worth the most), matching mood (worth a bit less), being *close to* the desired energy level (not just "high" or "low" — close counts even if it's not exact), and having the right amount of acoustic-ness (worth the least). It adds up the credit into one score, does this for every song in the catalog, sorts highest to lowest, and hands back the top few — each with a plain-English reason pulled from whichever parts actually matched. The starter code was empty placeholders; we designed and built the entire scoring formula, the ranking step, and the CSV loading from scratch, and grew the catalog from 10 to 20 songs.

---

## 4. Data  

20 songs covering 17 genres and 16 moods (pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, folk, metal, classical, r&b, country, reggae, house, punk, blues). We added 10 songs to the original 10 specifically to diversify genre coverage and to break an accidental correlation where "low energy" and "acoustic" always went together. Gaps: no songs below 0.2 energy, 10 of the 20 genres have only one song each, and there's no lyrics, language, or popularity data at all.

---

## 5. Strengths  

Works best for users whose genre has several catalog entries and whose energy target sits in the well-covered 0.4–1.0 range (pop, rock, lofi fans, for example). It correctly captures that "close to the target energy" should score better than just "high energy" or "low energy." Recommendations matched intuition cleanly for clear-cut profiles — Chill Lofi and Deep Intense Rock both surfaced obviously-correct top picks with sensible reasons.

---

## 6. Limitations and Bias 

**Features not considered:** tempo, danceability, valence, lyrics, and other users' behavior (no collaborative filtering).

**Underrepresented genres/moods:** 10 of 20 songs are the only song in their genre. No songs exist below 0.2 energy, so very-calm listeners never get a close match.

**Overfitting to one preference:** `genre` is a high-weight, all-or-nothing match, so it acts as a hard gate — the system rarely recommends outside a user's stated genre (filter-bubble risk). A single `target_energy` also can't represent bimodal taste (e.g., likes both calm and intense music).

**Unintentional favoritism:** exact-string genre matching gives zero credit to close variants (e.g. "indie" vs. "indie pop"). Users whose target energy falls in the catalog's denser range (0.4–1.0) get better matches than those at the sparse low end.

**Weakness found during experiments:** setting the mood weight to zero flipped our "High-Energy Pop" profile's top pick from Sunrise City to Gym Hero, with no change to the songs themselves. This showed Sunrise City's #1 rank depended almost entirely on one component (mood), not a broad overall fit — a fragility the explanation text doesn't reveal. It means small, equally reasonable weight changes can overturn the "best" recommendation for the same user and catalog.

**Update (Project 4 extension):** the `likes_acoustic` truthy-string bug
described above is now actually **fixed** — but only in the new agent
pipeline (`src/guardrails.py`'s `validate_profile`), not in `recommender.py`
itself, which is intentionally left unmodified as the original base
project. See `README.md`'s "Reliability, Evaluation, and Guardrails"
section for the before/after.

---

## 7. Evaluation  

**Project 4 extension:** `python3 -m scripts.eval_harness` runs the real
Plan→Guardrail→Act→Check pipeline (no mocks) against free-text and
structured-profile inputs and checks determinism, score bounds,
malformed-input handling, that confidence/contradiction flags fire on
known-ambiguous inputs, the `likes_acoustic` guardrail fix, and catalog
integrity — 6/6 checks passing as of this writing. Full captured output is
in `README.md`'s "Reliability, Evaluation, and Guardrails" section.

**Profiles tested (original VibeFit 1.0 evaluation):** High-Energy Pop, Chill Lofi, Deep Intense Rock, Acoustic Folk Dreamer, Euphoric House Head, plus 5 adversarial edge cases (typo genre, out-of-range energy, truthy-string bug, unknown genre, contradictory prefs — see README).

**What we looked for:** whether each top pick's listed reasons actually match human intuition, and whether changing one trait (genre, mood, energy, acoustic) visibly moved the ranking.

**What surprised us — why "Gym Hero" keeps showing up:** Gym Hero (pop, but mood = *intense*, very high energy, non-acoustic) turned up as a strong runner-up for three unrelated profiles — Happy Pop, Deep Intense Rock, *and* Euphoric House. In plain terms: imagine picking a restaurant by scoring crust, toppings, price, and speed. A place with so-so toppings but amazing crust and lightning-fast delivery can still win even if price wasn't your main ask — because it racked up enough points elsewhere. Gym Hero is that restaurant: it doesn't nail "happy," but it's so loud and electric that it still earns enough energy + acoustic points to land near the top for almost anyone who wants high-energy music, regardless of their actual genre or mood.

**Profile comparisons:**
- *High-Energy Pop vs. Chill Lofi:* Pop lands on Sunrise City (loud, electric); Lofi lands on Library Rain (soft, acoustic) — makes sense, energy and acoustic pull in opposite directions.
- *Chill Lofi vs. Deep Intense Rock:* completely disjoint top picks (Library Rain vs. Storm Runner) — these two profiles want opposite moods and energy levels, so no song satisfies both.
- *Deep Intense Rock vs. Acoustic Folk Dreamer:* Rock favors loud/electric (Storm Runner); Folk favors acoustic/nostalgic (Wildflower Fields) — the acoustic-fit component flips direction between them.
- *Acoustic Folk Dreamer vs. Euphoric House Head:* same story in reverse — Folk wants acoustic, House wants electric/euphoric (Warehouse Pulse) — again fully different winners.
- *High-Energy Pop vs. Euphoric House Head:* different genres and moods, but both want high energy + non-acoustic, so Gym Hero shows up as a solid secondary pick in both — evidence that energy/acoustic alone can pull the same "generically loud" song across genre lines.

---

## 8. Future Work  

Add `valence` as a real scoring feature (it's the one numeric column that isn't redundant with energy). Show every component's contribution in the explanation, not just the ones above a threshold, so users can see the full picture. Add a diversity/exploration step so results aren't 100% deterministic for identical profiles. Support richer preferences — an energy *range* instead of one target, or more than one favorite genre — for users with mixed tastes.

---

## 9. Personal Reflection  

Building this made it clear that a "recommendation" is really just data plus comparison math — there's no hidden intelligence, just weighted arithmetic run over and over. The most surprising thing was how fragile the ranking turned out to be: zeroing out one weight (mood) was enough to flip the #1 pick entirely, which showed that a system's confident-looking "best answer" can hinge on one design choice a listener would never see. It changed how I think about apps like Spotify — a "personalized" top result might be one weight away from being a completely different song.

---

## 10. Reflection on AI Collaboration and System Design (Project 4 Extension)

### What are the limitations or biases in your system?

**Limitations:** the agent's understanding is genuinely shallow — it is
keyword matching over a hand-curated synonym dictionary, not real language
understanding. It cannot handle negation, sarcasm, or multi-clause
requests, and common-word collisions are possible (e.g. the genre "house"
versus an ordinary sentence about a house). Ambiguity is resolved with a
simple "first value mentioned wins" heuristic — flagged honestly to the
user via the confidence record, but not actually resolved.

**Biases:** the synonym dictionaries in `src/agent.py` are not uniform —
some canonical values have many recognized phrasings (`"lofi"` has five:
`lofi`, `lo-fi`, `lo fi`, `study music`, `chillhop`; `"melancholic"` has
five too) while others have exactly one (`"pop"`, `"rock"`, `"jazz"`,
`"folk"`, `"metal"`, `"classical"`, `"country"`, `"reggae"`, `"punk"`,
`"blues"` — ten of the seventeen genres). That means a request phrased in
an unanticipated way is systematically more likely to resolve correctly
for some genres/moods than others, purely because of which words we
happened to think to include — a bias baked into the dictionary's
coverage, not something the system can see or report about itself. None
of this is hidden: every limitation and bias here is either surfaced live
(via the per-field confidence status) or documented here and in
`README.md`.

### Could your AI be misused, and how would you prevent that?

The most concrete, real risk in this codebase (not a hypothetical one) is
**logging**: `src/agent.py`'s `log_event` writes the user's raw free-text
input verbatim into `logs/agent_activity.log` on every request, with no
redaction. If someone typed something personal or identifying into the
"describe your vibe" box (people do put unrelated things into free-text
fields), it would sit on disk in plain JSON Lines indefinitely — this is a
real privacy gap in the current implementation, not just a theoretical
one. Prevention we did *not* implement, but would before any real
deployment: cap log retention, strip/redact free text before persisting
it (keep only the parsed profile and confidence, not the original
sentence), and never commit the log directory (already gitignored here).
Beyond logging, misuse potential is otherwise low — this is a local,
single-user, read-only recommender over a fixed 20-song catalog with no
authentication, network exposure, or ability to take real-world action,
so there's no meaningful path to abusing it for anything beyond
"logged text I didn't mean to keep."

### What surprised you while testing your AI's reliability?

Two things. First, while validating the build plan, actually *running*
`python -m src.main` (the command this README already documented)
crashed with `ModuleNotFoundError` — a bug that had been sitting in the
codebase, undetected, because it only surfaces under one of the two
common ways to invoke the script. It wasn't found by reading the code; it
was found by executing it. Second, the self-check step turned out to be
more sensitive than expected: a single deliberately-contradictory request
("aggressive metal but keep it chill and acoustic") didn't trigger just
one warning but three at once (an acoustic/genre mismatch, an
energy/genre mismatch, *and* an ambiguous-mood flag) — each check had
been designed and tested in isolation, and seeing them all legitimately
fire together on one real input was a useful confirmation that the checks
compose correctly rather than stepping on each other.

### Describe your collaboration with AI during this project

The entire VibeFit Agent extension (the Plan→Guardrail→Act→Check pipeline
in `src/agent.py`/`src/guardrails.py`, the Streamlit UI, the eval harness,
this documentation) was built with Claude Code. Before writing any code,
I used it in **plan mode**: it read the existing codebase, proposed the
agent architecture, and — because it actually *ran* the project rather
than only reading it — surfaced a real, pre-existing bug before
implementation even began (see below). During implementation, each new
file was explained in plain language before being written, so I could
catch design issues (like the guardrail/critique overlap question) before
they became code, not after.

**One helpful AI suggestion:** while validating the build plan, Claude
Code actually executed `python -m src.main` — the command this README
already documented — and it crashed with `ModuleNotFoundError`, because
`main.py`'s sibling import only resolves when the file is run directly,
not when imported as a module. This was caught by *running* the code, not
by inspecting it, and it mattered directly: without the one-line fix, the
new eval harness and several new tests (which import `USER_PROFILES`/
`EDGE_CASE_PROFILES` straight from `src.main` rather than retyping them)
would have failed for the same reason, and a grader following the
original README's setup steps verbatim would have hit a crash before
reaching any of the new work.

**One flawed AI suggestion:** an early version of `tests/test_parser.py`
asserted that the free-text phrase *"non-acoustic"* should resolve to
`likes_acoustic: False`. It didn't — the parser (`parse_vibe_text`) does
plain keyword matching with no negation handling, so `"non-acoustic"`
correctly matches the substring `"acoustic"` and resolves to `True`. This
wasn't a bug in the actual system; it was a bad test that assumed a
capability (understanding "non-") the design was explicitly scoped not to
have. The failing test caught the mismatch immediately, and the fix was to
rewrite the test with an unambiguous phrase ("electric sound") rather than
add negation-handling scope creep to the parser. The lesson: an
AI-generated test passing a code review by "looking reasonable" is not the
same as it matching the system's actual, documented scope — it still has
to be checked against that scope explicitly.

### Future improvements

Replace hand-curated keyword lists with a lightweight embedding-based
similarity search over the catalog's genre/mood vocabulary — this would
generalize to phrasing we haven't anticipated, reduce the dictionary-
coverage bias noted above, and would be a natural place to introduce real
retrieval (RAG) in a later iteration. Add a simple negation heuristic
(checking for a "not"/"non-" token immediately before a matched phrase) to
fix the exact failure mode found above. Support more than one genre or
mood per request instead of collapsing ambiguity to "whichever was
mentioned first," to better reflect how people actually describe mixed
tastes. Redact or drop raw free text from the persisted log, keeping only
the parsed profile and confidence, to close the privacy gap noted above.
