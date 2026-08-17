import json

from app.core.enums import RiskLevel
from app.services.assessment import PsychologicalAssessmentService
from app.services.memory import RedisShortTermMemoryStore
from app.services.privacy import PrivacySanitizer


class ExplodingAi:
    def complete(self, messages):
        raise AssertionError("high risk hard guard should not call the model")


def test_privacy_sanitizer_masks_common_identifiers():
    text = PrivacySanitizer().sanitize(
        "电话 13800138000 邮箱 a@example.com 身份证 110101199003071234"
    )

    assert "13800138000" not in text
    assert "a@example.com" not in text
    assert "110101199003071234" not in text
    assert text.count("[已脱敏]") == 3


def test_redis_memory_serializes_sanitized_content():
    store = RedisShortTermMemoryStore.__new__(RedisShortTermMemoryStore)
    store.privacy = PrivacySanitizer()

    payload = json.loads(
        store._serialize("user", "电话 13800138000 邮箱 a@example.com")
    )

    assert "13800138000" not in payload["content"]
    assert "a@example.com" not in payload["content"]
    assert payload["content"].count("[已脱敏]") == 2


def test_high_risk_signal_uses_hard_guard_before_model():
    result = PsychologicalAssessmentService(ExplodingAi()).assess(
        "我不想活了，想结束生命"
    )

    assert result.risk == RiskLevel.HIGH
    assert result.confidence >= 0.9