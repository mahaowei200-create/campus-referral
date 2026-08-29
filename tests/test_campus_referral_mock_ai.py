from types import SimpleNamespace

from app.schemas.dtos import AiMessage
from app.services.ai import AiClient


def build_mock_client() -> AiClient:
    settings = SimpleNamespace(
        ai_provider="mock",
    )
    return AiClient(settings)


def build_referral_messages(
    department: str,
    urgency: str,
) -> list[AiMessage]:
    return [
        AiMessage(
            role="system",
            content=(
                "你是MindBridge校园咨询分诊助手。\n"
                "请严格依据结构化分诊结果回复。\n\n"
                "转介记录ID：3\n"
                "问题类别：教务咨询\n"
                f"推荐部门：{department}\n"
                f"紧急程度：{urgency}\n"
                "分诊原因：用户咨询课程、考试或补考问题\n"
            ),
        ),
        AiMessage(
            role="user",
            content="我有一门课需要补考，应该找哪个部门办理？",
        ),
    ]


def test_mock_ai_returns_campus_referral_reply():
    client = build_mock_client()

    result = client.complete(
        build_referral_messages(
            department="教务处",
            urgency="NORMAL",
        )
    )

    assert "教务处" in result
    assert "补考" in result or "课程" in result
    assert "具体办理时间和流程" in result
    assert "最具体的困扰" not in result


def test_mock_ai_adds_safety_advice_for_urgent_referral():
    client = build_mock_client()

    result = client.complete(
        build_referral_messages(
            department="校园保卫处",
            urgency="URGENT",
        )
    )

    assert "校园保卫处" in result
    assert "人身安全" in result
    assert "紧急服务" in result