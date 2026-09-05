"""Geometry-based extraction ported from the validated September 3 pilot."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from typing import Any

TOL = Decimal("0.01")

from .common import (
    dec,
    money,
)


def _bank_signed(entry: dict[str, Any]) -> Decimal | None:
    direction = entry.get("direction")
    amount = dec(entry.get("amount"))
    if amount is None:
        return None
    if direction == "deposit":
        return abs(amount)
    if direction == "withdrawal":
        return -abs(amount)
    return None


def _set_bank_signed(entry: dict[str, Any], signed: Decimal, *, imputed: bool = True) -> None:
    amount = money(abs(signed))
    if signed > 0:
        entry.update({"deposit": amount, "withdrawal": "", "direction": "deposit"})
    else:
        entry.update({"deposit": "", "withdrawal": amount, "direction": "withdrawal"})
    entry["amount"] = amount
    entry["chain_amount_imputed"] = imputed


def _digit_distance(left: Decimal, right: Decimal) -> int:
    a = str(int(abs(left * 100)))
    b = str(int(abs(right * 100)))
    width = max(len(a), len(b))
    return sum(x != y for x, y in zip(a.zfill(width), b.zfill(width)))


def _bank_residuals(document: dict[str, Any]) -> list[Decimal | None]:
    previous = dec(document.get("opening_balance"))
    output = []
    for entry in document.get("entries") or []:
        signed = _bank_signed(entry)
        balance = dec(entry.get("balance"))
        if previous is None or signed is None or balance is None:
            output.append(None)
        else:
            output.append(previous + signed - balance)
        if balance is not None:
            previous = balance
    return output


def _bank_chain(document: dict[str, Any]) -> dict[str, Any]:
    entries = document.get("entries") or []
    residuals = _bank_residuals(document)
    violations = []
    cross_page_checked = 0
    cross_page_violations = []
    previous_page = None
    checked = 0
    for index, (entry, residual) in enumerate(zip(entries, residuals), start=1):
        page = int(entry.get("page") or 1)
        boundary = previous_page is not None and page != previous_page
        if residual is not None:
            checked += 1
            if boundary:
                cross_page_checked += 1
        if residual is None or abs(residual) > TOL:
            item = {
                "row": index,
                "page": page,
                "residual": str(residual) if residual is not None else None,
            }
            violations.append(item)
            if boundary:
                cross_page_violations.append(item)
        previous_page = page
    return {
        "checked": checked,
        "violation_count": len(violations),
        "violations": violations,
        "cross_page_checked": cross_page_checked,
        "cross_page_violation_count": len(cross_page_violations),
        "cross_page_violations": cross_page_violations,
    }


def _infer_bank_directions(document: dict[str, Any], audit: list[dict[str, Any]]) -> None:
    entries = document.get("entries") or []
    previous = dec(document.get("opening_balance"))
    for index, entry in enumerate(entries, start=1):
        amount, balance = dec(entry.get("amount")), dec(entry.get("balance"))
        if (
            not entry.get("direction")
            and previous is not None
            and amount is not None
            and balance is not None
        ):
            delta = balance - previous
            if delta and abs(abs(delta) - abs(amount)) <= TOL:
                _set_bank_signed(entry, delta, imputed=False)
                audit.append(
                    {
                        "row": index,
                        "field": "direction",
                        "value": entry["direction"],
                        "basis": "adjacent printed balance delta",
                    }
                )
        if balance is not None:
            previous = balance

    if dec(document.get("opening_balance")) is None and entries:
        first_balance = dec(entries[0].get("balance"))
        first_signed = _bank_signed(entries[0])
        if first_balance is not None and first_signed is not None:
            opening = first_balance - first_signed
            document["opening_balance"] = money(opening)
            audit.append(
                {
                    "field": "opening_balance",
                    "value": money(opening),
                    "basis": "first transaction balance minus signed amount",
                }
            )


def _repair_bank(document: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repaired = deepcopy(document)
    entries = repaired.get("entries") or []
    audit: list[dict[str, Any]] = []
    opening = dec(repaired.get("opening_balance"))
    amounts = [
        abs(value) if (value := dec(row.get("amount"))) is not None else None for row in entries
    ]
    balances = [dec(row.get("balance")) for row in entries]
    signs = [
        (
            1
            if row.get("direction") == "deposit"
            else -1 if row.get("direction") == "withdrawal" else None
        )
        for row in entries
    ]
    observed_amounts = list(amounts)
    observed_balances = list(balances)

    for _ in range(8):
        changed = False
        for index in range(len(entries)):
            previous = opening if index == 0 else balances[index - 1]
            amount, balance = amounts[index], balances[index]
            if None in (previous, amount, balance):
                continue
            assert previous is not None and amount is not None and balance is not None
            delta = balance - previous
            if delta and abs(abs(delta) - amount) <= TOL:
                sign = 1 if delta > 0 else -1
                if signs[index] != sign:
                    signs[index] = sign
                    changed = True

        for index in range(len(entries) - 1):
            previous = opening if index == 0 else balances[index - 1]
            current_amount, next_amount = amounts[index], amounts[index + 1]
            next_balance = balances[index + 1]
            if None in (previous, current_amount, next_amount, next_balance):
                continue
            assert previous is not None and current_amount is not None
            assert next_amount is not None and next_balance is not None
            solutions = []
            for current_sign in (-1, 1):
                for next_sign in (-1, 1):
                    middle = previous + current_sign * current_amount
                    if abs(middle + next_sign * next_amount - next_balance) <= TOL:
                        solutions.append((middle, current_sign, next_sign))
            if len(solutions) != 1:
                continue
            middle, current_sign, next_sign = solutions[0]
            if balances[index] is None or abs(balances[index] - middle) > TOL:
                balances[index] = middle
                changed = True
            if signs[index] != current_sign or signs[index + 1] != next_sign:
                signs[index], signs[index + 1] = current_sign, next_sign
                changed = True

        for index in range(len(entries)):
            previous = opening if index == 0 else balances[index - 1]
            if amounts[index] is None and previous is not None and balances[index] is not None:
                delta = balances[index] - previous
                if delta:
                    amounts[index] = abs(delta)
                    signs[index] = 1 if delta > 0 else -1
                    changed = True
        if not changed:
            break

    bad = []
    for index in range(len(entries)):
        previous = opening if index == 0 else balances[index - 1]
        if None in (previous, amounts[index], balances[index], signs[index]):
            bad.append(index)
            continue
        assert previous is not None and amounts[index] is not None
        assert balances[index] is not None and signs[index] is not None
        if abs(previous + signs[index] * amounts[index] - balances[index]) > TOL:
            bad.append(index)

    clusters: list[list[int]] = []
    for index in bad:
        if not clusters or index > clusters[-1][-1] + 1:
            clusters.append([index])
        else:
            clusters[-1].append(index)

    for cluster in clusters:
        left, right = cluster[0], cluster[-1]
        start = opening if left == 0 else balances[left - 1]
        end = balances[right]
        if None in (start, end) or any(
            amounts[index] is None or signs[index] is None for index in range(left, right + 1)
        ):
            continue
        assert start is not None and end is not None
        target = end - start
        current = sum(
            signs[index] * amounts[index]  # type: ignore[operator]
            for index in range(left, right + 1)
        )
        residual = target - current
        alternatives: dict[int, set[Decimal]] = {
            index: {amounts[index]} for index in range(left, right + 1)  # type: ignore[list-item]
        }
        for index in range(left, right + 1):
            assert amounts[index] is not None and signs[index] is not None
            direct = amounts[index] + residual / signs[index]
            if direct > 0:
                alternatives[index].add(direct)
            for segment_left in range(left, index + 1):
                segment_start = (
                    start if segment_left == left else observed_balances[segment_left - 1]
                )
                if segment_start is None:
                    continue
                for segment_right in range(index, right + 1):
                    segment_end = observed_balances[segment_right]
                    if segment_end is None:
                        continue
                    other = sum(
                        signs[position] * amounts[position]  # type: ignore[operator]
                        for position in range(segment_left, segment_right + 1)
                        if position != index
                    )
                    candidate = (segment_end - segment_start - other) / signs[index]
                    if candidate > 0:
                        alternatives[index].add(candidate)

        best: tuple[tuple[int, int, int], list[Decimal]] | None = None
        for first in range(left, right + 1):
            for first_amount in alternatives[first]:
                proposed = [amounts[index] for index in range(left, right + 1)]
                proposed[first - left] = first_amount
                remainder = target - sum(
                    signs[index] * proposed[index - left]  # type: ignore[operator]
                    for index in range(left, right + 1)
                )
                combinations: list[list[Decimal]] = []
                if abs(remainder) <= TOL:
                    combinations.append(proposed)  # type: ignore[arg-type]
                else:
                    for second in range(first + 1, right + 1):
                        candidate = proposed[second - left] + remainder / signs[second]  # type: ignore[operator]
                        if candidate <= 0:
                            continue
                        pair = list(proposed)
                        pair[second - left] = candidate
                        combinations.append(pair)  # type: ignore[arg-type]
                for values in combinations:
                    cursor = start
                    balance_cost = 0
                    amount_cost = 0
                    edits = 0
                    for offset, value in enumerate(values):
                        position = left + offset
                        cursor += signs[position] * value  # type: ignore[operator]
                        observed_balance = observed_balances[position]
                        if observed_balance is not None and abs(cursor - observed_balance) > TOL:
                            balance_cost += _digit_distance(cursor, observed_balance)
                        observed_amount = observed_amounts[position]
                        if observed_amount is not None and abs(value - observed_amount) > TOL:
                            edits += 1
                            amount_cost += _digit_distance(value, observed_amount)
                    score = (edits * 2 + balance_cost * 2 + amount_cost, edits, amount_cost)
                    if best is None or score < best[0]:
                        best = (score, values)
        if best is None:
            continue
        cursor = start
        for offset, value in enumerate(best[1]):
            position = left + offset
            cursor += signs[position] * value  # type: ignore[operator]
            amounts[position] = value
            balances[position] = cursor

    if (
        opening is not None
        and balances
        and balances[-1] is not None
        and all(amount is not None and sign is not None for amount, sign in zip(amounts, signs))
    ):
        net = sum(sign * amount for sign, amount in zip(signs, amounts))  # type: ignore[operator]
        closing_residual = balances[-1] - opening - net
        if Decimal("0") < abs(closing_residual) <= Decimal("0.02"):
            choices = []
            for index, (amount, observed, sign) in enumerate(zip(amounts, observed_amounts, signs)):
                if (
                    amount is None
                    or observed is None
                    or sign is None
                    or abs(amount - observed) <= TOL
                ):
                    continue
                candidate = amount + closing_residual / sign
                if candidate <= 0:
                    continue
                cents = int((candidate * 100) % 100)
                choices.append(
                    ((cents != 0, _digit_distance(candidate, observed)), index, candidate)
                )
            if choices:
                _, index, candidate = min(choices, key=lambda item: item[0])
                amounts[index] = candidate
                cursor = opening if index == 0 else balances[index - 1]
                for position in range(index, len(entries)):
                    if cursor is None or amounts[position] is None or signs[position] is None:
                        break
                    predicted = cursor + signs[position] * amounts[position]
                    if (
                        position != index
                        and balances[position] is not None
                        and abs(predicted - balances[position]) > Decimal("0.02")
                    ):
                        break
                    balances[position] = predicted
                    cursor = predicted
                audit.append(
                    {
                        "row": index + 1,
                        "field": "amount",
                        "value": money(candidate),
                        "basis": "printed opening-to-closing one-satang reconciliation",
                        "review_required": True,
                    }
                )

    for index, row in enumerate(entries):
        amount, balance, sign = amounts[index], balances[index], signs[index]
        if amount is not None and sign is not None:
            before_amount = observed_amounts[index]
            before_direction = row.get("direction")
            _set_bank_signed(row, Decimal(sign) * amount, imputed=before_amount != amount)
            if before_amount is None or abs(before_amount - amount) > TOL:
                row["review_required"] = True
                audit.append(
                    {
                        "row": index + 1,
                        "field": "amount",
                        "from": money(before_amount) if before_amount is not None else "",
                        "to": row["amount"],
                        "basis": "bounded balance-chain equation",
                        "review_required": True,
                    }
                )
            if before_direction != row["direction"]:
                audit.append(
                    {
                        "row": index + 1,
                        "field": "direction",
                        "from": before_direction,
                        "to": row["direction"],
                        "basis": "adjacent printed balance delta",
                    }
                )
        if balance is not None:
            before_balance = observed_balances[index]
            row["balance"] = money(balance)
            if before_balance is None or abs(before_balance - balance) > TOL:
                row["chain_repaired"] = True
                row["review_required"] = True
                audit.append(
                    {
                        "row": index + 1,
                        "field": "balance",
                        "from": money(before_balance) if before_balance is not None else "",
                        "to": row["balance"],
                        "basis": "unique forward/backward balance-chain solution",
                        "review_required": True,
                    }
                )
    if entries:
        repaired["closing_balance"] = entries[-1].get("balance") or ""
    return repaired, audit
