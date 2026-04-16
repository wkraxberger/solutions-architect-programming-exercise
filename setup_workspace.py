"""Interactive helper to pick a workspace and save its id to .env."""
import os
from pathlib import Path

import smartsheet
from dotenv import load_dotenv, set_key
from smartsheet.models import Workspace

ENV_FILE = Path(__file__).parent / ".env"


def pick_or_create(client) -> int:
    workspaces = client.Workspaces.list_workspaces().data

    if workspaces:
        print("\nYour workspaces:")
        for i, w in enumerate(workspaces, 1):
            print(f"  {i}. {w.name}  ({w.id})")
        print("  0. Create a new workspace\n")
    else:
        print("\nNo workspaces found. You'll need to create one with 0.\n")

    while True:
        choice = input("Pick one: ").strip()

        if choice == "0" or not workspaces:
            name = input("Name for the new workspace: ").strip()
            if not name:
                print("Name can't be empty.")
                continue
            ws = client.Workspaces.create_workspace(Workspace({"name": name})).result
            print(f"Created '{ws.name}' (id={ws.id})")
            return ws.id

        try:
            idx = int(choice)
            if 1 <= idx <= len(workspaces):
                return workspaces[idx - 1].id
        except ValueError:
            pass

        print(f"Invalid choice. Enter 1-{len(workspaces)} or 0 to create.")


def main():
    load_dotenv(ENV_FILE)

    token = os.environ.get("SMARTSHEET_ACCESS_TOKEN")
    if not token:
        raise SystemExit(
            "SMARTSHEET_ACCESS_TOKEN not set. Put it in .env first."
        )

    client = smartsheet.Smartsheet(token)
    client.errors_as_exceptions(True)

    wsid = pick_or_create(client)

    ENV_FILE.touch(exist_ok=True)
    set_key(str(ENV_FILE), "SMARTSHEET_WORKSPACE_ID", str(wsid))
    print(f"\nSaved SMARTSHEET_WORKSPACE_ID={wsid} to {ENV_FILE.name}")


if __name__ == "__main__":
    main()
