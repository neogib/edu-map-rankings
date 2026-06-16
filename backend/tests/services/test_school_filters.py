import pytest
from sqlmodel import Session, col, select

from app.schemas.school_filters import SchoolFilterParams
from app.schemas.schools import SzkolaPublicShort
from app.services.school_service import SchoolService

pytestmark = pytest.mark.seeded


@pytest.fixture
def school_service(seeded_session: Session) -> SchoolService:
    return SchoolService(seeded_session)


@pytest.fixture
def reference_school(school_service: SchoolService) -> SzkolaPublicShort:
    params = SchoolFilterParams.model_validate({"limit": 1})
    schools = school_service.get_schools_live(params)
    if not schools:
        pytest.skip("No seeded schools found to get reference school")
    return schools[0]


def test_get_schools_live_no_filters(school_service: SchoolService) -> None:
    params = SchoolFilterParams.model_validate({"limit": 10})
    schools = school_service.get_schools_live(params)
    assert len(schools) > 0


def test_get_schools_live_bbox_within_and_outside(
    school_service: SchoolService, reference_school: SzkolaPublicShort
) -> None:
    # 1. Get a reference school to get coordinates
    assert reference_school.latitude is not None
    assert reference_school.longitude is not None

    lat, lon = reference_school.latitude, reference_school.longitude

    # 2. Create a bbox containing this school
    bbox_within = SchoolFilterParams.model_validate(
        {
            "min_lng": lon - 0.01,
            "max_lng": lon + 0.01,
            "min_lat": lat - 0.01,
            "max_lat": lat + 0.01,
            "bbox_mode": "within",
            "limit": 10,
        }
    )
    schools_within = school_service.get_schools_live(bbox_within)
    assert len(schools_within) > 0
    assert any(s.id == reference_school.id for s in schools_within)

    # 3. Create a bbox excluding this school (shifted far away)
    bbox_outside = SchoolFilterParams.model_validate(
        {
            "min_lng": lon - 0.01,
            "max_lng": lon + 0.01,
            "min_lat": lat - 0.01,
            "max_lat": lat + 0.01,
            "bbox_mode": "outside",
        }
    )
    schools_outside = school_service.get_schools_live(bbox_outside)
    assert all(s.id != reference_school.id for s in schools_outside)


def test_school_filter_bbox_validation() -> None:
    # Bbox parameters must be provided together or raise ValueError
    with pytest.raises(
        ValueError, match="All bbox parameters must be provided together"
    ):
        SchoolFilterParams.model_validate({"min_lng": 21.0})  # pyright: ignore[reportUnusedCallResult]

    # Latitudes/Longitudes validation: max must be greater than min
    with pytest.raises(ValueError, match="max_lat must be greater than min_lat"):
        SchoolFilterParams.model_validate(  # pyright: ignore[reportUnusedCallResult]
            {
                "min_lng": 20.0,
                "max_lng": 21.0,
                "min_lat": 52.0,
                "max_lat": 51.0,
            }
        )

    with pytest.raises(ValueError, match="max_lng must be greater than min_lng"):
        SchoolFilterParams.model_validate(  # pyright: ignore[reportUnusedCallResult]
            {
                "min_lng": 22.0,
                "max_lng": 21.0,
                "min_lat": 51.0,
                "max_lat": 52.0,
            }
        )


def test_get_schools_live_filter_by_score_range(school_service: SchoolService) -> None:
    # Fetch schools that have a score
    from app.models.schools import Szkola

    db_schools_with_wynik = list(
        school_service.session.exec(
            select(Szkola).where(col(Szkola.wynik) != None).limit(5)  # noqa: E711
        ).all()
    )

    if not db_schools_with_wynik:
        pytest.skip("No seeded schools with scores found")

    scores = [s.wynik for s in db_schools_with_wynik if s.wynik is not None]
    min_s = int(min(scores))
    max_s = int(max(scores))

    filter_params = SchoolFilterParams.model_validate(
        {"min_score": min_s, "max_score": max_s, "limit": 10}
    )
    filtered_schools = school_service.get_schools_live(filter_params)

    for school in filtered_schools:
        assert school.wynik is not None
        assert min_s <= school.wynik <= max_s


def test_get_schools_live_search_q(
    school_service: SchoolService, reference_school: SzkolaPublicShort
) -> None:
    school_name = reference_school.nazwa
    search_term = school_name[:5]

    filter_params = SchoolFilterParams.model_validate({"q": search_term, "limit": 10})
    filtered_schools = school_service.get_schools_live(filter_params)

    assert len(filtered_schools) > 0
    assert all(search_term.lower() in s.nazwa.lower() for s in filtered_schools)


def test_get_schools_live_closed_schools(school_service: SchoolService) -> None:
    # By default closed=False, zlikwidowane schools are excluded.
    # Let's check if there are zlikwidowane schools in the database.
    from app.models.schools import Szkola

    closed_schools = list(
        school_service.session.exec(
            select(Szkola).where(col(Szkola.zlikwidowana) == True).limit(5)  # noqa: E712
        ).all()
    )

    if not closed_schools:
        return

    closed_school = closed_schools[0]

    # closed=False: should NOT find the closed school
    params_open_only = SchoolFilterParams.model_validate(
        {"closed": False, "q": closed_school.nazwa, "limit": 10}
    )
    open_schools = school_service.get_schools_live(params_open_only)
    assert all(s.id != closed_school.id for s in open_schools)

    # closed=True: should find the closed school if it has coordinates
    if closed_school.geom is not None:
        params_all = SchoolFilterParams.model_validate(
            {"closed": True, "q": closed_school.nazwa, "limit": 10}
        )
        all_schools = school_service.get_schools_live(params_all)
        assert any(s.id == closed_school.id for s in all_schools)
