import asyncio
import json
from types import SimpleNamespace

from app.schemas.campus_referral import (
    CampusReferralResponse,
)
from app.schemas.dtos import ChatRequest
from app.services.chat import ChatService


class FakeAgentHarness:
    def __init__(self):
        self.saved_assistant = None

    def run(self, user, request):
        referral = CampusReferralResponse(
            recordId=42,
            category="教务咨询",
            department="教务处",
            urgency="NORMAL",
            reason="用户咨询补考办理问题",
            suggestions=[
                "联系教务处了解补考流程",
            ],
            needsHumanFollowUp=False,
            knowledgeContext=(
                "教务处负责补考和学分问题。"
            ),
            status="PENDING",
        )

        return SimpleNamespace(
            session=SimpleNamespace(
                public_id="session-001",
            ),
            response_messages=[],
            campus_referral=referral,
            tool_plan=SimpleNamespace(),
            report_id=None,
        )

    def save_assistant_message(
        self,
        user,
        session,
        content,
    ):
        self.saved_assistant = content

    async def dispatch_tools(
        self,
        tool_plan,
    ):
        return []


class FakeAiClient:
    async def stream(self, messages):
        yield "请联系教务处了解补考流程。"


async def collect_events(service):
    return [
        event
        async for event in service.stream_chat(
            user=SimpleNamespace(id=1001),
            request=ChatRequest(
                message="补考应该找哪个部门？"
            ),
        )
    ]


def parse_sse_data(event: str) -> dict:
    data_line = next(
        line
        for line in event.splitlines()
        if line.startswith("data: ")
    )

    return json.loads(
        data_line.removeprefix("data: ")
    )


def test_chat_meta_exposes_campus_referral():
    service = object.__new__(ChatService)
    service.agent_harness = FakeAgentHarness()
    service.ai = FakeAiClient()

    events = asyncio.run(
        collect_events(service)
    )

    meta_payload = parse_sse_data(
        events[0]
    )

    assert meta_payload["type"] == "meta"
    assert (
        meta_payload["sessionId"]
        == "session-001"
    )
    assert (
        meta_payload["referralRecordId"]
        == 42
    )
    assert (
        meta_payload["referralDepartment"]
        == "教务处"
    )
    assert (
        meta_payload["referralUrgency"]
        == "NORMAL"
    )

class FakeNonReferralAgentHarness(FakeAgentHarness):
    def run(self, user, request):
        return SimpleNamespace(
            session=SimpleNamespace(
                public_id="session-chat-001",
            ),
            response_messages=[],
            campus_referral=None,
            tool_plan=SimpleNamespace(),
            report_id=None,
        )


def test_chat_meta_omits_referral_fields_for_normal_chat():
    service = object.__new__(ChatService)
    service.agent_harness = FakeNonReferralAgentHarness()
    service.ai = FakeAiClient()

    events = asyncio.run(
        collect_events(service)
    )

    meta_payload = parse_sse_data(
        events[0]
    )

    assert meta_payload["type"] == "meta"
    assert (
        meta_payload["sessionId"]
        == "session-chat-001"
    )
    assert "referralRecordId" not in meta_payload
    assert "referralDepartment" not in meta_payload
    assert "referralUrgency" not in meta_payload