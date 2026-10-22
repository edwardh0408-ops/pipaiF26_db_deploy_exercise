"""Read the placeholder database stored as one CSV per table."""

import csv
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[1] / "databases"

TABLES = (
    "student",
    "skill",
    "tool",
    "availability_slot",
    "student_skill",
    "student_tool",
    "student_availability",
)


def read_table(name: str) -> list[dict[str, str]]:
    if name not in TABLES:
        raise KeyError(f"Unknown table: {name}")
    path = DATABASE / f"{name}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def students() -> list[dict[str, str]]:
    """Return the student rows the homepage displays, in table order."""
    return [
        {"student_id": row["student_id"], "full_name": row["full_name"]}
        for row in read_table("student")
        if row["full_name"].strip()
    ]
