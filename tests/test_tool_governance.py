from types import SimpleNamespace

from app.core.enums import RiskLevel, ToolJobKind
from app.services.tool_governance import ToolPolicyRegistry


def report(risk: RiskLevel):
    return SimpleNamespace(risk_level=risk.value)


def test_high_risk_alert_is_allowed_only_for_high_risk():
    allowed, _, _ = ToolPolicyRegistry.authorize(
        ToolJobKind.ALERT_SEND.value,
        report(RiskLevel.HIGH),
    )
    blocked, reason, _ = ToolPolicyRegistry.authorize(
        ToolJobKind.ALERT_SEND.value,
        report(RiskLevel.LOW),
    )

    assert allowed
    assert not blocked
    assert "不允许" in reason


def test_medium_case_create_is_allowed_but_low_is_blocked():
    allowed, _, _ = ToolPolicyRegistry.authorize(
        ToolJobKind.CASE_CREATE.value,
        report(RiskLevel.MEDIUM),
    )
    blocked, _, _ = ToolPolicyRegistry.authorize(
        ToolJobKind.CASE_CREATE.value,
        report(RiskLevel.LOW),
    )

    assert allowed
    assert not blocked


def test_unknown_tool_is_blocked():
    allowed, reason, policy = ToolPolicyRegistry.authorize(
        "DELETE_EVERYTHING",
        report(RiskLevel.HIGH),
    )

    assert not allowed
    assert policy is None
    assert "未知工具" in reason