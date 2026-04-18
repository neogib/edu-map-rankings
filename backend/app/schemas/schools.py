from app.models.schools import (
    EtapEdukacjiBase,
    KategoriaUczniowBase,
    KsztalcenieZawodoweBase,
    StatusPublicznoprawnyBase,
    SzkolaAllData,
    SzkolaBase,
    TypSzkolyBase,
)
from app.schemas.base import CustomBaseModel
from app.schemas.exam_results import (
    WynikE8PublicWithPrzedmiot,
    WynikEMPublicWithPrzedmiot,
)
from app.schemas.locations import (
    MiejscowoscPublic,
    MiejscowoscPublicWithGmina,
    UlicaPublic,
)
from app.schemas.ranking_shared import RankingPublic


class SzkolaPublic(CustomBaseModel, SzkolaAllData):
    id: int


# Short version of Szkola for listing schools with minimal info
# Fields are compressed for minimal data transfer
class SzkolaPublicShort(CustomBaseModel, SzkolaBase):
    id: int
    latitude: float
    longitude: float
    wynik: float | None
    typ: str
    status: str
    miejscowosc: str


class SzkolaPublicWithRelations(SzkolaPublic):
    etapy_edukacji: list["EtapEdukacjiPublic"]
    typ: "TypSzkolyPublic"
    status_publicznoprawny: "StatusPublicznoprawnyPublic"
    kategoria_uczniow: "KategoriaUczniowPublic"
    miejscowosc: MiejscowoscPublicWithGmina
    ulica: UlicaPublic | None
    ksztalcenie_zawodowe: list["KsztalcenieZawodowePublic"]
    wyniki_e8: list[WynikE8PublicWithPrzedmiot]
    wyniki_em: list[WynikEMPublicWithPrzedmiot]
    rankingi: list[RankingPublic]
    latitude: float | None = None
    longitude: float | None = None


class SzkolaRankingRow(CustomBaseModel, SzkolaBase):
    id: int
    numer_rspo: int
    status_publicznoprawny: "StatusPublicznoprawnyPublic"
    miejscowosc: MiejscowoscPublic


class KsztalcenieZawodowePublic(CustomBaseModel, KsztalcenieZawodoweBase):
    id: int


class EtapEdukacjiPublic(CustomBaseModel, EtapEdukacjiBase):
    id: int


class KategoriaUczniowPublic(CustomBaseModel, KategoriaUczniowBase):
    id: int


class TypSzkolyPublic(CustomBaseModel, TypSzkolyBase):
    id: int


class StatusPublicznoprawnyPublic(CustomBaseModel, StatusPublicznoprawnyBase):
    id: int
