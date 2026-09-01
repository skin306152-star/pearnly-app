"""Pearnly ERP LINE six-cell Rich Menu."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from services.line_platform import rich_menu as publisher

logger = logging.getLogger(__name__)

CHANNEL = "erp"
MENU_NAME = "pearnly-erp-v1"
IMAGE_PATH = (
    Path(__file__).resolve().parents[2] / "static" / "brand" / "line-richmenu-erp-v1-2500x1686.png"
)
WIDTH, HEIGHT = 2500, 1686
ROW_HEIGHT = 843
COLUMN_EDGES = (0, 833, 1666, 2500)


def _area(col: int, mode: str, display_text: str) -> dict[str, Any]:
    return {
        "bounds": {
            "x": COLUMN_EDGES[col],
            "y": 0,
            "width": COLUMN_EDGES[col + 1] - COLUMN_EDGES[col],
            "height": ROW_HEIGHT,
        },
        "action": {
            "type": "postback",
            "data": urlencode({"a": f"mode:{mode}"}),
            "displayText": display_text,
        },
    }


def build_payload() -> dict[str, Any]:
    return {
        "size": {"width": WIDTH, "height": HEIGHT},
        "selected": False,
        "name": MENU_NAME,
        "chatBarText": "เมนู ERP",
        "areas": [
            _area(0, "purchase", "ซื้อ"),
            _area(1, "sales", "ขาย"),
        ],
    }


def setup_default_menu(image_path: str | Path | None = None) -> str | None:
    path = Path(image_path) if image_path else IMAGE_PATH
    try:
        image = path.read_bytes()
    except OSError:
        logger.exception("Could not read ERP LINE Rich Menu image")
        return None
    return publisher.replace_default(
        CHANNEL,
        MENU_NAME,
        build_payload(),
        image,
    )


__all__ = ["IMAGE_PATH", "MENU_NAME", "build_payload", "setup_default_menu"]
