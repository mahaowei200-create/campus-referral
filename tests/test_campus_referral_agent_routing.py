from types import SimpleNamespace

from app.agents.langgraph_runtime import (
    LangGraphAgentRuntimeService,
)
from app.agents.runtime import (
    AgentContext,
    AgentRuntimeService,
)
from app.core.enums import (
    IntentType,
    RiskLevel,
)
from app.schemas.campus_referral import (
    CampusReferralResponse,
)
from app.schemas.dtos import AiMessage
from app.services.campus_referral import (
    has_campus_referral_signal,
)

def test_detects_academic_referral_request():
    assert has_campus_referral_signal(
        "补考应该找哪个部门办理？"
    ) is True


def test_detects_financial_aid_request():
    assert has_campus_referral_signal(
        "助学金应该怎么申请？"
    ) is True


def test_detects_immediate_campus_safety_request():
    assert has_campus_referral_signal(
        "有人威胁我，现在正在宿舍门口堵我"
    ) is True


def test_does_not_treat_emotional_distress_as_referral():
    assert has_campus_referral_signal(
        "最近考试压力很大，晚上一直睡不着"
    ) is False


def test_does_not_treat_general_chat_as_referral():
    assert has_campus_referral_signal(
        "请给我讲一下Python字典"
    ) is False

def test_supervisor_classifies_campus_referral_intent():
    runtime = object.__new__(
        AgentRuntimeService
    )

    intent = runtime._classify(
        "补考应该找哪个部门办理？",
        [],
    )

    assert intent == (
        IntentType.CAMPUS_REFERRAL
    )

def test_high_risk_takes_priority_over_campus_referral():
    runtime = object.__new__(
        AgentRuntimeService
    )

    intent = runtime._classify(
        (
            "我想申请助学金，"
            "但我现在已经不想活了"
        ),
        [],
    )

    assert intent == IntentType.RISK

class FakeCampusReferralApplication:
    def __init__(self):
        self.received_request = None
        self.received_user_id = None

    def create_referral(
        self,
        request,
        user_id,
    ):
        self.received_request = request
        self.received_user_id = user_id

        return CampusReferralResponse(
            recordId=42,
            category="教务咨询",
            department="教务处",
            urgency="NORMAL",
            reason="用户咨询补考办理问题",
            suggestions=[
                "联系教务处了解补考流程",
                "准备学号和课程信息",
            ],
            needsHumanFollowUp=False,
            knowledgeContext=(
                "教务处负责补考和学分问题。"
            ),
            status="PENDING",
        )

def test_campus_referral_agent_creates_record_and_response_plan():
    runtime = object.__new__(
        AgentRuntimeService
    )

    fake_application = (
        FakeCampusReferralApplication()
    )

    runtime.campus_referral_application = (
        fake_application
    )

    context = AgentContext(
        user=SimpleNamespace(
            id=1001,
            display_name="测试学生",
        ),
        session=SimpleNamespace(
            public_id="session-001",
        ),
        original_input=(
            "补考应该找哪个部门办理？"
        ),
        model_input=(
            "补考应该找哪个部门办理？"
        ),
        memory_loaded=True,
        intent_routed=True,
        intent=(
            IntentType.CAMPUS_REFERRAL
        ),
        model_history=[
            AiMessage(
                role="user",
                content=(
                    "补考应该找哪个部门办理？"
                ),
            )
        ],
    )

    ran = runtime.campus_referral_agent(
        step=3,
        context=context,
    )

    assert ran is True
    assert (
        fake_application.received_user_id
        == 1001
    )
    assert (
        fake_application
        .received_request
        .session_id
        == "session-001"
    )

    assert context.campus_referral is not None
    assert (
        context.campus_referral.record_id
        == 42
    )
    assert context.response_agent == (
        "CampusReferralAgent"
    )
    assert context.response_planned is True
    assert context.finished is True
    assert context.risk_level == RiskLevel.LOW

    system_prompt = (
        context.response_messages[0].content
    )

    assert "推荐部门：教务处" in system_prompt
    assert "紧急程度：NORMAL" in system_prompt
    assert "不得擅自更换部门" in system_prompt

    assert context.steps[-1].agent == (
        "CampusReferralAgent"
    )
    assert context.steps[-1].action == (
        "CREATE_CAMPUS_REFERRAL"
    )

def test_langgraph_controller_routes_to_campus_referral():
    runtime = object.__new__(
        LangGraphAgentRuntimeService
    )

    context = AgentContext(
        user=SimpleNamespace(
            id=1001,
        ),
        session=SimpleNamespace(
            public_id="session-001",
        ),
        original_input=(
            "补考应该找哪个部门办理？"
        ),
        model_input=(
            "补考应该找哪个部门办理？"
        ),
        memory_loaded=True,
        intent_routed=True,
        intent=(
            IntentType.CAMPUS_REFERRAL
        ),
    )

    next_node = runtime._select_next_agent(
        {
            "context": context,
        }
    )

    assert next_node == "campus_referral"

    context.response_planned = True

    next_node_after_response = (
        runtime._select_next_agent(
            {
                "context": context,
            }
        )
    )

    assert next_node_after_response == "end"