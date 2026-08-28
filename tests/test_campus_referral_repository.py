import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.schemas.campus_referral import CampusReferralDecision
from app.services.campus_referral_repository import (
    CampusReferralRepository,
    InvalidReferralStatusTransition,
)


def test_repository_creates_referral_record():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        decision = CampusReferralDecision(
            category="心理支持",
            department="心理咨询中心",
            urgency="PRIORITY",
            reason="用户描述了压力和睡眠问题",
            suggestions=[
                "联系学校心理咨询中心预约",
                "向辅导员说明近期状态",
            ],
            needsHumanFollowUp=True,
            knowledgeContext=(
                "[资料1｜来源：campus-referral-resources.md]\n"
                "心理咨询中心可以提供心理支持。"
            ),
        )

        record = repository.create(
            message="我最近压力很大，而且一直失眠",
            decision=decision,
            user_id=1001,
            session_public_id="session-001",
        )

        saved_suggestions = json.loads(
            record.suggestions_json
        )

        assert record.id is not None
        assert record.user_id == 1001
        assert record.session_public_id == "session-001"
        assert record.category == "心理支持"
        assert record.department == "心理咨询中心"
        assert record.urgency == "PRIORITY"
        assert record.needs_human_follow_up is True
        assert record.status == "PENDING"
        assert len(saved_suggestions) == 2
        assert "心理咨询中心预约" in saved_suggestions[0]
        assert "心理咨询中心可以提供心理支持" in (
            record.knowledge_context
        )
def test_repository_gets_referral_record_by_id():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        decision = CampusReferralDecision(
            category="教务咨询",
            department="教务处",
            urgency="NORMAL",
            reason="用户咨询补考和学分问题",
            suggestions=[
                "联系教务处了解办理流程",
            ],
            needsHumanFollowUp=False,
        )

        created_record = repository.create(
            message="我想咨询补考问题",
            decision=decision,
            user_id=1001,
            session_public_id="session-002",
        )

        found_record = repository.get_by_id(
            created_record.id
        )

        missing_record = repository.get_by_id(
            999999
        )

        assert found_record is not None
        assert found_record.id == created_record.id
        assert found_record.department == "教务处"
        assert found_record.session_public_id == "session-002"
        assert missing_record is None
def make_referral_decision(
    category: str,
    department: str,
    urgency: str,
    needs_human_follow_up: bool,
) -> CampusReferralDecision:
    return CampusReferralDecision(
        category=category,
        department=department,
        urgency=urgency,
        reason=f"测试{category}分诊结果",
        suggestions=[
            f"联系{department}处理",
        ],
        needsHumanFollowUp=needs_human_follow_up,
    )
def test_repository_lists_pending_human_follow_up_records():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        psychological_record = repository.create(
            message="我最近一直焦虑失眠",
            decision=make_referral_decision(
                category="心理支持",
                department="心理咨询中心",
                urgency="PRIORITY",
                needs_human_follow_up=True,
            ),
            user_id=1001,
            session_public_id="session-psychological",
        )

        urgent_record = repository.create(
            message="我在学校被人跟踪和威胁",
            decision=make_referral_decision(
                category="校园安全事件",
                department="校园保卫处",
                urgency="URGENT",
                needs_human_follow_up=True,
            ),
            user_id=1002,
            session_public_id="session-urgent",
        )

        repository.create(
            message="我想咨询补考时间",
            decision=make_referral_decision(
                category="教务咨询",
                department="教务处",
                urgency="NORMAL",
                needs_human_follow_up=False,
            ),
            user_id=1003,
            session_public_id="session-normal",
        )

        pending_records = repository.list_pending()

        pending_ids = [
            record.id
            for record in pending_records
        ]

        assert pending_ids == [
            urgent_record.id,
            psychological_record.id,
        ]

        assert all(
            record.needs_human_follow_up
            for record in pending_records
        )

        assert all(
            record.status == "PENDING"
            for record in pending_records
        )
def test_repository_updates_referral_status():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        record = repository.create(
            message="我最近焦虑失眠，希望获得帮助",
            decision=make_referral_decision(
                category="心理支持",
                department="心理咨询中心",
                urgency="PRIORITY",
                needs_human_follow_up=True,
            ),
            user_id=1001,
            session_public_id="session-update-status",
        )

        updated_record = repository.update_status(
            record_id=record.id,
            status="PROCESSING",
        )

        reloaded_record = repository.get_by_id(
            record.id
        )

        missing_record = repository.update_status(
            record_id=999999,
            status="PROCESSING",
        )

        assert updated_record is not None
        assert updated_record.status == "PROCESSING"

        assert reloaded_record is not None
        assert reloaded_record.status == "PROCESSING"

        assert missing_record is None
def test_repository_rejects_unsupported_status():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        record = repository.create(
            message="我最近焦虑失眠，希望获得帮助",
            decision=make_referral_decision(
                category="心理支持",
                department="心理咨询中心",
                urgency="PRIORITY",
                needs_human_follow_up=True,
            ),
            user_id=1001,
            session_public_id="session-invalid-status",
        )

        with pytest.raises(
            ValueError,
            match="Unsupported referral status",
        ):
            repository.update_status(
                record_id=record.id,
                status="UNKNOWN",
            )

        reloaded_record = repository.get_by_id(
            record.id
        )

        assert reloaded_record is not None
        assert reloaded_record.status == "PENDING"

def test_repository_rejects_backward_status_transition():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(
        bind=engine
    )

    with Session(engine) as db:
        repository = CampusReferralRepository(db)

        record = repository.create(
            message="我最近焦虑失眠",
            decision=make_referral_decision(
                category="心理支持",
                department="心理咨询中心",
                urgency="PRIORITY",
                needs_human_follow_up=True,
            ),
            user_id=1001,
            session_public_id=(
                "session-status-transition"
            ),
        )

        repository.update_status(
            record_id=record.id,
            status="PROCESSING",
        )

        repository.update_status(
            record_id=record.id,
            status="RESOLVED",
        )

        with pytest.raises(
            InvalidReferralStatusTransition,
            match=(
                "Cannot change referral status "
                "from RESOLVED to PENDING"
            ),
        ):
            repository.update_status(
                record_id=record.id,
                status="PENDING",
            )

        reloaded_record = (
            repository.get_by_id(record.id)
        )

        assert reloaded_record is not None
        assert reloaded_record.status == (
            "RESOLVED"
        )