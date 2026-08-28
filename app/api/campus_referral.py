from typing import Annotated

from fastapi import (APIRouter,Depends,HTTPException,)
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import current_user
from app.models.entities import UserAccount
from app.schemas.campus_referral import (CampusReferralRequest,CampusReferralResponse,)
from app.services.campus_referral import (CampusReferralService,)
from app.services.campus_referral_application import (CampusReferralApplicationService,)
from app.services.campus_referral_repository import (CampusReferralRepository,)
from app.services.campus_resource import (CampusResourceRetriever,)
from app.services.knowledge import KnowledgeService


router = APIRouter(prefix="/api/campus-referrals",tags=["campus-referrals"])


def get_campus_referral_application_service(db: Annotated[Session, Depends(get_db)],) -> CampusReferralApplicationService:
    settings = get_settings()

    knowledge_service = KnowledgeService(db=db,settings=settings,)
    resource_retriever = CampusResourceRetriever(knowledge_service=knowledge_service,)
    triage_service = CampusReferralService(resource_retriever=resource_retriever,)
    repository = CampusReferralRepository(db=db,)

    return CampusReferralApplicationService(
        triage_service=triage_service,
        repository=repository,
    )


@router.post("/triage",response_model=CampusReferralResponse,)
def triage_campus_referral(request: CampusReferralRequest,user: Annotated[UserAccount,Depends(current_user),],application_service: Annotated[CampusReferralApplicationService,
    Depends(
            get_campus_referral_application_service
        ),
    ],) -> CampusReferralResponse:
    if "ROLE_ADMIN" in user.roles:
        raise HTTPException(
            status_code=403,
            detail=(
                "管理员账号不能发起学生校园咨询分诊。"
            ),
        )

    return application_service.create_referral(
        request=request,
        user_id=user.id,
    )