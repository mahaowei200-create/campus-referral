from app.schemas.campus_referral import (
    CampusReferralRequest,
    CampusReferralResponse,
)
from app.services.campus_referral import (
    CampusReferralService,
)
from app.services.campus_referral_repository import (
    CampusReferralRepository,
)


class CampusReferralApplicationService:
    def __init__(self,triage_service: CampusReferralService,repository: CampusReferralRepository,):
        self.triage_service = triage_service
        self.repository = repository

    def create_referral(self,request: CampusReferralRequest,user_id: int | None,) -> CampusReferralResponse:
        decision = self.triage_service.triage(
            request.message
        )

        record = self.repository.create(
            message=request.message,
            decision=decision,
            user_id=user_id,
            session_public_id=request.session_id,
        )

        return CampusReferralResponse(
            recordId=record.id,
            category=decision.category,
            department=decision.department,
            urgency=decision.urgency,
            reason=decision.reason,
            suggestions=decision.suggestions,
            needsHumanFollowUp=(
                decision.needs_human_follow_up
            ),
            knowledgeContext=decision.knowledge_context,
            status=record.status,
        )