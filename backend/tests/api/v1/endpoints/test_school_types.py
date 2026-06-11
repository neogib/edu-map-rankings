from typing import TypedDict

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.schemas.schools import TypSzkolyPublic
from app.services.exceptions import EntityNotFoundError
from tests.constants import MISSING_INT_ID

pytestmark = pytest.mark.seeded


class ErrorResponse(TypedDict):
    detail: str


school_type_adapter = TypeAdapter(TypSzkolyPublic)
school_type_list_adapter = TypeAdapter(list[TypSzkolyPublic])
error_response_adapter = TypeAdapter(ErrorResponse)


@pytest.fixture
def first_school_type(seeded_client: TestClient) -> TypSzkolyPublic:
    response = seeded_client.get("/api/v1/school_types/")
    assert response.status_code == 200
    data = school_type_list_adapter.validate_python(response.json())
    assert len(data) > 0
    return data[0]


def test_read_school_types_returns_seeded_data(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/school_types/")
    assert response.status_code == 200

    data = school_type_list_adapter.validate_python(response.json())

    assert len(data) > 0


def test_read_school_types_accepts_repeated_names_query_param(
    seeded_client: TestClient,
) -> None:
    response = seeded_client.get(
        "/api/v1/school_types/",
        params=[("names", "___missing_name_1___"), ("names", "___missing_name_2___")],
    )
    assert response.status_code == 200
    data = school_type_list_adapter.validate_python(response.json())
    assert data == []


def test_read_school_types_filters_by_existing_name(
    seeded_client: TestClient,
    first_school_type: TypSzkolyPublic,
) -> None:
    existing_name = first_school_type.nazwa

    response = seeded_client.get(
        "/api/v1/school_types/",
        params=[("names", existing_name)],
    )
    assert response.status_code == 200
    data = school_type_list_adapter.validate_python(response.json())

    assert len(data) > 0
    assert all(item.nazwa == existing_name for item in data)


def test_read_school_type_by_existing_id(
    seeded_client: TestClient,
    first_school_type: TypSzkolyPublic,
) -> None:
    school_type_id = first_school_type.id

    response = seeded_client.get(f"/api/v1/school_types/{school_type_id}")
    assert response.status_code == 200
    data = school_type_adapter.validate_python(response.json())

    assert data.id == school_type_id


def test_read_school_type_returns_404_for_missing_id(
    seeded_client: TestClient,
) -> None:
    response = seeded_client.get(f"/api/v1/school_types/{MISSING_INT_ID}")
    assert response.status_code == 404
    data = error_response_adapter.validate_python(response.json())

    expected_error = EntityNotFoundError(
        entity_id=MISSING_INT_ID, model_name="TypSzkoly"
    )
    assert data["detail"] == str(expected_error)


def test_read_school_types_empty_name_param(seeded_client: TestClient) -> None:
    response = seeded_client.get("/api/v1/school_types/", params={"names": ""})
    assert response.status_code == 200
