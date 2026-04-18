from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies import SessionDep
from app.schemas.school_filters import SchoolFilterParams
from app.schemas.schools import (
    SzkolaPublicShort,
    SzkolaPublicWithRelations,
)
from app.services.school_service import SchoolService

_ = SzkolaPublicWithRelations.model_rebuild()


router = APIRouter(
    prefix="/schools",
    tags=["schools"],
)


def get_school_service(session: SessionDep) -> SchoolService:
    return SchoolService(session)


SchoolServiceDep = Annotated[SchoolService, Depends(get_school_service)]


@router.get("/live")
async def read_schools_live(
    service: SchoolServiceDep, filters: Annotated[SchoolFilterParams, Query()]
) -> list[SzkolaPublicShort]:
    return service.get_schools_live(filters)


@router.get("/{school_id}")
async def read_school(
    school_id: int, service: SchoolServiceDep
) -> SzkolaPublicWithRelations:
    return service.get_school_with_relations(school_id)
