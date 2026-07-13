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

---

## 7. Evaluation  

**Profiles tested:** High-Energy Pop, Chill Lofi, Deep Intense Rock, Acoustic Folk Dreamer, Euphoric House Head, plus 5 adversarial edge cases (typo genre, out-of-range energy, truthy-string bug, unknown genre, contradictory prefs — see README).

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
