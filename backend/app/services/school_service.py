from typing import cast

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import Session, func, select

from app.core.sqlalchemy_typing import orm_rel_attr
from app.models.exam_results import WynikE8, WynikEM
from app.models.locations import Gmina, Miejscowosc, Powiat
from app.models.schools import Szkola
from app.schemas.school_filters import SchoolFilterParams
from app.schemas.schools import SzkolaPublicShort, SzkolaPublicWithRelations
from app.services.base_service import BaseService
from app.services.exceptions import EntityNotFoundError
from app.services.school_filters import build_schools_short_query


class SchoolService(BaseService[Szkola]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Szkola)

    def get_school(self, school_id: int) -> Szkola:
        return self._get_entity(school_id)

    def get_school_with_relations(self, school_id: int) -> SzkolaPublicWithRelations:
        stmt = (
            select(
                Szkola,
                func.ST_Y(Szkola.geom).label("latitude"),
                func.ST_X(Szkola.geom).label("longitude"),
            )
            .where(Szkola.id == school_id)
            .options(
                joinedload(orm_rel_attr(Szkola.typ)),
                joinedload(orm_rel_attr(Szkola.status_publicznoprawny)),
                joinedload(orm_rel_attr(Szkola.kategoria_uczniow)),
                joinedload(orm_rel_attr(Szkola.ulica)),
                joinedload(orm_rel_attr(Szkola.miejscowosc))
                .joinedload(orm_rel_attr(Miejscowosc.gmina))
                .joinedload(orm_rel_attr(Gmina.powiat))
                .joinedload(orm_rel_attr(Powiat.wojewodztwo)),
                selectinload(orm_rel_attr(Szkola.etapy_edukacji)),
                selectinload(orm_rel_attr(Szkola.ksztalcenie_zawodowe)),
                selectinload(orm_rel_attr(Szkola.wyniki_e8)).joinedload(
                    orm_rel_attr(WynikE8.przedmiot)
                ),
                selectinload(orm_rel_attr(Szkola.wyniki_em)).joinedload(
                    orm_rel_attr(WynikEM.przedmiot)
                ),
                selectinload(orm_rel_attr(Szkola.rankingi)),
            )
        )
        row = self.session.exec(stmt).first()
        if not row:
            raise EntityNotFoundError(entity_id=school_id, model_name=Szkola.__name__)

        base_school, latitude, longitude = cast(
            tuple[Szkola, float | None, float | None], row
        )
        base_school.wyniki_e8.sort(key=lambda w: (w.rok, w.przedmiot.nazwa))
        base_school.wyniki_em.sort(key=lambda w: (w.rok, w.przedmiot.nazwa))

        school = SzkolaPublicWithRelations.model_validate(
            base_school, from_attributes=True
        )
        school.latitude = latitude
        school.longitude = longitude
        return school

    def get_schools(self) -> list[Szkola]:
        return self._get_entities()

    def get_schools_live(self, filters: SchoolFilterParams) -> list[SzkolaPublicShort]:
        stmt = build_schools_short_query(filters)

        rows = (
            self.session.connection().execute(stmt).mappings().all()
        )  # use execute from sqlalchemy Session to get mappings

        return [SzkolaPublicShort.model_validate(row) for row in rows]
