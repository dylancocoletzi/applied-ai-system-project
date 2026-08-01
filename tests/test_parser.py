from src.agent import parse_vibe_text


def test_clear_request_matches_all_four_fields():
    result = parse_vibe_text("I want something upbeat pop for a workout, electric sound")
    profile = result["profile"]
    confidence = result["confidence"]

    assert profile["genre"] == "pop"
    assert confidence["genre"]["status"] == "matched"

    assert profile["energy"] == 0.85
    assert confidence["energy"]["status"] == "matched"

    assert profile["likes_acoustic"] is False
    assert confidence["likes_acoustic"]["status"] == "matched"


def test_indie_pop_does_not_double_count_as_plain_pop():
    result = parse_vibe_text("give me some indie pop")
    confidence = result["confidence"]["genre"]

    assert confidence["status"] == "matched"
    assert confidence["value"] == "indie pop"


def test_plain_pop_without_indie_matches_pop():
    result = parse_vibe_text("give me some pop music")
    confidence = result["confidence"]["genre"]

    assert confidence["status"] == "matched"
    assert confidence["value"] == "pop"


def test_empty_text_defaults_every_field():
    result = parse_vibe_text("")
    profile = result["profile"]
    confidence = result["confidence"]

    assert profile == {"genre": "", "mood": "", "energy": 0.5, "likes_acoustic": False}
    assert all(f["status"] == "defaulted" for f in confidence.values())


def test_gibberish_with_no_keywords_defaults_without_crashing():
    result = parse_vibe_text("asdkjfh qwoeiru zzz")
    assert all(f["status"] == "defaulted" for f in result["confidence"].values())


def test_conflicting_mood_words_are_flagged_ambiguous():
    result = parse_vibe_text("something aggressive but also chill")
    mood_confidence = result["confidence"]["mood"]

    assert mood_confidence["status"] == "ambiguous"
    assert set(mood_confidence["value"]) == {"aggressive", "chill"}


def test_acoustic_synonym_is_recognized():
    result = parse_vibe_text("something acoustic and unplugged for a rainy day")
    assert result["profile"]["likes_acoustic"] is True
    assert result["profile"]["energy"] == 0.3


def test_hip_hop_synonym_variants():
    for phrase in ("hip hop", "hip-hop", "rap"):
        result = parse_vibe_text(f"play some {phrase}")
        assert result["confidence"]["genre"]["value"] == "hip-hop", phrase
