import csv
import logging

from src.app.models.schools import Szkola
from src.data_import.utils.db.session import DatabaseManagerBase

logger = logging.getLogger(__name__)


class SchoolCoordinatesImporter(DatabaseManagerBase):
    def __init__(self, converted_file: str = "converted_addresses.csv"):
        super().__init__()
        self.converted_file: str = converted_file

    def update_school_coordinates(self):
        """
        Method for updating geodata based on converted addresses.
        """
        session = self._ensure_session()
        total_processed = 0

        with open(self.converted_file, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                logger.info(f"Processing row: {row}")
                if total_processed == 0:
                    try:
                        lat = row.index("g_szer")
                        lon = row.index("g_dlug")
                        id = row.index("id")
                    except ValueError as e:
                        logger.critical(
                            f"🚨 Critical error: Missing expected header in CSV file: {e}"
                        )
                        return
                    total_processed += 1
                    continue

                if row[id] == "" or row[lat] == "" or row[lon] == "":
                    logger.warning(
                        f"Skipping row with missing data: ID={row[id]}, Latitude={row[lat]}, Longitude={row[lon]}"
                    )
                    continue
                school = session.get(Szkola, int(row[id]))
                if not school:
                    logger.warning(f"School with ID {row[id]} not found.")
                    continue

                school.geolokalizacja_latitude = float(row[lat])
                school.geolokalizacja_longitude = float(row[lon])
                session.add(school)
                session.commit()
                total_processed += 1
