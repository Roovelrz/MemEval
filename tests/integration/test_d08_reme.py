def test_d08_reme(reme_dimension_runner) -> None:
    result = reme_dimension_runner("D08")
    assert result["metrics"]["privacy_pass"] == 1.0
    # 有效隐私通过率必须同时考虑允许召回，不能只看无泄露。
    assert "effective_privacy_pass" in result["metrics"]


def test_d08_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D08")["status"] == "ok"
