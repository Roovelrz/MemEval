from memory_eval.adapters.memory.reme import safe_name
from memory_eval.systems import ReMeSystemAdapter, SystemCapabilities


def test_reme_system_declares_the_stage_29_contract() -> None:
    assert ReMeSystemAdapter.capabilities == SystemCapabilities(
        write_trace=True,
        retrieval=True,
        delete=True,
        user_isolation=True,
        latency_stats=True,
    )


def test_reme_workspace_names_are_bounded_and_stable() -> None:
    value = "dimension:" + "long-case-and-session-name:" * 8
    assert len(safe_name(value)) == 48
    assert safe_name(value) == safe_name(value)
    assert safe_name(value) != safe_name(value + "different")
