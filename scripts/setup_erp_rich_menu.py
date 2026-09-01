"""Publish the default Pearnly ERP LINE Rich Menu."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.line_erp.rich_menu import setup_default_menu  # noqa: E402


def main() -> int:
    rich_menu_id = setup_default_menu()
    if not rich_menu_id:
        print("ERP Rich Menu publish failed")
        return 1
    print(f"ERP Rich Menu published: {rich_menu_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
