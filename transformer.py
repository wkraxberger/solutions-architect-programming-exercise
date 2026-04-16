import csv
from pathlib import Path
from typing import Sequence


def load_rows(csv_path: Path) -> list[dict]:
    """Read the CSV into dicts and cast arr to int."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["arr"] = int(r["arr"]) if r["arr"].strip() else 0
    return rows


def group_rows(rows: list[dict], group_by: Sequence[str]):
    """Nest rows by the given fields.

    group_by=("country", "state") -> {country: {state: [rows]}}
    Empty group_by returns a flat list.
    """
    if not group_by:
        return list(rows)

    first_field = group_by[0]
    remaining_fields = group_by[1:]

    buckets: dict[str, list[dict]] = {}
    for r in rows:
        key = r.get(first_field) or "Unknown"
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(r)

    result = {}
    for key, rs in buckets.items():
        result[key] = group_rows(rs, remaining_fields)
    return result
