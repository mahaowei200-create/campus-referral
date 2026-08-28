import json

from app.schemas.campus_referral import (
    CampusReferralAdminResponse,
    CampusReferralRequest,
    CampusReferralResponse,
    ReferralStatus,
)
from app.services.campus_referral import (
    CampusReferralService,
)
from app.services.campus_referral_repository import (
    CampusReferralRepository,
)


class CampusReferralApplicationService:
    def __init__(
        self,
        triage_service: CampusReferralService,
        repository: CampusReferralRepository,
    ):
        self.triage_service = triage_service
        self.repository = repository

    def create_referral(
        self,
        request: CampusReferralRequest,
        user_id: int | None,
    ) -> CampusReferralResponse:
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

    def list_pending_referrals(
        self,
    ) -> list[CampusReferralAdminResponse]:
        records = self.repository.list_pending()

        return [
            self._to_admin_response(record)
            for record in records
        ]

    def update_referral_status(
        self,
        record_id: int,
        status: ReferralStatus,
    ) -> CampusReferralAdminResponse | None:
        record = self.repository.update_status(
            record_id=record_id,
            status=status.value,
        )

        if record is None:
            return None

        return self._to_admin_response(record)

    @staticmethod
    def _to_admin_response(
        record,
    ) -> CampusReferralAdminResponse:
        suggestions = json.loads(
            record.suggestions_json
        )

        return CampusReferralAdminResponse(
            recordId=record.id,
            userId=record.user_id,
            sessionId=record.session_public_id,
            message=record.message,
            category=record.category,
            department=record.department,
            urgency=record.urgency,
            reason=record.reason,
            suggestions=suggestions,
            needsHumanFollowUp=(
                record.needs_human_follow_up
            ),
            knowledgeContext=(
                record.knowledge_context
            ),
            status=record.status,
            createdAt=record.created_at,
            updatedAt=record.updated_at,
        )
