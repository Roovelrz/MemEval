def test_d05_reme(reme_dimension_runner) -> None:
    # D05 已改为纯检索召回，不进入 Answer/Judge，不产出 answer prediction。
    assert reme_dimension_runner("D05")["prediction"] is None


def test_d05_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D05")["status"] == "ok"
