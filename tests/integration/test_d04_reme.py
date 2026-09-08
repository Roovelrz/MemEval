def test_d04_reme(reme_dimension_runner) -> None:
    assert reme_dimension_runner("D04")["prediction"]["status"] == "unsupported"


def test_d04_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D04")["status"] == "unsupported"
