import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import CampusReferralRecord
from app.schemas.campus_referral import CampusReferralDecision

ALLOWED_REFERRAL_STATUSES = {
    "PENDING",
    "PROCESSING",
    "RESOLVED",
    "CLOSED",
}


class CampusReferralRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        message: str,
        decision: CampusReferralDecision,
        user_id: int | None = None,
        session_public_id: str | None = None,
    ) -> CampusReferralRecord:
        record = CampusReferralRecord(
            user_id=user_id,
            session_public_id=session_public_id,
            message=message,
            category=decision.category,
            department=decision.department.value,
            urgency=decision.urgency.value,
            reason=decision.reason,
            suggestions_json=json.dumps(
                decision.suggestions,
                ensure_ascii=False,
            ),
            knowledge_context=decision.knowledge_context,
            needs_human_follow_up=(
                decision.needs_human_follow_up
            ),
            status="PENDING",
        )

        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise

        return record
    def get_by_id(self,record_id: int,) -> CampusReferralRecord | None:
        return self.db.get(
            CampusReferralRecord,
            record_id,
        )
    def list_pending(self) -> list[CampusReferralRecord]:
        statement = (
            select(CampusReferralRecord).where(CampusReferralRecord.needs_human_follow_up.is_(True),CampusReferralRecord.status == "PENDING",).order_by(CampusReferralRecord.id.desc())
        )

        return list(
            self.db.scalars(statement).all()
        )
    def update_status(self,record_id: int,status: str,) -> CampusReferralRecord | None:
        normalized_status = status.strip().upper()

        if normalized_status not in ALLOWED_REFERRAL_STATUSES:
            raise ValueError(
                f"Unsupported referral status: {status}"
            )

        record = self.get_by_id(record_id)

        if record is None:
            return None

        record.status = normalized_status

        try:
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise

        return record