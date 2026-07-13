"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


USER_PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False},
    "Acoustic Folk Dreamer": {"genre": "folk", "mood": "nostalgic", "energy": 0.5, "likes_acoustic": True},
    "Euphoric House Head": {"genre": "house", "mood": "euphoric", "energy": 0.8, "likes_acoustic": False},
}

# Adversarial / edge-case profiles: not real users, designed to probe how
# score_song behaves under invalid or contradictory input.
EDGE_CASE_PROFILES = {
    "Typo Genre (case mismatch)": {"genre": "Rock", "mood": "Happy", "energy": 0.7, "likes_acoustic": False},
    "Overshoot Energy (target > 1.0)": {"genre": "pop", "mood": "happy", "energy": 1.4, "likes_acoustic": False},
    "String Acoustic Flag (truthy-string bug)": {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": "false"},
    "Unknown Genre (not in catalog)": {"genre": "k-pop", "mood": "euphoric", "energy": 0.8, "likes_acoustic": False},
    "Contradiction (no real match exists)": {"genre": "metal", "mood": "chill", "energy": 0.1, "likes_acoustic": True},
}


def print_recommendations(user_prefs, recommendations) -> None:
    print(f"\nTop recommendations for profile: {user_prefs}\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} — {song['artist']}  (score: {score:.2f})")
        for reason in explanation.split(" + "):
            print(f"     - {reason}")
        print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    for name, user_prefs in USER_PROFILES.items():
        print(f"=== {name} ===")
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(user_prefs, recommendations)

    print("\n############################\n# Edge Case / Adversarial Profiles\n############################")
    for name, user_prefs in EDGE_CASE_PROFILES.items():
        print(f"=== {name} ===")
        recommendations = recommend_songs(user_prefs, songs, k=3)
        print_recommendations(user_prefs, recommendations)


if __name__ == "__main__":
    main()
