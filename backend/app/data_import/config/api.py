from enum import Enum
from pathlib import Path
from typing import ClassVar, final

from pydantic_settings import BaseSettings, SettingsConfigDict


@final
class SchoolStatus(Enum):
    "Defines which school statuses to fetch from the API and their corresponding starting pages"

    ACTIVE = (False, False, 1)
    CLOSED = (True, True, 1)

    def __init__(self, is_closed: bool, fetch_enabled: bool, start_page: int):
        self.is_closed = is_closed
        self.fetch_enabled = fetch_enabled
        self.start_page = start_page


@final
class APISettings:
    API_SCHOOLS_URL: str = "https://api.rspo.gov.pl/api/placowki/"
    HEADERS: ClassVar[dict[str, str]] = {"accept": "application/json"}
    CONCURRENT_REQUESTS: int = 10


class APIAuthSettings(BaseSettings):
    RSPO_USERNAME: str
    RSPO_PASSWORD: str

    model_config: SettingsConfigDict = SettingsConfigDict(  # pyright: ignore[reportIncompatibleVariableOverride]
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@final
class RetrySettings:
    INITIAL_DELAY = 1
    MAX_DELAY = 30
    MAX_RETRIES = 20


@final
class TIMEOUT:
    CONNECT = 30
    READ = 90
