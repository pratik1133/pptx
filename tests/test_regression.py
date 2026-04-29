from reportgen.qa.regression import discover_sample_bundles, run_regression_sample_set


def test_discover_sample_bundles_finds_multiple_inputs() -> None:
    bundles = discover_sample_bundles()

    assert len(bundles) >= 2


def test_regression_sample_set_runs_cleanly() -> None:
    result = run_regression_sample_set()

    assert result.ok
