import argparse
import asyncio
import logging
from collections.abc import Callable

from app.core.logging import configure_logging
from app.data_import.api.db.decomposer import Decomposer
from app.data_import.api.exceptions import SchoolsDataError
from app.data_import.api.fetcher import SchoolsAPIFetcher
from app.data_import.config.api import SchoolStatus
from app.data_import.config.excel import ExamType
from app.data_import.excel.db.table_splitter import TableSplitter
from app.data_import.excel.reader import ExcelReader

logger = logging.getLogger(__name__)


async def api_importer() -> None:
    total_processed = 0

    for status in SchoolStatus:
        if not status.fetch_enabled:
            logger.info(f"⏭️ Skipping fetching {status.name} schools - fetch disabled")
            continue
        zlikwidowana = status.is_closed
        api_fetcher = SchoolsAPIFetcher(zlikwidowana=zlikwidowana)

        start_page = status.start_page
        segment_number = 1

        status_label = f"zlikwidowana={zlikwidowana}"
        logger.info(f"🔄 Starting import for {status_label} from page {start_page}...")

        try:
            batch_iterator = api_fetcher.fetch_schools_batches(
                start_page=start_page,
            )
            async for schools_data in batch_iterator:
                logger.info(
                    f"🔄 Processing segment {segment_number} ({status_label})..."
                )
                logger.info(
                    f"⚡ Processing {len(schools_data)} schools from segment {segment_number}..."
                )
                with Decomposer() as decomposer:
                    decomposer.prune_and_decompose_schools(schools_data)

                total_processed += len(schools_data)
                logger.info(
                    f"✅ Successfully processed segment {segment_number} ({len(schools_data)} schools)"
                )
                logger.info(f"📊 Total schools processed so far: {total_processed}")
                segment_number += 1

        except SchoolsDataError as e:
            logger.error(f"📛 Schools data error: {e}")
            logger.error(
                f"❌ Error processing segment {segment_number} ({status_label})"
            )
            break
        except Exception as e:
            logger.critical(f"🚨 Unhandled, critical error: {e}")
            logger.error(
                f"❌ Error processing segment {segment_number} ({status_label})"
            )
            break

    logger.info(
        f"🎉 Import from API completed. Total schools processed: {total_processed}"
    )


def excel_importer(year: int | None = None):
    reader = ExcelReader()
    year_str = f" for year {year}" if year is not None else ""
    logger.info(f"📄 Starting Excel data import{year_str}...")
    for exam_type in ExamType:
        logger.info(f"📊 Processing {exam_type.name} exam data...")
        for file_year, exam_data in reader.load_files(exam_type, year=year):
            logger.info(f"🗓️ Processing {exam_type.name} data for year {file_year}...")
            with TableSplitter(exam_data, exam_type, file_year) as splitter:
                if not splitter.initialize():
                    logger.warning(
                        f"⚠️ Skipping invalid {exam_type.name} data for year {file_year}"
                    )
                    continue  # skip this file - it was invalid
                splitter.split_exam_results()
                logger.info(
                    f"✅ Successfully processed {exam_type.name} data for year {file_year}"
                )
    logger.info("🎉 Excel data import completed")


class ImportOptions:
    option: str  # pyright: ignore[reportUninitializedInstanceVariable]
    year: int | None = None


COMMANDS: dict[str, Callable[[int | None], None]] = {
    "api": lambda _year: asyncio.run(api_importer()),
    "excel": lambda year: excel_importer(year=year),
}


def main():
    configure_logging("data_import.log")

    parser = argparse.ArgumentParser(
        description="Main import script for school data processing"
    )
    _ = parser.add_argument(
        "-o",
        "--option",
        type=str,
        required=True,
        choices=["api", "excel"],
        help="Operation to perform: api (schools API import) or excel (exam data import)",
    )
    _ = parser.add_argument(
        "-y",
        "--year",
        type=int,
        required=False,
        default=None,
        help="Optional year to filter excel import files",
    )

    args = ImportOptions()
    _ = parser.parse_args(namespace=args)

    try:
        logger.info(f"🚀 Starting {args.option} operation...")
        COMMANDS[args.option](args.year)
        logger.info(f"✅ {args.option.capitalize()} operation completed successfully")
    except Exception as e:
        logger.error(f"❌ Error executing {args.option} operation: {e}")


if __name__ == "__main__":
    main()
