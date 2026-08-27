from app.schemas.campus_referral import CampusDepartment, ReferralUrgency
from app.services.campus_referral import CampusReferralService


def test_triage_routes_academic_affairs_question():# 教务咨询
    service = CampusReferralService()

    decision = service.triage("我的成绩有问题，想申请补考")

    assert decision.category == "教务咨询"
    assert decision.department == CampusDepartment.ACADEMIC_AFFAIRS
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.needs_human_follow_up is False

def test_triage_routes_psychological_support_question():# 心理咨询
    service = CampusReferralService()

    decision = service.triage("我最近一直失眠，学习压力很大")

    assert decision.category == "心理支持"
    assert decision.department == CampusDepartment.PSYCHOLOGICAL_CENTER
    assert decision.urgency == ReferralUrgency.PRIORITY
    assert decision.needs_human_follow_up is True

def test_triage_routes_immediate_danger_to_urgent_support():
    service = CampusReferralService()

    decision = service.triage("我不想活了，已经准备伤害自己")

    assert decision.category == "校园安全与心理危机"
    assert decision.department == CampusDepartment.CAMPUS_SECURITY
    assert decision.urgency == ReferralUrgency.URGENT
    assert decision.needs_human_follow_up is True

def test_triage_uses_other_department_for_unknown_question():
    service = CampusReferralService()

    decision = service.triage("食堂饭卡丢了，不知道应该找谁")

    assert decision.category == "其他校园咨询"
    assert decision.department == CampusDepartment.OTHER
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.needs_human_follow_up is False

def test_triage_routes_career_question():
    service = CampusReferralService()

    decision = service.triage("我准备找实习，不知道简历应该怎么修改")

    assert decision.category == "就业咨询"
    assert decision.department == CampusDepartment.CAREER_CENTER
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.needs_human_follow_up is False


def test_triage_routes_financial_aid_question():
    service = CampusReferralService()

    decision = service.triage("家庭经济比较困难，我想申请助学金")

    assert decision.category == "学生资助"
    assert decision.department == CampusDepartment.FINANCIAL_AID_CENTER
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.needs_human_follow_up is False

def test_triage_routes_health_question_to_campus_hospital():
    service = CampusReferralService()

    decision = service.triage("我今天发烧了，想问一下去哪里看病")

    assert decision.category == "校园医疗"
    assert decision.department == CampusDepartment.CAMPUS_HOSPITAL
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.needs_human_follow_up is False


def test_triage_routes_immediate_threat_to_campus_security():
    service = CampusReferralService()

    decision = service.triage("有人威胁我，现在正在宿舍门口堵我")

    assert decision.category == "校园安全事件"
    assert decision.department == CampusDepartment.CAMPUS_SECURITY
    assert decision.urgency == ReferralUrgency.URGENT
    assert decision.needs_human_follow_up is True
def test_triage_prioritizes_high_risk_over_other_matches():
    service = CampusReferralService()

    decision = service.triage("考试压力太大，我已经不想活了")

    assert decision.category == "校园安全与心理危机"
    assert decision.department == CampusDepartment.CAMPUS_SECURITY
    assert decision.urgency == ReferralUrgency.URGENT
    assert decision.needs_human_follow_up is True
class FakeCampusResourceRetriever:
    def __init__(self):
        self.received_query = None
        self.received_top_k = None

    def build_context(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        self.received_query = query
        self.received_top_k = top_k

        return (
            "[资料1｜来源：campus-referral-resources.md]\n"
            "教务处主要处理补考、选课和学分问题。"
        )


def test_triage_adds_knowledge_context():
    fake_retriever = FakeCampusResourceRetriever()

    service = CampusReferralService(
        resource_retriever=fake_retriever,
    )

    decision = service.triage(
        "我想咨询补考和学分问题"
    )

    assert fake_retriever.received_query == "我想咨询补考和学分问题"
    assert fake_retriever.received_top_k == 3
    assert "教务处主要处理补考" in decision.knowledge_context

class FailingCampusResourceRetriever:
    def build_context(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        raise RuntimeError("模拟知识检索服务不可用")


def test_triage_falls_back_when_knowledge_retrieval_fails():
    failing_retriever = FailingCampusResourceRetriever()

    service = CampusReferralService(
        resource_retriever=failing_retriever,
    )

    decision = service.triage(
        "我的成绩有问题，想申请补考"
    )

    assert decision.category == "教务咨询"
    assert decision.department == CampusDepartment.ACADEMIC_AFFAIRS
    assert decision.urgency == ReferralUrgency.NORMAL
    assert decision.knowledge_context == ""