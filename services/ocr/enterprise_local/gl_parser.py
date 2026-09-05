"""Geometry-based extraction ported from the validated September 3 pilot."""

from __future__ import annotations

import re
from copy import deepcopy
from decimal import Decimal
from typing import Any, Sequence

TOL = Decimal("0.01")

from .geometry import (
    RowBox,
    TokenBox,
)
from .common import (
    DATE_RE,
    _money_tokens,
    _without_structural_tokens,
    dec,
    money,
    norm_date,
    norm_text,
)


def _gl_chain(document: dict[str, Any]) -> dict[str, Any]:
    entries = document.get("entries") or []
    previous = dec(document.get("opening_balance"))
    previous_page = None
    checked = 0
    cross_page_checked = 0
    violations = []
    cross_page_violations = []
    for index, row in enumerate(entries, start=1):
        current = dec(row.get("balance"))
        debit, credit = dec(row.get("debit")), dec(row.get("credit"))
        page = int(row.get("page") or 1)
        boundary = previous_page is not None and page != previous_page
        if (
            previous is not None
            and current is not None
            and (debit is not None or credit is not None)
        ):
            checked += 1
            expected = previous + (debit or Decimal("0")) - (credit or Decimal("0"))
            if boundary:
                cross_page_checked += 1
            if abs(expected - current) > TOL:
                item = {
                    "row": index,
                    "page": page,
                    "expected": str(expected),
                    "actual": str(current),
                }
                violations.append(item)
                if boundary:
                    cross_page_violations.append(item)
        if current is not None:
            previous = current
        previous_page = page
    return {
        "checked": checked,
        "violation_count": len(violations),
        "violations": violations,
        "cross_page_checked": cross_page_checked,
        "cross_page_violation_count": len(cross_page_violations),
        "cross_page_violations": cross_page_violations,
    }


def _repair_gl(document: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repaired = deepcopy(document)
    entries = repaired.get("entries") or []
    audit: list[dict[str, Any]] = []
    previous = dec(repaired.get("opening_balance"))
    for index, row in enumerate(entries, start=1):
        debit, credit, balance = (
            dec(row.get("debit")),
            dec(row.get("credit")),
            dec(row.get("balance")),
        )
        if previous is not None and balance is not None and ((debit is None) != (credit is None)):
            implied = balance - previous
            observed = (debit or Decimal("0")) - (credit or Decimal("0"))
            if abs(implied - observed) > TOL:
                field = "debit" if implied >= 0 else "credit"
                other = "credit" if field == "debit" else "debit"
                before = row.get(field) or row.get(other)
                row[field], row[other] = money(abs(implied)), ""
                audit.append(
                    {
                        "row": index,
                        "field": field,
                        "from": before,
                        "to": row[field],
                        "basis": "adjacent printed balance delta",
                        "review_required": True,
                    }
                )
                debit, credit = dec(row.get("debit")), dec(row.get("credit"))
        if balance is None and previous is not None and (debit is not None or credit is not None):
            balance = previous + (debit or Decimal("0")) - (credit or Decimal("0"))
            row["balance"] = money(balance)
            audit.append(
                {
                    "row": index,
                    "field": "balance",
                    "value": row["balance"],
                    "basis": "forward balance chain",
                }
            )
        elif balance is not None and previous is not None and debit is None and credit is None:
            delta = balance - previous
            field = "debit" if delta >= 0 else "credit"
            row[field] = money(abs(delta))
            audit.append(
                {
                    "row": index,
                    "field": field,
                    "value": row[field],
                    "basis": "forward balance delta",
                }
            )
        if balance is not None:
            previous = balance

    closing = dec(repaired.get("closing_balance"))
    next_balance = closing
    for offset in range(len(entries) - 1, -1, -1):
        row = entries[offset]
        balance = dec(row.get("balance"))
        if balance is not None:
            next_balance = balance
            continue
        if offset + 1 >= len(entries) or next_balance is None:
            continue
        following = entries[offset + 1]
        debit, credit = dec(following.get("debit")), dec(following.get("credit"))
        if debit is None and credit is None:
            continue
        value = next_balance - (debit or Decimal("0")) + (credit or Decimal("0"))
        row["balance"] = money(value)
        audit.append(
            {
                "row": offset + 1,
                "field": "balance",
                "value": row["balance"],
                "basis": "backward balance chain",
            }
        )
        next_balance = value
    return repaired, audit


def _header_anchors(rows: Sequence[RowBox]) -> dict[int, dict[str, float]]:
    aliases = {
        "debit": ("debit", "เดบิต"),
        "credit": ("credit", "เครดิต"),
        "balance": ("balance", "ยอดคงเหลือ", "คงเหลือ"),
    }
    output: dict[int, dict[str, float]] = {}
    for row in rows:
        matches: dict[str, float] = {}
        for token in row.tokens:
            normalized = norm_text(token.text)
            for field, words in aliases.items():
                if any(norm_text(word) in normalized for word in words):
                    matches[field] = token.xc
        # A label such as "Balance Forward" is data, not a table header.  Only
        # a physical row carrying at least two known column labels may define
        # column anchors.
        if len(matches) >= 2:
            output.setdefault(row.page, {}).update(matches)
    return output


def parse_gl(
    rows: Sequence[RowBox], pages: int
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    document: dict[str, Any] = {
        "account_name": "",
        "account_number": "",
        "period_start": "",
        "period_end": "",
        "opening_balance": "",
        "closing_balance": "",
        "printed_total_debit": "",
        "printed_total_credit": "",
        "entries": [],
    }
    audit: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    anchors = _header_anchors(rows)
    raw_rows: list[dict[str, Any]] = []
    last_date = ""

    for row in rows:
        compact = norm_text(row.text)
        amounts = _money_tokens(row)
        if "balanceforward" in compact or "ยอดยกมา" in compact:
            opening_pair = (
                amounts[-1]
                if amounts
                else next(
                    (
                        (token, Decimal("0"))
                        for token in reversed(row.tokens)
                        if re.fullmatch(r"[-+]?0(?:[.,]00)?", token.text.strip())
                    ),
                    None,
                )
            )
            if opening_pair:
                document["opening_balance"] = money(opening_pair[1])
                audit.append(
                    {
                        "field": "opening_balance",
                        "value": document["opening_balance"],
                        "basis": "labeled OCR row",
                        "source": row.as_source(),
                    }
                )
            continue

        transaction_date = norm_date(row.text)
        account_tokens = [
            token
            for token in row.tokens
            if re.fullmatch(r"(?:[A-Za-z]\d{3,}|\d{5,})", token.text.replace(" ", ""))
            and not DATE_RE.fullmatch(token.text)
        ]
        if not transaction_date and account_tokens and amounts and last_date:
            transaction_date = last_date
        if transaction_date:
            last_date = transaction_date
        if not transaction_date or not account_tokens or not amounts:
            continue

        account_token = account_tokens[-1]
        page_anchors = anchors.get(row.page, {})
        balance_pair: tuple[TokenBox, Decimal] | None
        if len(amounts) == 1:
            token = amounts[0][0]
            labeled_columns = {
                field: x
                for field, x in page_anchors.items()
                if field in {"debit", "credit", "balance"}
            }
            nearest = (
                min(labeled_columns, key=lambda field: abs(token.xc - labeled_columns[field]))
                if labeled_columns
                else ""
            )
            # The proven Mistral GL parser treats a lone trailing number as an
            # amount.  Coordinates may override that only when the token is
            # explicitly closest to the printed Balance header.
            balance_pair = amounts[0] if nearest == "balance" else None
        else:
            balance_pair = min(
                amounts,
                key=lambda pair: abs(pair[0].xc - page_anchors.get("balance", amounts[-1][0].xc)),
            )
        balance_token = balance_pair[0] if balance_pair else None
        balance = balance_pair[1] if balance_pair else None
        remaining = [pair for pair in amounts if pair is not balance_pair]
        debit = credit = amount = None
        if remaining:
            amount_token, amount = remaining[-1]
            if "debit" in page_anchors and "credit" in page_anchors:
                if abs(amount_token.xc - page_anchors["debit"]) <= abs(
                    amount_token.xc - page_anchors["credit"]
                ):
                    debit = amount
                else:
                    credit = amount
            elif len(remaining) >= 2:
                debit, credit = remaining[-2][1], remaining[-1][1]
                amount = debit if credit is None else credit if debit is None else None
        excluded = (
            [account_token]
            + ([balance_token] if balance_token else [])
            + [token for token, _ in remaining]
        )
        description = _without_structural_tokens(row, excluded)
        words = description.split()
        raw_rows.append(
            {
                "page": str(row.page),
                "transaction_date": transaction_date,
                "transaction_date_raw": (
                    DATE_RE.search(row.text).group(0) if DATE_RE.search(row.text) else ""
                ),
                "voucher_no": words[0] if words else "",
                "account_code": account_token.text.replace(" ", ""),
                "description": description,
                "amount": amount,
                "debit": debit,
                "credit": credit,
                "balance": balance,
                "source": row,
            }
        )

    direction_votes: dict[str, dict[str, int]] = {}
    for row in raw_rows:
        direction = (
            "debit"
            if row["debit"] is not None and row["credit"] is None
            else "credit" if row["credit"] is not None and row["debit"] is None else ""
        )
        if direction:
            votes = direction_votes.setdefault(row["account_code"], {"debit": 0, "credit": 0})
            votes[direction] += 1

    previous = dec(document.get("opening_balance"))
    for index, row in enumerate(raw_rows, start=1):
        amount, balance = row["amount"], row["balance"]
        direction = (
            "debit"
            if row["debit"] is not None and row["credit"] is None
            else "credit" if row["credit"] is not None and row["debit"] is None else ""
        )
        if not direction and previous is not None and amount is not None and balance is not None:
            delta = balance - previous
            if abs(abs(delta) - amount) <= TOL:
                direction = "debit" if delta >= 0 else "credit"
                audit.append(
                    {
                        "row": index,
                        "field": "direction",
                        "value": direction,
                        "basis": "adjacent printed balance delta",
                    }
                )
                direction_votes.setdefault(row["account_code"], {"debit": 0, "credit": 0})[
                    direction
                ] += 1
        if not direction and amount is not None:
            votes = direction_votes.get(row["account_code"], {})
            if votes:
                direction = "debit" if votes.get("debit", 0) >= votes.get("credit", 0) else "credit"
                audit.append(
                    {
                        "row": index,
                        "field": "direction",
                        "value": direction,
                        "basis": "same-account observed column vote",
                    }
                )
        debit = amount if direction == "debit" else row["debit"]
        credit = amount if direction == "credit" else row["credit"]
        if balance is None and previous is not None and (debit is not None or credit is not None):
            balance = previous + (debit or Decimal("0")) - (credit or Decimal("0"))
            audit.append(
                {
                    "row": index,
                    "field": "balance",
                    "value": money(balance),
                    "basis": "forward balance chain",
                }
            )
        entry = {
            "page": row["page"],
            "transaction_date": row["transaction_date"],
            "transaction_date_raw": row["transaction_date_raw"],
            "voucher_no": row["voucher_no"],
            "account_code": row["account_code"],
            "description": row["description"],
            "debit": money(debit) if debit is not None else "",
            "credit": money(credit) if credit is not None else "",
            "balance": money(balance) if balance is not None else "",
        }
        document["entries"].append(entry)
        provenance.append({"row": index, "source": row["source"].as_source()})
        if balance is not None:
            previous = balance

    if dec(document.get("opening_balance")) is None and document["entries"]:
        first = document["entries"][0]
        balance = dec(first.get("balance"))
        debit, credit = dec(first.get("debit")), dec(first.get("credit"))
        if balance is not None and (debit is not None or credit is not None):
            opening = balance - (debit or Decimal("0")) + (credit or Decimal("0"))
            document["opening_balance"] = money(opening)
            audit.append(
                {
                    "field": "opening_balance",
                    "value": document["opening_balance"],
                    "basis": "first transaction reverse chain",
                }
            )
    if document["entries"]:
        document["closing_balance"] = document["entries"][-1]["balance"]
    repaired, repair_audit = _repair_gl(document)
    audit.extend(repair_audit)
    return repaired, audit, provenance
