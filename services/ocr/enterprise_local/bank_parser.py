"""Geometry-based extraction ported from the validated September 3 pilot."""

from __future__ import annotations

import statistics
import unicodedata
from collections import Counter
from decimal import Decimal
from typing import Any, Sequence

TOL = Decimal("0.01")

from .geometry import (
    RowBox,
    TokenBox,
)
from .common import (
    FLEX_DATE_RE,
    TIME_RE,
    _line_direction,
    _loose_money_candidates,
    money,
    norm_text,
)
from .bank_chain import (
    _infer_bank_directions,
    _repair_bank,
)


def _row_from_lines(lines: Sequence[RowBox]) -> RowBox:
    tokens = tuple(token for line in lines for token in line.tokens)
    return RowBox(
        lines[0].page,
        " ".join(line.text for line in sorted(lines, key=lambda line: (line.yc, line.x0))),
        tokens,
        min(line.x0 for line in lines),
        min(line.y0 for line in lines),
        max(line.x1 for line in lines),
        max(line.y1 for line in lines),
    )


def _bank_date_parts(value: object) -> tuple[int, int, int] | None:
    match = FLEX_DATE_RE.search(unicodedata.normalize("NFKC", str(value or "")))
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    if year < 100:
        year += 2000
    if year >= 2400:
        year -= 543
    return day, month, year


def _bank_groups(lines: Sequence[RowBox]) -> list[dict[str, Any]]:
    by_page: dict[int, list[RowBox]] = {}
    for line in lines:
        by_page.setdefault(line.page, []).append(line)

    groups: list[dict[str, Any]] = []
    for page, page_lines in sorted(by_page.items()):
        anchors = [
            line
            for line in page_lines
            if line.x0 < 0.23 and _bank_date_parts(line.text) is not None
        ]
        anchors.sort(key=lambda line: line.yc)
        for index, anchor in enumerate(anchors):
            if index:
                lower = (anchors[index - 1].yc + anchor.yc) / 2
            elif len(anchors) > 1:
                lower = anchor.yc - (anchors[1].yc - anchor.yc) / 2
            else:
                lower = anchor.y0 - 0.01
            if index + 1 < len(anchors):
                upper = (anchor.yc + anchors[index + 1].yc) / 2
            elif len(anchors) > 1:
                upper = anchor.yc + (anchor.yc - anchors[index - 1].yc) / 2
            else:
                upper = anchor.y1 + 0.01
            members = [line for line in page_lines if lower <= line.yc < upper]
            if anchor not in members:
                members.append(anchor)
            combined = _row_from_lines(members)
            groups.append(
                {
                    "page": page,
                    "anchor": anchor,
                    "lines": members,
                    "source": combined,
                    "raw_parts": _bank_date_parts(anchor.text),
                    "carry": any(
                        label in norm_text(combined.text)
                        for label in ("ยอดยกมา", "ยอดเงินคงเหลือยกมา", "balanceforward")
                    ),
                }
            )

    years = Counter(
        parts[2] for group in groups if (parts := group["raw_parts"]) and 2000 <= parts[2] <= 2100
    )
    months = Counter(
        parts[1] for group in groups if (parts := group["raw_parts"]) and 1 <= parts[1] <= 12
    )
    year = years.most_common(1)[0][0] if years else None
    month = months.most_common(1)[0][0] if months else None
    valid_days = [
        parts[0] if parts and 1 <= parts[0] <= 31 else None
        for parts in (group["raw_parts"] for group in groups)
    ]
    for index, group in enumerate(groups):
        parts = group["raw_parts"]
        if not parts or year is None or month is None:
            group["date"] = ""
            continue
        raw_day, raw_month, raw_year = parts
        day = raw_day if 1 <= raw_day <= 31 else None
        if day is None:
            before = next(
                (value for value in reversed(valid_days[:index]) if value is not None), None
            )
            after = next((value for value in valid_days[index + 1 :] if value is not None), None)
            day = before if before == after and before is not None else before or after
        group["date"] = f"{year:04d}-{month:02d}-{day:02d}" if day is not None else ""
        group["date_corrected"] = (raw_day, raw_month, raw_year) != (day, month, year)
    return groups


def _nearest_column_matches(
    groups: Sequence[tuple[int, dict[str, Any]]],
    candidates: Sequence[tuple[TokenBox, Decimal]],
    beta: float,
    tolerance: float,
) -> tuple[dict[int, tuple[TokenBox, Decimal]], float]:
    used: set[int] = set()
    matches: dict[int, tuple[TokenBox, Decimal]] = {}
    residual = 0.0
    for group_index, group in sorted(groups, key=lambda item: item[1]["anchor"].yc):
        anchor = group["anchor"]
        anchor_y = anchor.yc - beta * ((anchor.x0 + anchor.x1) / 2)
        choices = [
            (
                abs((token.yc - beta * token.xc) - anchor_y),
                candidate_index,
                token,
                value,
            )
            for candidate_index, (token, value) in enumerate(candidates)
            if candidate_index not in used
        ]
        if not choices:
            continue
        distance, candidate_index, token, value = min(choices, key=lambda item: item[0])
        if distance > tolerance:
            continue
        used.add(candidate_index)
        matches[group_index] = (token, value)
        residual += distance
    return matches, residual


def _bank_column_assignments(
    groups: Sequence[dict[str, Any]],
    lines: Sequence[RowBox],
    tables: Sequence[dict[str, Any]],
) -> tuple[dict[int, dict[str, tuple[TokenBox, Decimal]]], list[dict[str, Any]]]:
    by_page_groups: dict[int, list[tuple[int, dict[str, Any]]]] = {}
    by_page_lines: dict[int, list[RowBox]] = {}
    by_page_tables: dict[int, list[dict[str, Any]]] = {}
    for index, group in enumerate(groups):
        by_page_groups.setdefault(int(group["page"]), []).append((index, group))
    for line in lines:
        by_page_lines.setdefault(line.page, []).append(line)
    for table in tables:
        by_page_tables.setdefault(int(table["page"]), []).append(table)

    output: dict[int, dict[str, tuple[TokenBox, Decimal]]] = {}
    audit: list[dict[str, Any]] = []
    for page, page_groups in sorted(by_page_groups.items()):
        page_tables = by_page_tables.get(page) or []
        if not page_tables:
            continue
        table = max(
            page_tables,
            key=lambda item: (item["bbox"][2] - item["bbox"][0])
            * (item["bbox"][3] - item["bbox"][1]),
        )
        x0, _, x1, _ = table["bbox"]
        width = max(x1 - x0, 0.001)
        candidates = _loose_money_candidates(by_page_lines.get(page) or [])
        amount_candidates = [
            pair for pair in candidates if 0.31 <= (pair[0].xc - x0) / width <= 0.48
        ]
        balance_candidates = [
            pair for pair in candidates if 0.48 <= (pair[0].xc - x0) / width <= 0.62
        ]
        anchor_y = sorted(group["anchor"].yc for _, group in page_groups)
        pitch = statistics.median(
            right - left for left, right in zip(anchor_y, anchor_y[1:]) if right > left
        )
        tolerance = min(0.42 * pitch, 0.006)
        best_beta = 0.0
        best_balance: dict[int, tuple[TokenBox, Decimal]] = {}
        best_score: tuple[int, float, float] = (-1, float("-inf"), float("-inf"))
        for step in range(-400, 401, 2):
            beta = step / 10000
            matched, residual = _nearest_column_matches(
                page_groups, balance_candidates, beta, tolerance
            )
            score = (len(matched), -residual, -abs(beta))
            if score > best_score:
                best_score = score
                best_beta = beta
                best_balance = matched
        best_amount, amount_residual = _nearest_column_matches(
            page_groups, amount_candidates, best_beta, tolerance
        )
        for group_index, pair in best_balance.items():
            output.setdefault(group_index, {})["balance"] = pair
        for group_index, pair in best_amount.items():
            output.setdefault(group_index, {})["amount"] = pair
        audit.append(
            {
                "page": page,
                "field": "layout_alignment",
                "value": {
                    "beta": round(best_beta, 4),
                    "tolerance": round(tolerance, 6),
                    "date_anchors": len(page_groups),
                    "amount_matches": len(best_amount),
                    "balance_matches": len(best_balance),
                    "amount_residual": round(amount_residual, 6),
                    "balance_residual": round(-best_score[1], 6),
                },
                "basis": "table-relative columns and fixed-anchor perspective fit",
            }
        )
    return output, audit


def parse_bank(
    rows: Sequence[RowBox], pages: int, tables: Sequence[dict[str, Any]] = ()
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    document: dict[str, Any] = {
        "document_type": "bank_statement",
        "bank_name": "",
        "bank_code": "",
        "opening_balance": "",
        "closing_balance": "",
        "entries": [],
    }
    audit: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    groups = _bank_groups(rows)
    assignments, layout_audit = _bank_column_assignments(groups, rows, tables)
    audit.extend(layout_audit)
    for group_index, group in enumerate(groups):
        assigned = assignments.get(group_index, {})
        if group["carry"]:
            balance_pair = assigned.get("balance")
            if balance_pair and not document["opening_balance"]:
                document["opening_balance"] = money(balance_pair[1])
                audit.append(
                    {
                        "field": "opening_balance",
                        "value": document["opening_balance"],
                        "basis": "first-page printed carry-forward row",
                        "source": group["source"].as_source(),
                    }
                )
            continue
        row = group["source"]
        transaction_date = group["date"]
        if not transaction_date:
            continue
        amount_pair = assigned.get("amount")
        balance_pair = assigned.get("balance")
        amount_token = amount_pair[0] if amount_pair else None
        amount = amount_pair[1] if amount_pair else None
        balance_token = balance_pair[0] if balance_pair else None
        balance = balance_pair[1] if balance_pair else None
        description = row.text[:240]
        direction = _line_direction(row.text)
        time_match = TIME_RE.search(row.text)
        entry = {
            "page": str(row.page),
            "transaction_date": transaction_date,
            "transaction_date_raw": " ".join(
                part
                for part in (group["anchor"].text, time_match.group(1) if time_match else "")
                if part
            ),
            "description": description[:240],
            "reference": "",
            "deposit": money(amount) if amount is not None and direction == "deposit" else "",
            "withdrawal": money(amount) if amount is not None and direction == "withdrawal" else "",
            "amount": money(amount) if amount is not None else "",
            "direction": direction,
            "balance": money(balance) if balance is not None else "",
            "chain_repaired": False,
            "chain_amount_imputed": False,
            "review_required": not bool(direction),
        }
        document["entries"].append(entry)
        if group.get("date_corrected"):
            audit.append(
                {
                    "row": len(document["entries"]),
                    "field": "transaction_date",
                    "from": group["anchor"].text,
                    "to": transaction_date,
                    "basis": "statement-wide majority year/month and adjacent printed dates",
                }
            )
        provenance.append(
            {
                "row": len(document["entries"]),
                "source": row.as_source(),
                "amount_bbox": (
                    [amount_token.x0, amount_token.y0, amount_token.x1, amount_token.y1]
                    if amount_token
                    else None
                ),
                "balance_bbox": (
                    [balance_token.x0, balance_token.y0, balance_token.x1, balance_token.y1]
                    if balance_token
                    else None
                ),
            }
        )

    _infer_bank_directions(document, audit)
    if document["entries"]:
        document["closing_balance"] = document["entries"][-1]["balance"]
    repaired, repair_audit = _repair_bank(document)
    audit.extend(repair_audit)
    return repaired, audit, provenance
