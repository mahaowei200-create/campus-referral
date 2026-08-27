import pytest
from pydantic import ValidationError
from app.schemas.campus_referral import (
    CampusDepartment,
    CampusReferralRequest,
    CampusReferralDecision,
    ReferralUrgency,
)

def test_referral_request_accepts_valid_message():  #校园转介请求能够接受一条合法消息
    request = CampusReferralRequest(message="我最近总是失眠")
    assert request.message == "我最近总是失眠"

def test_referral_request_accepts_session_id_alias():  #校园转介请求能够接受session_id别名
    request = CampusReferralRequest(
        sessionId="session-001",
        message="我不知道去哪里补办学生证",
    )

    assert request.session_id == "session-001"

def test_referral_request_rejects_blank_message(): #校园转介请求不能接受空白消息
    with pytest.raises(ValidationError):
        CampusReferralRequest(message="   ")

def test_campus_department_accepts_supported_value(): #校园部门能够接受支持的部门名称
    department = CampusDepartment("心理咨询中心")

    assert department == CampusDepartment.PSYCHOLOGICAL_CENTER


def test_referral_urgency_accepts_supported_value(): #转介紧急程度能够接受支持的紧急程度
    urgency = ReferralUrgency("URGENT")

    assert urgency == ReferralUrgency.URGENT

def test_referral_decision_accepts_valid_result(): #校园转介结果能够接受合法结果
    decision = CampusReferralDecision(
        category="心理支持",
        department="心理咨询中心",
        urgency="PRIORITY",
        reason="用户描述了持续失眠和学习压力",
        suggestions=[
            "联系学校心理咨询中心预约",
            "向辅导员说明近期状态",
        ],
        needsHumanFollowUp=True,
    )

    assert decision.category == "心理支持"
    assert decision.department == CampusDepartment.PSYCHOLOGICAL_CENTER
    assert decision.urgency == ReferralUrgency.PRIORITY
    assert decision.needs_human_follow_up is True
    assert len(decision.suggestions) == 2

def test_referral_decision_rejects_unknown_department(): #校园转介结果不能接受未知部门
    with pytest.raises(ValidationError):
        CampusReferralDecision(
            category="未知问题",
            department="宇宙事务管理局",
            urgency="NORMAL",
            reason="测试系统不支持的部门",
            suggestions=["联系管理员"],
            needsHumanFollowUp=False,
        )


def test_referral_decision_rejects_empty_suggestions(): #校园转介结果不能接受空建议
    with pytest.raises(ValidationError):
        CampusReferralDecision(
            category="心理支持",
            department="心理咨询中心",
            urgency="NORMAL",
            reason="用户描述了持续失眠和学习压力",
            suggestions=[],
            needsHumanFollowUp=False,
        )

def test_referral_decision_accepts_knowledge_context():
    decision = CampusReferralDecision(
        category="教务咨询",
        department="教务处",
        urgency="NORMAL",
        reason="用户咨询补考和学分问题",
        suggestions=[
            "联系教务处了解补考流程",
        ],
        needsHumanFollowUp=False,
        knowledgeContext=(
            "[资料1｜来源：campus-referral-resources.md]\n"
            "教务处主要处理补考、选课和学分问题。"
        ),
    )

    assert "教务处主要处理补考" in decision.knowledge_context