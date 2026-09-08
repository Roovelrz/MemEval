def test_d07_reme(reme_dimension_runner) -> None:
    assert "answer_accuracy" in reme_dimension_runner("D07")["unsupported_metrics"]


def test_d07_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D07")["status"] == "partial"
