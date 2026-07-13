import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

INT_FIELDS = ("id",)
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            for field in INT_FIELDS:
                row[field] = int(row[field])
            for field in FLOAT_FIELDS:
                row[field] = float(row[field])
            songs.append(row)
    return songs

GENRE_WEIGHT = 0.35
MOOD_WEIGHT = 0.25
ENERGY_WEIGHT = 0.25
ACOUSTIC_WEIGHT = 0.15

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    genre_match = song["genre"] == user_prefs.get("genre")
    mood_match = song["mood"] == user_prefs.get("mood")

    target_energy = user_prefs.get("energy", 0.5)
    energy_closeness = 1.0 - abs(target_energy - song["energy"])

    likes_acoustic = user_prefs.get("likes_acoustic", False)
    acoustic_fit = song["acousticness"] if likes_acoustic else 1.0 - song["acousticness"]

    score = (
        GENRE_WEIGHT * genre_match
        + MOOD_WEIGHT * mood_match
        + ENERGY_WEIGHT * energy_closeness
        + ACOUSTIC_WEIGHT * acoustic_fit
    )

    reasons = []
    if genre_match:
        reasons.append(f"matches your favorite genre ({song['genre']})")
    if mood_match:
        reasons.append(f"matches your favorite mood ({song['mood']})")
    if energy_closeness >= 0.85:
        reasons.append(f"energy ({song['energy']:.2f}) is close to your target ({target_energy:.2f})")
    if acoustic_fit >= 0.7:
        reasons.append(
            "acoustic sound fits your preference" if likes_acoustic
            else "energetic, non-acoustic sound fits your preference"
        )

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    # Judge: score every song in the catalog, in isolation, using score_song.
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # Rank: sort the whole catalog by score, descending, then take the top k.
    scored.sort(key=lambda entry: entry[1], reverse=True)

    recommendations = []
    for song, score, reasons in scored[:k]:
        explanation = " + ".join(reasons) if reasons else "closest overall match available"
        recommendations.append((song, score, explanation))

    return recommendations
