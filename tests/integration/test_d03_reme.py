def test_d03_reme(reme_dimension_runner) -> None:
    assert "answer_accuracy" in reme_dimension_runner("D03")["unsupported_metrics"]


def test_d03_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D03")["status"] == "partial"
