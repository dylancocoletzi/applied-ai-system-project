from scripts.eval_harness import run_all_checks


def test_every_reliability_check_passes():
    results = run_all_checks()
    failures = [(name, detail) for name, passed, detail in results if not passed]
    assert failures == [], f"Reliability checks failed: {failures}"
