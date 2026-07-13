"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def print_recommendations(user_prefs, recommendations) -> None:
    print(f"\nTop recommendations for profile: {user_prefs}\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} — {song['artist']}  (score: {score:.2f})")
        for reason in explanation.split(" + "):
            print(f"     - {reason}")
        print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}

    recommendations = recommend_songs(user_prefs, songs, k=5)
    print_recommendations(user_prefs, recommendations)


if __name__ == "__main__":
    main()
