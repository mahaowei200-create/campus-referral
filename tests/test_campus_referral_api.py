from types import SimpleNamespace
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime
from app.api.campus_referral import (
    admin_router,
    get_campus_referral_application_service,
    router,
)
from app.core.security import current_user
from app.schemas.campus_referral import (
    CampusReferralAdminResponse,
    CampusReferralResponse,
    ReferralStatus,
)
from app.services.campus_referral_repository import (
    InvalidReferralStatusTransition,
)
def make_admin_response(record_id=42,status="PENDING",):
    now = datetime(2026,8,28,10,30,)

    return CampusReferralAdminResponse(
        recordId=record_id,
        userId=1001,
        sessionId="session-001",
        message="我最近一直焦虑失眠",
        category="心理支持",
        department="心理咨询中心",
        urgency="PRIORITY",
        reason="用户描述了压力和睡眠问题",
        suggestions=[
            "联系学校心理咨询中心预约",
        ],
        needsHumanFollowUp=True,
        knowledgeContext=(
            "心理咨询中心可以提供心理支持。"
        ),
        status=status,
        createdAt=now,
        updatedAt=now,
    )
class FakeCampusReferralApplicationService:
    def __init__(self):
        self.received_request = None
        self.received_user_id = None
        self.pending_responses = [make_admin_response()]
        self.updated_response = make_admin_response(
            status="PROCESSING"
        )
        self.received_record_id = None
        self.received_status = None
        self.update_error = None

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
    def list_pending_referrals(self):
        return self.pending_responses

    def update_referral_status(
        self,
        record_id,
        status,
    ):
        self.received_record_id = record_id
        self.received_status = status

        if self.update_error is not None:
            raise self.update_error

        return self.updated_response

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
    assert (
    "/api/admin/campus-referrals/pending"
    in registered_paths
)

    assert (
        (
            "/api/admin/campus-referrals/"
            "{record_id}/status"
        )
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
def build_admin_test_client(
        fake_application_service,
        roles=None,
    ):
        app = FastAPI()
        app.include_router(admin_router)

        app.dependency_overrides[current_user] = (
            lambda: SimpleNamespace(
                id=9001,
                roles=roles or [
                    "ROLE_ADMIN",
                ],
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

def test_admin_lists_pending_referrals():
    fake_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_admin_test_client(
        fake_service
    )

    response = client.get(
        "/api/admin/campus-referrals/pending"
    )

    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["recordId"] == 42
    assert payload[0]["userId"] == 1001
    assert payload[0]["status"] == "PENDING"
    assert payload[0]["needsHumanFollowUp"] is True

def test_admin_updates_referral_status():
    fake_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_admin_test_client(
        fake_service
    )

    response = client.patch(
        (
            "/api/admin/campus-referrals/"
            "42/status"
        ),
        json={
            "status": "PROCESSING",
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert fake_service.received_record_id == 42
    assert fake_service.received_status == (
        ReferralStatus.PROCESSING
    )
    assert payload["recordId"] == 42
    assert payload["status"] == "PROCESSING"

def test_admin_update_returns_404_when_record_missing():
    fake_service = (
        FakeCampusReferralApplicationService()
    )
    fake_service.updated_response = None

    client = build_admin_test_client(
        fake_service
    )

    response = client.patch(
        (
            "/api/admin/campus-referrals/"
            "999999/status"
        ),
        json={
            "status": "PROCESSING",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "校园转介记录不存在。"
    )

def test_admin_update_rejects_unknown_status():
    fake_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_admin_test_client(
        fake_service
    )

    response = client.patch(
        (
            "/api/admin/campus-referrals/"
            "42/status"
        ),
        json={
            "status": "UNKNOWN",
        },
    )

    assert response.status_code == 422
    assert fake_service.received_record_id is None

def test_student_cannot_list_pending_referrals():
    fake_service = (
        FakeCampusReferralApplicationService()
    )

    client = build_admin_test_client(
        fake_service,
        roles=["ROLE_USER"],
    )

    response = client.get(
        "/api/admin/campus-referrals/pending"
    )

    assert response.status_code == 403

def test_admin_update_rejects_backward_transition():
    fake_service = (
        FakeCampusReferralApplicationService()
    )

    fake_service.update_error = (
        InvalidReferralStatusTransition(
            "Cannot change referral status "
            "from RESOLVED to PENDING"
        )
    )

    client = build_admin_test_client(
        fake_service
    )

    response = client.patch(
        (
            "/api/admin/campus-referrals/"
            "42/status"
        ),
        json={
            "status": "PENDING",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Cannot change referral status "
        "from RESOLVED to PENDING"
    )

    assert fake_service.received_record_id == 42
    assert fake_service.received_status == (
        ReferralStatus.PENDING
    )