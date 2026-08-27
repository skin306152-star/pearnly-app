from __future__ import annotations

from typing import Optional

MODES = frozenset({"purchase", "sales"})
STATES = frozenset(
    {"menu", "receiving", "ocr_processing", "draft", "editing", "confirmed", "discarded", "failed"}
)


def accept_media_mode(mode: Optional[str], requested: str) -> bool:
    """只有已选采购/销售模式才接收媒体；切换模式会覆盖会话模式。"""
    return bool(mode in MODES and requested in MODES)


def next_state(state: str, event: str) -> str:
    transitions = {
        ("menu", "choose"): "receiving",
        ("receiving", "media"): "ocr_processing",
        ("ocr_processing", "ready"): "draft",
        ("draft", "edit"): "editing",
        ("editing", "edit"): "editing",
        ("draft", "confirm"): "confirmed",
        ("editing", "confirm"): "confirmed",
        ("draft", "discard"): "discarded",
        ("editing", "discard"): "discarded",
        ("ocr_processing", "fail"): "failed",
    }
    return transitions.get((state, event), state)
