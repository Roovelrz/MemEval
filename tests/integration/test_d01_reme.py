def test_d01_reme(reme_dimension_runner) -> None:
    result = reme_dimension_runner("D01")
    # 逐字全量写入：事实全部保留（recall=1），但 non-memory 噪声也被写入（precision<1）。
    assert result["metrics"]["memory_recall"] == 1.0
    assert result["metrics"]["memory_precision"] < 1.0
    assert result["metrics"]["noise_event_count"] > 0


def test_d01_live_reme(live_reme_dimension_runner) -> None:
    assert live_reme_dimension_runner("D01")["status"] == "partial"
