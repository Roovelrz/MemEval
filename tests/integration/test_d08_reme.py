def test_d08_reme(reme_dimension_runner) -> None:
    assert reme_dimension_runner("D08")["metrics"]["privacy_pass"] == 1.0


def test_d08_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D08")["status"] == "ok"
