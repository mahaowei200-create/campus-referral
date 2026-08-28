from types import SimpleNamespace
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.campus_referral import (
    get_campus_referral_application_service,
    router,
)
from app.core.security import current_user
from app.schemas.campus_referral import (
    CampusReferralResponse,
)


class FakeCampusReferralApplicationService:
    def __init__(self):
        self.received_request = None
        self.received_user_id = None

    def create_referral(
        self,
        request,
        user_id,
    ) -> CampusReferralResponse:
        self.received_request = request
        self.received_user_id = user_id

        return CampusReferralResponse(
            recordId=42,
            category="心理支持",
            department="心理咨询中心",
            urgency="PRIORITY",
            reason="用户描述了压力和睡眠问题",
            suggestions=[
                "联系学校心理咨询中心预约",
            ],
            needsHumanFollowUp=True,
            knowledgeContext=(
                "[资料1｜来源："
                "campus-referral-resources.md]\n"
                "心理咨询中心可以提供心理支持。"
            ),
            status="PENDING",
        )


def test_triage_endpoint_returns_referral_response():
    fake_application_service = (
        FakeCampusReferralApplicationService()
    )

    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(
            id=1001,
            roles=["ROLE_USER"],
        )
    )

    app.dependency_overrides[
        get_campus_referral_application_service
    ] = lambda: fake_application_service

    client = TestClient(app)

    response = client.post(
        "/api/campus-referrals/triage",
        json={
            "sessionId": "session-001",
            "message": "我最近一直焦虑失眠",
        },
    )

    payload = response.json()

    assert response.status_code == 200

    assert fake_application_service.received_user_id == (
        1001
    )

    assert (
        fake_application_service
        .received_request
        .session_id
        == "session-001"
    )

    assert payload["recordId"] == 42
    assert payload["category"] == "心理支持"
    assert payload["department"] == "心理咨询中心"
    assert payload["urgency"] == "PRIORITY"
    assert payload["needsHumanFollowUp"] is True
    assert payload["status"] == "PENDING"
    assert "心理咨询中心可以提供心理支持" in (
        payload["knowledgeContext"]
    )

def test_main_app_registers_campus_referral_router():
    app = create_app()

    registered_paths = {
        route.path
        for route in app.routes
    }

    assert (
        "/api/campus-referrals/triage"
        in registered_paths
    )
def build_test_client(
    fake_application_service,
    roles=None,
):
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[current_user] = (
        lambda: SimpleNamespace(
            id=1001,
            roles=roles or ["ROLE_USER"],
        )
    )

    app.dependency_overrides[
        get_campus_referral_application_service
    ] = lambda: fake_application_service

    return TestClient(app)
def test_triage_endpoint_rejects_blank_message():
    fake_application_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_test_client(
        fake_application_service
    )

    response = client.post(
        "/api/campus-referrals/triage",
        json={
            "sessionId": "session-001",
            "message": "   ",
        },
    )

    assert response.status_code == 422
    assert (
        fake_application_service.received_request
        is None
    )
def test_triage_endpoint_rejects_too_long_message():
    fake_application_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_test_client(
        fake_application_service
    )

    response = client.post(
        "/api/campus-referrals/triage",
        json={
            "sessionId": "session-001",
            "message": "压" * 501,
        },
    )

    assert response.status_code == 422
    assert (
        fake_application_service.received_request
        is None
    )
def test_triage_endpoint_rejects_admin_user():
    fake_application_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_test_client(
        fake_application_service,
        roles=[
            "ROLE_USER",
            "ROLE_ADMIN",
        ],
    )

    response = client.post(
        "/api/campus-referrals/triage",
        json={
            "sessionId": "session-admin",
            "message": "我想咨询补考问题",
        },
    )

    assert response.status_code == 403

    assert response.json