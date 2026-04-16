import logging
from typing import Sequence

import smartsheet

logger = logging.getLogger(__name__)

COLUMN_TITLES: tuple[str, ...] = ("Name", "ARR", "Sector", "City")

class SmartsheetService:

    def __init__(self, access_token: str, workspace_id: int) -> None:
        if not access_token:
            raise ValueError("Smartsheet access token is required")
        if not workspace_id:
            raise ValueError("Smartsheet workspace id is required")
        self._client = smartsheet.Smartsheet(access_token)
        self._client.errors_as_exceptions(True)
        self._workspace_id = workspace_id

    def create_sheet(self, name: str) -> tuple[int, dict[str, int], str]:
        """Create a sheet in the workspace and return (sheet_id, {column_title: column_id}, url)."""
        columns = [
            smartsheet.models.Column(
                {"title": title, "type": "TEXT_NUMBER", "primary": idx == 0}
            )
            for idx, title in enumerate(COLUMN_TITLES)
        ]
        sheet_spec = smartsheet.models.Sheet({"name": name, "columns": columns})
        response = self._client.Workspaces.create_sheet_in_workspace(
            self._workspace_id, sheet_spec
        )

        sheet = response.result
        column_map = {col.title: col.id for col in sheet.columns}
        logger.info("Created sheet '%s' (id=%s)", sheet.name, sheet.id)
        return sheet.id, column_map, sheet.permalink

    def add_parent_row(self, sheet_id: int, cells: Sequence[dict]) -> int:
        """Add a top-level row and return its id so children can be attached."""
        row = smartsheet.models.Row()
        row.to_bottom = True
        row.cells = list(cells)
        response = self._client.Sheets.add_rows(sheet_id, [row])
        parent_id = response.result[0].id
        logger.info("Added parent row %s to sheet %s", parent_id, sheet_id)
        return parent_id

    def add_child_rows(
        self,
        sheet_id: int,
        parent_row_id: int,
        rows_cells: Sequence[Sequence[dict]],
    ) -> list[int]:
        """Add rows under a given parent."""
        rows = []
        for cells in rows_cells:
            row = smartsheet.models.Row()
            row.parent_id = parent_row_id
            row.cells = list(cells)
            rows.append(row)
        response = self._client.Sheets.add_rows(sheet_id, rows)
        ids = [r.id for r in response.result]
        logger.info("Added %d child rows under parent %s", len(ids), parent_row_id)
        return ids
