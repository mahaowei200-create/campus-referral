from types import SimpleNamespace

from app.schemas.campus_referral import (
    CampusReferralDecision,
    CampusReferralRequest,
)
from app.services.campus_referral_application import (
    CampusReferralApplicationService,
)


class FakeTriageService:
    def __init__(self):
        self.received_message = None

    def triage(self,message: str) -> CampusReferralDecision:
        self.received_message = message

        return CampusReferralDecision(
            category="心理支持",
            department="心理咨询中心",
            urgency="PRIORITY",
            reason="用户描述了压力和睡眠问题",
            suggestions=[
                "联系学校心理咨询中心预约",
            ],
            needsHumanFollowUp=True,
            knowledgeContext=(
                "[资料1｜来源：campus-referral-resources.md]\n"
                "心理咨询中心可以提供心理支持。"
            ),
        )


class FakeCampusReferralRepository:
    def __init__(self):
        self.received_message = None
        self.received_decision = None
        self.received_user_id = None
        self.received_session_public_id = None

    def create(
        self,
        message,
        decision,
        user_id=None,
        session_public_id=None,
    ):
        self.received_message = message
        self.received_decision = decision
        self.received_user_id = user_id
        self.received_session_public_id = (
            session_public_id
        )

        return SimpleNamespace(
            id=42,
            status="PENDING",
        )


def test_application_service_triages_and_persists_record():
    triage_service = FakeTriageService()
    repository = FakeCampusReferralRepository()

    application_service = (
        CampusReferralApplicationService(
            triage_service=triage_service,
            repository=repository,
        )
    )

    request = CampusReferralRequest(
        sessionId="session-001",
        message="我最近一直焦虑失眠",
    )

    response = application_service.create_referral(
        request=request,
        user_id=1001,
    )

    assert triage_service.received_message == (
        "我最近一直焦虑失眠"
    )

    assert repository.received_message == (
        "我最近一直焦虑失眠"
    )

    assert repository.received_user_id == 1001

    assert repository.received_session_public_id == (
        "session-001"
    )

    assert response.record_id == 42
    assert response.status == "PENDING"
    assert response.category == "心理支持"
    assert response.department.value == "心理咨询中心"
    assert response.urgency.value == "PRIORITY"
    assert response.needs_human_follow_up is True
    assert "心理咨询中心可以提供心理支持" in (
        response.knowledge_context
    )