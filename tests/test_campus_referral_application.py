from types import SimpleNamespace
from datetime import datetime
from app.schemas.campus_referral import (
    CampusReferralDecision,
    CampusReferralRequest,
    ReferralStatus,
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
        self.pending_records = []
        self.received_record_id = None
        self.received_status = None
        self.updated_record = None

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
    def list_pending(self):
        return self.pending_records

    def update_status(
        self,
        record_id,
        status,
    ):
        self.received_record_id = record_id
        self.received_status = status
        return self.updated_record
def make_record(
    record_id=42,
    status="PENDING",
):
    now = datetime(
        2026,
        8,
        28,
        10,
        30,
    )

    return SimpleNamespace(
        id=record_id,
        user_id=1001,
        session_public_id="session-001",
        message="我最近一直焦虑失眠",
        category="心理支持",
        department="心理咨询中心",
        urgency="PRIORITY",
        reason="用户描述了压力和睡眠问题",
        suggestions_json=(
            '["联系学校心理咨询中心预约"]'
        ),
        knowledge_context=(
            "心理咨询中心可以提供心理支持。"
        ),
        needs_human_follow_up=True,
        status=status,
        created_at=now,
        updated_at=now,
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

def test_application_service_lists_pending_referrals():
    repository = FakeCampusReferralRepository()
    repository.pending_records = [
        make_record(record_id=42),
        make_record(record_id=43),
    ]

    application_service = (
        CampusReferralApplicationService(
            triage_service=FakeTriageService(),
            repository=repository,
        )
    )

    responses = (
        application_service
        .list_pending_referrals()
    )

    assert len(responses) == 2
    assert responses[0].record_id == 42
    assert responses[1].record_id == 43
    assert responses[0].user_id == 1001
    assert responses[0].suggestions == [
        "联系学校心理咨询中心预约"
    ]


def test_application_service_updates_referral_status():
    repository = FakeCampusReferralRepository()
    repository.updated_record = make_record(
        record_id=42,
        status="PROCESSING",
    )

    application_service = (
        CampusReferralApplicationService(
            triage_service=FakeTriageService(),
            repository=repository,
        )
    )

    response = (
        application_service
        .update_referral_status(
            record_id=42,
            status=ReferralStatus.PROCESSING,
        )
    )

    assert repository.received_record_id == 42
    assert repository.received_status == "PROCESSING"
    assert response is not None
    assert response.record_id == 42
    assert response.status == (
        ReferralStatus.PROCESSING
    )

def test_application_service_returns_none_when_record_missing():
    repository = FakeCampusReferralRepository()
    repository.updated_record = None

    application_service = (
        CampusReferralApplicationService(
            triage_service=FakeTriageService(),
            repository=repository,
        )
    )

    response = (
        application_service
        .update_referral_status(
            record_id=999999,
            status=ReferralStatus.PROCESSING,
        )
    )

    assert repository.received_record_id == 999999
    assert repository.received_status == "PROCESSING"
    assert response is None