"""CLI entry point. Reads a CSV, groups rows, populates a Smartsheet sheet."""
import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from smartsheet_service import SmartsheetService
from transformer import group_rows, load_rows


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--csv",
        default="data/SACodePrompt_MockData.csv",
        help="Path to the CSV file",
    )
    p.add_argument(
        "--group-by",
        default="country,state",
        help="Comma-separated fields, outermost first (e.g. country,state)",
    )
    p.add_argument(
        "--name",
        default=None,
        help="Sheet name (defaults to a timestamped one)",
    )
    p.add_argument(
        "--workspace-id",
        type=int,
        default=None,
        help="Target workspace id. Overrides SMARTSHEET_WORKSPACE_ID from env.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the tree and ARR totals, skips the API",
    )
    return p.parse_args()


def total_arr(tree) -> int:
    if isinstance(tree, list):
        return sum(r.get("arr", 0) for r in tree)
    return sum(total_arr(sub) for sub in tree.values())


def print_tree(tree, indent: int = 0) -> None:
    pad = "  " * indent
    if isinstance(tree, list):
        print(f"{pad}({len(tree)} accounts, ARR={total_arr(tree):,})")
        return
    for key, sub in tree.items():
        print(f"{pad}{key}: ARR={total_arr(sub):,}")
        print_tree(sub, indent + 1)


def populate(service, sid, cols, tree, parent_id=None):
    """Walk the tree and create rows, parents first so children can reference them."""
    if isinstance(tree, list):
        rows_cells = [
            [
                {"column_id": cols["Name"],   "value": r["company"]},
                {"column_id": cols["ARR"],    "value": r["arr"]},
                {"column_id": cols["Sector"], "value": r.get("sector", "")},
                {"column_id": cols["City"],   "value": r.get("city", "")},
            ]
            for r in tree
        ]
        service.add_child_rows(sid, parent_id, rows_cells)
        return

    for key, sub in tree.items():
        cells = [
            {"column_id": cols["Name"], "value": key},
            {"column_id": cols["ARR"],  "formula": "=SUM(CHILDREN())"},
        ]
        if parent_id is None:
            node_id = service.add_parent_row(sid, cells)
        else:
            node_id = service.add_child_rows(sid, parent_id, [cells])[0]
        populate(service, sid, cols, sub, parent_id=node_id)


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    args = parse_args()

    group_by = tuple(f.strip() for f in args.group_by.split(",") if f.strip())
    if not group_by:
        raise SystemExit("--group-by must have at least one field")

    rows = load_rows(Path(args.csv))
    tree = group_rows(rows, group_by)

    if args.dry_run:
        print_tree(tree)
        print(f"\nTotal: {len(rows)} accounts, ARR = {total_arr(tree):,}")
        return

    token = os.environ.get("SMARTSHEET_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "SMARTSHEET_ACCESS_TOKEN not set."
        )

    wsid_env = os.environ.get("SMARTSHEET_WORKSPACE_ID")
    wsid = args.workspace_id or (int(wsid_env) if wsid_env else None)
    if not wsid:
        raise SystemExit(
            "SMARTSHEET_WORKSPACE_ID not set. "
            "Run `python setup_workspace.py` to pick one, "
            "or set it directly in .env / pass --workspace-id."
        )

    sheet_name = args.name or f"Accounts Import - {datetime.now():%Y-%m-%d %H:%M}"
    service = SmartsheetService(token, workspace_id=wsid)
    sid, cols, url = service.create_sheet(sheet_name)
    populate(service, sid, cols, tree)
    print(f"Done. Sheet id: {sid}")
    print(f"Sheet url: {url}")


if __name__ == "__main__":
    main()
