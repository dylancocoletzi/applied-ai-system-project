from src.agent import run_agent


def test_run_agent_is_deterministic():
    first = run_agent("something upbeat pop for a workout", k=3)
    second = run_agent("something upbeat pop for a workout", k=3)

    first_ids = [song["id"] for song, _, _ in first["recommendations"]]
    second_ids = [song["id"] for song, _, _ in second["recommendations"]]
    assert first_ids == second_ids

    first_scores = [score for _, score, _ in first["recommendations"]]
    second_scores = [score for _, score, _ in second["recommendations"]]
    assert first_scores == second_scores


def test_scores_are_within_valid_bounds():
    result = run_agent("aggressive metal but keep it chill and acoustic", k=10)
    for _, score, _ in result["recommendations"]:
        assert 0.0 <= score <= 1.0


def test_no_crash_on_empty_or_gibberish_text():
    for text in ("", "   ", "asdkjfh qwoeiru zzz"):
        result = run_agent(text, k=3)
        assert len(result["recommendations"]) == 3
        assert result["profile"]["energy"] == 0.5


def test_contradiction_flag_fires_for_metal_acoustic_request():
    result = run_agent("aggressive metal but keep it chill and acoustic", k=5)
    flags = " ".join(result["critique_flags"])
    assert "acoustic" in flags
    assert "metal" in flags


def test_ambiguous_mood_is_flagged():
    result = run_agent("aggressive metal but keep it chill and acoustic", k=5)
    flags = " ".join(result["critique_flags"])
    assert "conflicting signals for mood" in flags


def test_low_confidence_is_flagged_when_little_is_detected():
    result = run_agent("play me something", k=3)
    flags = " ".join(result["critique_flags"])
    assert "Couldn't confidently detect" in flags


def test_clean_request_produces_no_critique_flags():
    result = run_agent("something upbeat pop for a workout, electric sound", k=3)
    assert result["critique_flags"] == []


def test_guardrail_corrections_are_surfaced_through_run_agent():
    # A well-formed free-text request shouldn't need any guardrail correction.
    result = run_agent("happy pop songs", k=3)
    assert result["guardrail_corrections"] == []
