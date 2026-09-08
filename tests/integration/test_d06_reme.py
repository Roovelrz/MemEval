def test_d06_reme(reme_dimension_runner) -> None:
    assert "answer_accuracy" in reme_dimension_runner("D06")["unsupported_metrics"]


def test_d06_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D06")["status"] == "partial"
