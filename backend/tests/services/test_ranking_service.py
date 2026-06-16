import pytest
from sqlmodel import Session

from app.schemas.ranking import (
    RankingDirection,
    RankingScope,
    RankingsParams,
)
from app.services.ranking_service import RankingService

pytestmark = pytest.mark.seeded


@pytest.fixture
def ranking_service(seeded_session: Session) -> RankingService:
    return RankingService(seeded_session)


def test_get_rankings_page_national_scope(ranking_service: RankingService) -> None:
    filters = ranking_service.get_ranking_filters()
    year = filters.years[0]
    ranking_type = filters.types[0]

    params = RankingsParams.model_validate(
        {
            "year": year,
            "type": ranking_type,
            "scope": RankingScope.KRAJ,
            "direction": RankingDirection.BEST,
            "page": 1,
            "page_size": 10,
        }
    )
    result = ranking_service.get_rankings_page(params)

    assert result.page == 1
    assert result.page_size == 10
    assert result.total >= 0
    if result.total > 0:
        assert len(result.rankings) > 0
        # Check that it's sorted by national place ascending
        places = [r.miejsce_kraj for r in result.rankings]
        assert places == sorted(places)


def test_get_rankings_page_voivodeship_scope(ranking_service: RankingService) -> None:
    filters = ranking_service.get_ranking_filters()
    year = filters.years[0]
    ranking_type = filters.types[0]
    voivodeship_id = filters.voivodeships[0].id

    params = RankingsParams.model_validate(
        {
            "year": year,
            "type": ranking_type,
            "scope": RankingScope.WOJEWODZTWO,
            "voivodeship_id": voivodeship_id,
            "direction": RankingDirection.BEST,
            "page": 1,
            "page_size": 10,
        }
    )
    result = ranking_service.get_rankings_page(params)

    assert result.total >= 0
    if result.total > 0:
        assert len(result.rankings) > 0
        # Check that it's sorted by voivodeship place ascending
        places = [
            r.miejsce_wojewodztwo for r in result.rankings if r.miejsce_wojewodztwo
        ]
        assert places == sorted(places)


def test_get_rankings_page_county_scope(ranking_service: RankingService) -> None:
    filters = ranking_service.get_ranking_filters()
    year = filters.years[0]
    ranking_type = filters.types[0]
    county_id = filters.counties[0].id

    params = RankingsParams.model_validate(
        {
            "year": year,
            "type": ranking_type,
            "scope": RankingScope.POWIAT,
            "county_id": county_id,
            "direction": RankingDirection.BEST,
            "page": 1,
            "page_size": 10,
        }
    )
    result = ranking_service.get_rankings_page(params)

    assert result.total >= 0
    if result.total > 0:
        assert len(result.rankings) > 0
        places = [r.miejsce_powiat for r in result.rankings]
        assert places == sorted(places)


def test_get_rankings_page_worst_direction(ranking_service: RankingService) -> None:
    filters = ranking_service.get_ranking_filters()
    year = filters.years[0]
    ranking_type = filters.types[0]

    params = RankingsParams.model_validate(
        {
            "year": year,
            "type": ranking_type,
            "scope": RankingScope.KRAJ,
            "direction": RankingDirection.WORST,
            "page": 1,
            "page_size": 10,
        }
    )
    result = ranking_service.get_rankings_page(params)

    assert result.total >= 0
    if result.total > 0:
        assert len(result.rankings) > 0
        places = [r.miejsce_kraj for r in result.rankings]
        # Since it's WORST, it should be sorted descending
        assert places == sorted(places, reverse=True)


def test_get_rankings_page_search(ranking_service: RankingService) -> None:
    # First, get a list of rankings to find a school name
    filters = ranking_service.get_ranking_filters()
    params = RankingsParams.model_validate(
        {
            "year": filters.years[0],
            "type": filters.types[0],
            "scope": RankingScope.KRAJ,
            "direction": RankingDirection.BEST,
            "page": 1,
            "page_size": 5,
        }
    )
    initial_result = ranking_service.get_rankings_page(params)
    if initial_result.total == 0:
        pytest.skip("No seeded rankings found to test search")

    existing_school_name = initial_result.rankings[0].szkola.nazwa
    # Test partial search (first 5 chars)
    search_term = existing_school_name[:5]

    search_params = RankingsParams.model_validate(
        {
            "year": filters.years[0],
            "type": filters.types[0],
            "scope": RankingScope.KRAJ,
            "direction": RankingDirection.BEST,
            "search": search_term,
            "page": 1,
            "page_size": 10,
        }
    )
    search_result = ranking_service.get_rankings_page(search_params)

    assert search_result.total > 0
    assert all(
        search_term.lower() in r.szkola.nazwa.lower() for r in search_result.rankings
    )


def test_get_rankings_page_pagination(ranking_service: RankingService) -> None:
    filters = ranking_service.get_ranking_filters()

    params_page = RankingsParams.model_validate(
        {
            "year": filters.years[0],
            "type": filters.types[0],
            "scope": RankingScope.KRAJ,
            "direction": RankingDirection.BEST,
            "page": 1,
            "page_size": 2,
        }
    )
    result_page1 = ranking_service.get_rankings_page(params_page)

    if result_page1.total < 3:
        pytest.skip("Not enough seeded rankings to test pagination")

    # Page size = 2, Page = 2
    params_page.page = 2

    result_page2 = ranking_service.get_rankings_page(params_page)

    assert len(result_page2.rankings) <= 2
    # The elements on page 2 should be different from page 1
    page1_ids = {r.id for r in result_page1.rankings}
    page2_ids = {r.id for r in result_page2.rankings}
    assert page1_ids.isdisjoint(page2_ids)
