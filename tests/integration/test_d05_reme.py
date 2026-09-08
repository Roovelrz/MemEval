def test_d05_reme(reme_dimension_runner) -> None:
    assert reme_dimension_runner("D05")["prediction"]["status"] == "unsupported"


def test_d05_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D05")["status"] == "partial"
