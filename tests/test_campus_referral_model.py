import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.entities import CampusReferralRecord


def test_campus_referral_record_can_be_persisted():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        record = CampusReferralRecord(
            session_public_id="session-001",
            message="我最近压力很大，想预约心理咨询",
            category="心理支持",
            department="心理咨询中心",
            urgency="PRIORITY",
            reason="用户描述了压力和情绪方面的困扰",
            suggestions_json=json.dumps(
                [
                    "联系学校心理咨询中心预约",
                    "向辅导员说明近期状态",
                ],
                ensure_ascii=False,
            ),
            knowledge_context=(
                "[资料1｜来源：campus-referral-resources.md]\n"
                "心理咨询中心可以提供心理支持。"
            ),
            needs_human_follow_up=True,
            status="PENDING",
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        saved_record = db.scalar(
            select(CampusReferralRecord).where(
                CampusReferralRecord.id == record.id
            )
        )

        assert record.id is not None
        assert saved_record is not None
        assert saved_record.session_public_id == "session-001"
        assert saved_record.department == "心理咨询中心"
        assert saved_record.urgency == "PRIORITY"
        assert saved_record.needs_human_follow_up is True
        assert saved_record.status == "PENDING"