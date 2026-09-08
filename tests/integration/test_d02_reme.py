def test_d02_reme(reme_dimension_runner) -> None:
    assert reme_dimension_runner("D02")["metrics"]["retrieval_evaluated"] is True


def test_d02_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D02")["status"] == "ok"
