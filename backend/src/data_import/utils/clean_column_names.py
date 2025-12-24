import re

from unidecode import unidecode


def clean_subjects_names(name: str) -> str:
    # Remove any parenthesized content (including the parentheses)
    name = re.sub(r"\([^)]*\)", "", name)

    # Remove percentage signs and asterisks
    name = re.sub(r"[*%]", "", name)

    # Remove hyphens and any spaces following them
    name = re.sub(r"-\s*", "", name)

    # Strip leading/trailing whitespace
    name = name.strip()

    # Replace forward slashes with underscores
    name = name.replace("/", "_")

    # Convert everything to lowercase
    return name.lower()


def clean_column_name(name: str) -> str:
    name = clean_subjects_names(name)

    # Normalize accented characters to ASCII
    name = unidecode(name)

    # Collapse any remaining whitespace into single underscores
    name = re.sub(r"\s+", "_", name)

    # Convert everything to lowercase
    return name
