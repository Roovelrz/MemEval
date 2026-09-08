def test_d01_reme(reme_dimension_runner) -> None:
    assert reme_dimension_runner("D01")["metrics"]["write_event_recall"] == 1.0


def test_d01_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D01")["status"] == "partial"
