"""Publish the six-cell Rich Menu to the DMS LINE channel."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.line_dms.rich_menu import setup_default_menu

if __name__ == "__main__":
    rich_menu_id = setup_default_menu()
    if not rich_menu_id:
        raise SystemExit("DMS Rich Menu setup failed")
    print(rich_menu_id)
