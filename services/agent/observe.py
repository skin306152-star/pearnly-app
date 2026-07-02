# -*- coding: utf-8 -*-
"""工具结果 → 喂回模型的最小观测(从 loop 抽出,给 loop 腾 500 行预算)。

只保留组织回复必需的字段,别灌满上下文;数字全来自工具真实结果。
加只读工具 = 这里加一个分支 + fallbacks 加兜底 + manifest 登记。
"""

from __future__ import annotations

_ERR_MAX = 160  # 推送错误原文喂模型的截断长度(人话化由模型做,原文防灌上下文)


def payload(tool: str, result) -> dict:
    data = result.data if isinstance(result.data, dict) else {}
    if not result.ok:
        # 失败也带上可选项(套账候选/单据候选),让模型请用户挑一个(非报错回退)。
        out = {"ok": False, "error": result.error_code or "failed"}
        for key in ("workspaces", "candidates", "endpoints", "pushed_endpoint"):
            if data.get(key):
                out[key] = data[key]
        return out
    if tool == "list_history":
        items = data.get("items") or []
        top = [
            {
                "vendor": (i.get("seller_name") or i.get("vendor_name") or ""),
                "amount": i.get("total_amount"),
            }
            for i in items[:5]
        ]
        return {"ok": True, "total": data.get("total", len(items)), "top": top}
    if tool == "history_summary":
        return {
            "ok": True,
            "doc_count": data.get("doc_count", 0),
            "amount_total": data.get("amount_total", 0),
            "by_category": data.get("by_category", []),
        }
    if tool == "usage_this_month":
        b = data.get("billing") or {}
        return {
            "ok": True,
            "pages_used_this_month": b.get("pages_used_this_month"),
            "docs": data.get("docs"),
        }
    if tool == "balance":
        return {
            "ok": True,
            "balance_thb": data.get("balance_thb"),
            "pages_used_this_month": data.get("pages_used_this_month"),
        }
    if tool == "list_notifications":  # result.data 是 list(非上面 dict 化的 data)→ 直接数长度
        return {"ok": True, "count": len(result.data) if isinstance(result.data, list) else 0}
    if tool == "list_workspaces":
        return {
            "ok": True,
            "workspaces": data.get("workspaces", []),
            "current_id": data.get("current_id"),
        }
    if tool == "switch_workspace":
        return {"ok": True, "switched_to": data.get("switched_to")}
    if tool == "push_status":  # 执行器产出即最小观测,只补错误截断
        return {"ok": True, **data, "error": (data.get("error") or "")[:_ERR_MAX]}
    if tool == "rd_lookup":
        return {
            "ok": True,
            "tax_id": data.get("tax_id"),
            "name": data.get("name"),
            "branch": data.get("branch_label"),
            "address": data.get("address"),
            "province": data.get("province"),
        }
    if tool == "my_plan":  # 执行器产出即最小观测
        return {"ok": True, **data}
    if tool in ("recon_overview", "recon_detail"):
        # 执行器产出已是最小观测(recent≤5 / unmatched≤8);漏这支=模型拿不到数字只能空话。
        return {"ok": True, **data}
    return {"ok": True}
