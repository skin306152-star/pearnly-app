"""LINE text questions with postback quick replies."""

from __future__ import annotations

from urllib.parse import urlencode


def postback_action(label: str, action: str, **params) -> dict:
    data = {"a": action, **{key: value for key, value in params.items() if value is not None}}
    return {
        "type": "postback",
        "label": label[:20],
        "data": urlencode(data),
        "displayText": label[:300],
    }


def quick_reply_item(label: str, action: str, **params) -> dict:
    return {"type": "action", "action": postback_action(label, action, **params)}


def question(title: str, subtitle: str, items: list[dict]) -> dict:
    message = {"type": "text", "text": f"{title}\n{subtitle}"}
    if items:
        message["quickReply"] = {"items": items}
    return message


__all__ = ["postback_action", "question", "quick_reply_item"]
