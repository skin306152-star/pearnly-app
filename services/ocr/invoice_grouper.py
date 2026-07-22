# -*- coding: utf-8 -*-
"""
Pearnly · v0.11 发票智能分组模块
把一个 PDF 的 N 页拆成 M 张独立发票 · 每张生成一条历史记录

分组规则(优先级从高到低):
1. 按 invoice_number 分界(跨页发票场景):相同号的页合并为一张;无号页默认续接
   当前发票,但「自带完整钱块(总额+税基/税额)」的无号页判为独立发票——治「另一张
   打包票的号没读出来就被静默并进上一张」的塌缩漏票(SINCERE 多票 PDF 实案)。
2. 无 invoice_number 但每页有 total_amount → 每页独立一张
3. 无 invoice_number 也无 total_amount → 整个 PDF 当 1 张发票(fallback)

合并规则(同一张发票多页时):
- invoice_number / date / seller_* / buyer_* / vat / subtotal:取第一个非空
- total_amount:取第一个非空(通常在最后一页)
- items:所有页的 items 按顺序拼接
- notes:拼接(换行分隔)
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict, Any

from services.ocr.money import normalize_money
from services.ocr.schemas_invoice import ThaiInvoice

# 合并时标量字段全量随行,不再手工白名单——白名单漏字段会静默蒸发
# (f003 折扣漏合并、台账#5 currency/document_type 不透出,同一类病)。
# items/notes 有专用合并逻辑;嵌套结构与页级判定标志不属于发票字段。
_NON_SCALAR_FIELDS = frozenset(
    {
        "items",
        "notes",
        "additional_invoices",
        "source_refs",
        "is_not_invoice",
        "is_copy_or_duplicate",
    }
)
_SCALAR_FIELDS = tuple(k for k in ThaiInvoice.model_fields if k not in _NON_SCALAR_FIELDS)


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False


def _first_non_empty(pages: List[Dict], field: str):
    """从多页中取第一个非空的字段值"""
    for p in pages:
        f = p.get("fields") or {}
        v = f.get(field)
        if not _is_empty(v):
            return v
    return None


def _norm_name(v: Any) -> str:
    """去掉全部空白再比对:同一联的泰文行被 OCR 读出碎空格(ราคา ส่ง vs ราคาส่ง)
    是双联去重失手的头号原因(INV2026030002 实案 2026-07-03)。"""
    return "".join(str(v or "").split())


def _norm_qty(v: Any) -> str:
    """取数量的数字部分:两联的同一行常被读成 "1" 与 "1 ก้อน"(单位词时有时无)。"""
    m = re.match(r"\s*([\d.,]*\d)", str(v or ""))
    return m.group(1).replace(",", "") if m else str(v or "").strip()


def _norm_price(v: Any) -> str:
    f = normalize_money(v)
    return f"{f:.2f}" if f is not None else str(v or "").strip()


def _keep_longer_name(entry: Dict, raw_name: str, norm_name: str) -> None:
    """判重命中时保留更长的 name(通常更详细)。"""
    if len(raw_name) > len(str(entry["item"].get("name", "") or "").strip()):
        entry["item"]["name"] = raw_name
        entry["name"] = norm_name


def _merge_items(pages: List[Dict]) -> List[Dict]:
    """把多页的 items 拼接 · v88 · 跨页去重(2026-07-03 归一化+复写联加强)
    规则(比对全部先归一化:name 去空白 · qty 取数字 · price 数值化 —— 双联的同一行
    常被 OCR 读成「ราคา ส่ง / 1」与「ราคาส่ง / 1 ก้อน」,原样比对必失手):
    1) 严格:(name, qty, price) 归一化后相同 → 重复
    2) 松散:qty+price 相同 · 且一方 name 是另一方子串 → 重复(保留更长 name)
    3) 复写联模糊:本页过半行已被 1/2 判重(证明这页是同票复写联)时,剩余行按
       qty+price 相同 + name 相似度 ≥0.9 并入前页最相近行 —— 兜住复写联上被 OCR
       读出错字的行(นครสวรรค์ vs นครสวรรศ์ · INV2026030002 实案 5 行存成 10 行)。
       正常多页发票各页行互不重复,永远到不了这一步,不会误合口味变体。
    """
    entries: List[Dict] = []  # {"item","name","qty","price"} · 按页序追加
    seen_strict = set()
    for p in pages:
        f = p.get("fields") or {}
        items = f.get("items") or []
        if not isinstance(items, list):
            continue
        prev_end = len(entries)  # 本页开始前的存量 = 前页行(模糊并入只对它们扫)
        n_items = 0
        for it in items:
            if not isinstance(it, dict):
                continue
            n_items += 1
            raw_name = str(it.get("name", "") or "").strip()
            name = _norm_name(raw_name)
            qty = _norm_qty(it.get("qty"))
            price = _norm_price(it.get("price"))

            # 严格去重
            if (name, qty, price) in seen_strict:
                continue

            # 松散去重:qty+price 相同 · name 子串关系
            dup_of = None
            if name and (qty or price):
                for prev in entries:
                    if (
                        prev["qty"] == qty
                        and prev["price"] == price
                        and prev["name"]
                        and (name in prev["name"] or prev["name"] in name)
                    ):
                        dup_of = prev
                        break
            if dup_of is not None:
                _keep_longer_name(dup_of, raw_name, name)
                continue

            seen_strict.add((name, qty, price))
            entries.append({"item": it, "name": name, "qty": qty, "price": price})

        # 复写联判定:本页 ≥2 行且过半已判重(判重数 = n_items − 本页新增)→ 剩余行
        # 大概率是同一联被 OCR 读出错字,对每行找前页 qty+price 相同的最相近行,
        # 相似度 ≥0.9 才并入(取最优,不取先到)。被并入行的严格键留在 seen_strict:
        # 后页同键行仍该判重(它是已并入行的复本),语义正确。
        page_new = entries[prev_end:]
        n_dup = n_items - len(page_new)
        if n_items >= 2 and n_dup * 2 >= n_items and page_new:
            for entry in page_new:
                if not entry["name"]:
                    continue
                best, best_ratio = None, 0.0
                for prev in entries[:prev_end]:
                    if (
                        prev["qty"] != entry["qty"]
                        or prev["price"] != entry["price"]
                        or not prev["name"]
                    ):
                        continue
                    ratio = SequenceMatcher(None, entry["name"], prev["name"]).ratio()
                    if ratio > best_ratio:
                        best, best_ratio = prev, ratio
                if best is not None and best_ratio >= 0.9:
                    _keep_longer_name(
                        best, str(entry["item"].get("name", "") or "").strip(), entry["name"]
                    )
                    entries.remove(entry)

    return [e["item"] for e in entries]


def _build_invoice_from_pages(pages_group: List[Dict]) -> Dict[str, Any]:
    """把同一张发票的 N 页合并成一个 fields 字典"""
    if not pages_group:
        return {}
    # 标量字段一律取第一个非空(跨页发票各字段可能散在不同页)
    merged_fields: Dict[str, Any] = {k: _first_non_empty(pages_group, k) for k in _SCALAR_FIELDS}
    merged_fields["items"] = _merge_items(pages_group)
    # notes 拼接
    notes = []
    for p in pages_group:
        f = p.get("fields") or {}
        n = f.get("notes")
        if not _is_empty(n):
            notes.append(str(n))
    if notes:
        merged_fields["notes"] = " · ".join(notes)
    return merged_fields


def _self_contained_total(fields: Dict[str, Any]):
    """无发票号的页若自带完整钱块(总额 + 税基或税额)→ 它自成一张发票,不是续页。

    真正的续页至多带一个结尾总额(或只是溢出的明细行),不会自带 subtotal/vat;据此把
    「另一张打包票的号没读出来」与「同一张票跨页续表」区分开——前者过去被无条件并进第一
    张(见旧策略1),N 张打包票于是塌成 1 张、被吞票的金额一并蒸发。返回归一化后的总额
    (供与前一张比对,避免把每页重复打印汇总块的续页误判成独立票);非自足页返回 None。"""
    if _is_empty(fields.get("total_amount")):
        return None
    if _is_empty(fields.get("subtotal")) and _is_empty(fields.get("vat")):
        return None
    return normalize_money(fields.get("total_amount"))


def _group_by_invoice_boundary(pages: List[Dict]) -> List[Dict[str, Any]]:
    """按页序切分发票:带号页开一张(同号页再并回,治跨页重复页眉);无号页默认续接当前
    发票,但「自足且总额与当前不同」的无号页判为独立发票。取代旧「无号页一律并入第一组」。"""
    groups: List[Dict[str, Any]] = []
    by_number: Dict[str, Dict[str, Any]] = {}
    current = None
    pending: List[Dict] = []  # 首张发票成型前的前导无号非自足页,等它来收

    def _new_group() -> Dict[str, Any]:
        g = {"source_pages": [], "page_indices": [], "_total": None}
        groups.append(g)
        return g

    def _flush_pending(group: Dict[str, Any]) -> None:
        if pending:
            group["source_pages"][:0] = pending
            group["page_indices"].extend(pp["page_index"] for pp in pending)
            pending.clear()

    for p in pages:
        f = p.get("fields") or {}
        inv_no = f.get("invoice_number")
        if not _is_empty(inv_no):
            key = str(inv_no).strip()
            current = by_number.get(key)
            if current is None:
                current = _new_group()
                by_number[key] = current
                _flush_pending(current)
        else:
            sc_total = _self_contained_total(f)
            cur_total = current["_total"] if current else None
            if sc_total is not None and (current is None or sc_total != cur_total):
                current = _new_group()
                _flush_pending(current)
            elif current is None:
                pending.append(p)  # 前导无号非自足页 · 挂起等第一张发票
                continue
        current["source_pages"].append(p)
        current["page_indices"].append(p["page_index"])
        if current["_total"] is None and not _is_empty(f.get("total_amount")):
            current["_total"] = normalize_money(f.get("total_amount"))

    if pending:  # 全程无一张成型发票(极少见)→ 兜成一张
        g = current or _new_group()
        for pp in pending:
            g["source_pages"].append(pp)
            g["page_indices"].append(pp["page_index"])

    return [
        {
            "invoice_fields": _build_invoice_from_pages(g["source_pages"]),
            "source_pages": g["source_pages"],
            "page_indices": sorted(g["page_indices"]),
        }
        for g in groups
    ]


def group_pages_to_invoices(pages: List[Dict]) -> List[Dict[str, Any]]:
    """
    把一个 PDF 的所有页分组成 M 张独立发票

    输入:pages = [{"page_index": 1, "fields": {...}}, ...]
    输出:[
        {
            "invoice_fields": {合并后的字段},
            "source_pages": [原始页对象列表],
            "page_indices": [1, 2]  # 1-based
        },
        ...
    ]
    """
    if not pages:
        return []

    # 给每页标上 1-based 的 page_index(如果没有)
    for i, p in enumerate(pages, start=1):
        if "page_index" not in p:
            p["page_index"] = i

    # ------ 策略 1:按 invoice_number 分界 ------
    # 门槛:有发票号的页覆盖过半(无号页 ≤ 半数)才按号分界;否则落金额分界(策略2)。
    # groups_by_inv/pages_without_inv 仅用于门槛判定;分界与无号页归属见
    # _group_by_invoice_boundary(续页并入当前票,自足的无号页自成一张 · 不再吞进第一组)。
    groups_by_inv = {}
    pages_without_inv = []
    for p in pages:
        f = p.get("fields") or {}
        if not _is_empty(f.get("invoice_number")):
            groups_by_inv.setdefault(str(f["invoice_number"]).strip(), []).append(p)
        else:
            pages_without_inv.append(p)

    if groups_by_inv and len(pages_without_inv) <= len(pages) / 2:
        return _group_by_invoice_boundary(pages)

    # ------ 策略 2:按金额页分界 ------
    # 没有发票号 · 看每页是否有 total_amount
    # 规则:有 total 的页作为一张发票的"结束页" · 它和前面所有无 total 的页合并
    has_total_any = any(not _is_empty((p.get("fields") or {}).get("total_amount")) for p in pages)

    if has_total_any:
        result = []
        buffer = []  # 累积无 total 的页
        for p in pages:
            buffer.append(p)
            f = p.get("fields") or {}
            total = f.get("total_amount")
            if not _is_empty(total):
                # 这是一张发票的结束
                result.append(
                    {
                        "invoice_fields": _build_invoice_from_pages(buffer),
                        "source_pages": buffer,
                        "page_indices": [pp["page_index"] for pp in buffer],
                    }
                )
                buffer = []
        # 剩余的 buffer(结尾无 total 的页)· 附加到最后一张
        if buffer:
            if result:
                result[-1]["source_pages"].extend(buffer)
                result[-1]["page_indices"].extend([p["page_index"] for p in buffer])
            else:
                # 理论上不会到这里 · 但保险
                result.append(
                    {
                        "invoice_fields": _build_invoice_from_pages(buffer),
                        "source_pages": buffer,
                        "page_indices": [p["page_index"] for p in buffer],
                    }
                )
        return result

    # ------ 策略 3:fallback 全部作为一张 ------
    return [
        {
            "invoice_fields": _build_invoice_from_pages(pages),
            "source_pages": pages,
            "page_indices": [p["page_index"] for p in pages],
        }
    ]
