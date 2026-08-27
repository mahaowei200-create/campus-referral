from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CampusDepartment(str, Enum):     #校园部门枚举
    PSYCHOLOGICAL_CENTER = "心理咨询中心"
    COUNSELOR = "辅导员"
    ACADEMIC_AFFAIRS = "教务处"
    STUDENT_AFFAIRS = "学生工作处"
    CAREER_CENTER = "就业指导中心"
    FINANCIAL_AID_CENTER = "学生资助中心"
    CAMPUS_HOSPITAL = "校医院"
    CAMPUS_SECURITY = "校园保卫处"
    OTHER = "其他"


class ReferralUrgency(str, Enum):   #紧急情况枚举
    NORMAL = "NORMAL"
    PRIORITY = "PRIORITY"
    URGENT = "URGENT"


class CampusReferralRequest(BaseModel):  #校园Referral请求
    session_id: str | None = Field(default=None, alias="sessionId")
    message: str = Field(min_length=1, max_length=500)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message cannot be blank")
        return cleaned

class CampusReferralDecision(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    department: CampusDepartment
    urgency: ReferralUrgency
    reason: str = Field(min_length=1, max_length=500)
    suggestions: list[str] = Field(min_length=1, max_length=5)
    needs_human_follow_up: bool = Field(alias="needsHumanFollowUp")
    knowledge_context: str = Field(
        default="",
        alias="knowledgeContext",
        max_length=4000,
    )
    