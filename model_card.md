# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

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

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
