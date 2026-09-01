"""Shared LINE summary card for Cowork and ERP document review."""

from __future__ import annotations

from urllib.parse import urlencode


def postback_action(label: str, action: str, draft_id: str) -> dict:
    return {
        "type": "postback",
        "label": label[:20],
        "data": urlencode({"a": action, "draft": draft_id}),
        "displayText": label,
    }


def build_summary_card(
    *,
    title: str,
    subtitle: str,
    alt_text: str,
    accent: str,
    summary: list[dict],
    detail_label: str,
    detail_count: int,
    detail_hint: str,
    edit_label: str,
    edit_uri: str,
    discard_action: dict,
) -> dict:
    body = [*summary, {"type": "separator", "margin": "md", "color": "#EEEAF7"}]
    body.append(
        {
            "type": "box",
            "layout": "vertical",
            "margin": "md",
            "paddingAll": "12px",
            "cornerRadius": "10px",
            "backgroundColor": "#F5F1FF",
            "contents": [
                {
                    "type": "text",
                    "text": f"{detail_label} · {max(0, int(detail_count))}",
                    "size": "sm",
                    "weight": "bold",
                    "color": "#30295F",
                    "wrap": True,
                },
                {
                    "type": "text",
                    "text": detail_hint,
                    "size": "xxs",
                    "color": "#6F688C",
                    "margin": "xs",
                    "wrap": True,
                },
            ],
        }
    )
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": accent,
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "size": "lg",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": subtitle,
                        "size": "xxs",
                        "color": "#F4F4F4",
                        "margin": "xs",
                        "wrap": True,
                    },
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "16px",
                "contents": body,
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "paddingAll": "14px",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "color": accent,
                        "action": {
                            "type": "uri",
                            "label": edit_label[:20],
                            "uri": edit_uri,
                        },
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "color": "#C53A3A",
                        "action": discard_action,
                    },
                ],
            },
        },
    }


__all__ = ["build_summary_card", "postback_action"]
