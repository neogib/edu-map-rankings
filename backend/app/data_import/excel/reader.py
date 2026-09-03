import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import pandas as pd

from app.data_import.config.core import EXCEL_DIR
from app.data_import.config.excel import EM_FORMULA_PRIORITY, ExamType, ExcelFile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _FileMetadata:
    path: Path
    year: int
    priority: int


class ExcelReader:
    base_data_path: Path = EXCEL_DIR
    _year_only_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<year>\d{4})\.xlsx$", re.IGNORECASE
    )
    _e8_year_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^e8_(?P<year>\d{4})\.xlsx$", re.IGNORECASE
    )
    _em_formula_pattern: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<formula>em\d{4})_(?P<year>\d{4})\.xlsx$", re.IGNORECASE
    )

    def __init__(self, base_data_path: Path | None = None):
        """
        Initializes the ExcelReader.

        Args:
            base_data_path: The base path where E8_data and EM_data directories reside.
                            Defaults to the script's directory if None.
        """
        if base_data_path is not None:
            self.base_data_path = base_data_path

    def load_files(
        self, exam_type: ExamType, year: int | None = None
    ) -> Iterator[tuple[int, pd.DataFrame]]:
        """
        Loads Excel files from E8 or EM directories
        """
        target_dir = exam_type.directory_name
        path = self.base_data_path / target_dir
        logger.info(f"📂 Accessing data from directory: {path}")
        yield from self.read_files_from_dir(path, exam_type, year=year)

        logger.info(f"✅ Successfully processed all files from: {path}")

    def read_files_from_dir(
        self, directory_path: Path, exam_type: ExamType, year: int | None = None
    ) -> Iterator[tuple[int, pd.DataFrame]]:
        # Check that the directory actually exists
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return
        files_metadata: list[_FileMetadata] = []

        for file_path in directory_path.glob("*.xlsx"):
            metadata = self._parse_file_metadata(file_path, exam_type)
            if metadata is None:
                continue
            if year is not None and metadata.year != year:
                continue
            files_metadata.append(metadata)

        for metadata in sorted(
            files_metadata,
            key=lambda item: (item.year, item.priority, item.path.name.lower()),
        ):
            file_name = metadata.path.name
            logger.info(f"📄 Processing file: {file_name}")
            try:
                df = pd.read_excel(  # pyright: ignore[reportUnknownMemberType]
                    metadata.path,
                    sheet_name=ExcelFile.SHEET_NAME,
                    header=exam_type.header,
                    skiprows=exam_type.skiprows,
                )
                yield metadata.year, df
            except Exception as e:
                logger.error(f"Error reading file {file_name}: {e}")

    def _parse_file_metadata(
        self, file_path: Path, exam_type: ExamType
    ) -> _FileMetadata | None:
        file_name = file_path.name

        if exam_type is ExamType.EM:
            em_match = self._em_formula_pattern.match(file_name)
            if em_match:
                year = int(em_match.group("year"))
                formula = em_match.group("formula").upper()
                # For the same year we process EM2023 first, then EM2015.
                priority: int = EM_FORMULA_PRIORITY.get(formula, 2)
                return _FileMetadata(path=file_path, year=year, priority=priority)

        year_match = self._year_only_pattern.match(file_name)
        if year_match:
            return _FileMetadata(
                path=file_path, year=int(year_match.group("year")), priority=0
            )

        if exam_type is ExamType.E8:
            e8_match = self._e8_year_pattern.match(file_name)
            if e8_match:
                year = int(e8_match.group("year"))
                return _FileMetadata(path=file_path, year=year, priority=0)

        logger.error(
            f"Invalid filename format: {file_name}. Expected EM: 'EM<formula_year>_<year>.xlsx' or '<year>.xlsx'; Expected E8: 'E8_<year>.xlsx' or '<year>.xlsx'"
        )
        return None
