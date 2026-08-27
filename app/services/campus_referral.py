import logging

from app.schemas.campus_referral import (
    CampusDepartment,
    CampusReferralDecision,
    ReferralUrgency,
)
from app.services.campus_resource import CampusResourceRetriever


logger = logging.getLogger(__name__)


HIGH_RISK_WORDS = (
    "自杀",
    "自残",
    "不想活",
    "结束生命",
    "伤害自己",
    "轻生",
    "伤害别人",
)


PSYCHOLOGICAL_WORDS = (
    "失眠",
    "焦虑",
    "压力",
    "情绪低落",
    "难过",
    "抑郁",
    "崩溃",
)


CAMPUS_SAFETY_WORDS = (
    "威胁我",
    "跟踪我",
    "堵我",
    "打我",
    "校园暴力",
    "欺凌",
    "霸凌",
    "持刀",
    "被骚扰",
)


NORMAL_REFERRAL_RULES = (
    {
        "keywords": (
            "成绩",
            "考试",
            "补考",
            "选课",
            "学分",
            "课程",
            "教务",
        ),
        "category": "教务咨询",
        "department": CampusDepartment.ACADEMIC_AFFAIRS,
        "reason": "用户咨询成绩、考试、选课或课程相关问题",
        "suggestions": [
            "联系教务处查询具体办理流程",
            "准备学号及相关课程信息",
        ],
    },
    {
        "keywords": (
            "实习",
            "简历",
            "就业",
            "求职",
            "招聘",
            "面试",
        ),
        "category": "就业咨询",
        "department": CampusDepartment.CAREER_CENTER,
        "reason": "用户咨询实习、求职或职业发展相关问题",
        "suggestions": [
            "联系就业指导中心了解招聘和实习信息",
            "准备个人简历及目标岗位信息",
        ],
    },
    {
        "keywords": (
            "助学金",
            "奖学金",
            "学费",
            "经济困难",
            "家庭经济",
            "勤工助学",
            "资助",
        ),
        "category": "学生资助",
        "department": CampusDepartment.FINANCIAL_AID_CENTER,
        "reason": "用户咨询经济困难或学生资助相关问题",
        "suggestions": [
            "联系学生资助中心了解申请条件",
            "准备家庭经济情况及相关证明材料",
        ],
    },
    {
        "keywords": (
            "发烧",
            "感冒",
            "头痛",
            "肚子痛",
            "身体不舒服",
            "看病",
            "校医院",
        ),
        "category": "校园医疗",
        "department": CampusDepartment.CAMPUS_HOSPITAL,
        "reason": "用户咨询身体不适或校园医疗服务",
        "suggestions": [
            "联系校医院了解接诊时间和地点",
            "如果症状严重或持续加重，请及时联系当地医疗急救服务",
        ],
    },
)


class CampusReferralService:
    def __init__(
        self,
        resource_retriever: CampusResourceRetriever | None = None,
    ):
        self.resource_retriever = resource_retriever

    def triage(self, message: str) -> CampusReferralDecision:
        normalized_message = message.strip().lower()

        decision = self._triage_by_rules(normalized_message)

        return self._add_knowledge_context(
            message=message,
            decision=decision,
        )

    def _triage_by_rules(
        self,
        normalized_message: str,
    ) -> CampusReferralDecision:
        if any(
            word in normalized_message
            for word in HIGH_RISK_WORDS
        ):
            return CampusReferralDecision(
                category="校园安全与心理危机",
                department=CampusDepartment.CAMPUS_SECURITY,
                urgency=ReferralUrgency.URGENT,
                reason="用户表达了明确的自伤、轻生或伤人风险",
                suggestions=[
                    "立即联系校园保卫处、辅导员或当地紧急服务",
                    "尽快前往有其他人在场的安全区域",
                    "联系身边可信任的人陪伴，不要独自处理",
                    "同步联系学校心理咨询中心",
                ],
                needsHumanFollowUp=True,
            )

        if any(
            word in normalized_message
            for word in CAMPUS_SAFETY_WORDS
        ):
            return CampusReferralDecision(
                category="校园安全事件",
                department=CampusDepartment.CAMPUS_SECURITY,
                urgency=ReferralUrgency.URGENT,
                reason="用户描述了正在发生或可能立即发生的人身安全威胁",
                suggestions=[
                    "立即联系校园保卫处或当地紧急服务",
                    "尽快前往有老师、同学或工作人员在场的安全区域",
                    "联系辅导员或身边可信任的人陪同处理",
                ],
                needsHumanFollowUp=True,
            )

        if any(
            word in normalized_message
            for word in PSYCHOLOGICAL_WORDS
        ):
            return CampusReferralDecision(
                category="心理支持",
                department=CampusDepartment.PSYCHOLOGICAL_CENTER,
                urgency=ReferralUrgency.PRIORITY,
                reason="用户描述了压力、睡眠或情绪方面的困扰",
                suggestions=[
                    "联系学校心理咨询中心预约",
                    "向辅导员或可信任的人说明近期状态",
                ],
                needsHumanFollowUp=True,
            )

        for rule in NORMAL_REFERRAL_RULES:
            if any(
                word in normalized_message
                for word in rule["keywords"]
            ):
                return CampusReferralDecision(
                    category=rule["category"],
                    department=rule["department"],
                    urgency=ReferralUrgency.NORMAL,
                    reason=rule["reason"],
                    suggestions=rule["suggestions"],
                    needsHumanFollowUp=False,
                )

        return CampusReferralDecision(
            category="其他校园咨询",
            department=CampusDepartment.OTHER,
            urgency=ReferralUrgency.NORMAL,
            reason="当前规则无法确定具体负责部门",
            suggestions=[
                "联系校园综合服务大厅进行确认",
                "也可以先向辅导员说明具体问题",
            ],
            needsHumanFollowUp=False,
        )

    def _add_knowledge_context(
        self,
        message: str,
        decision: CampusReferralDecision,
    ) -> CampusReferralDecision:
        if self.resource_retriever is None:
            return decision

        try:
            knowledge_context = (
                self.resource_retriever.build_context(
                    query=message,
                    top_k=3,
                )
            )
        except Exception as exc:
            logger.warning(
                "Campus resource retrieval failed; "
                "using rule-based decision: %s",
                exc,
            )
            return decision

        if not knowledge_context:
            return decision

        return decision.model_copy(
            update={
                "knowledge_context": knowledge_context[:4000],
            }
        )