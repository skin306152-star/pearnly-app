"""Geometry-based extraction ported from the validated September 3 pilot."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Sequence

TOL = Decimal("0.01")


@dataclass(frozen=True)
class TokenBox:
    page: int
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float | None
    start: int | None
    end: int | None

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def height(self) -> float:
        return max(self.y1 - self.y0, 0.001)

    def as_layout(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "bbox": [round(self.x0, 6), round(self.y0, 6), round(self.x1, 6), round(self.y1, 6)],
            "confidence": self.confidence,
            "text_anchor": [self.start, self.end],
        }


@dataclass(frozen=True)
class RowBox:
    page: int
    text: str
    tokens: tuple[TokenBox, ...]
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2

    def as_source(self) -> dict[str, Any]:
        confidences = [token.confidence for token in self.tokens if token.confidence is not None]
        return {
            "page": self.page,
            "text": self.text,
            "bbox": [round(self.x0, 6), round(self.y0, 6), round(self.x1, 6), round(self.y1, 6)],
            "min_token_confidence": min(confidences) if confidences else None,
        }

    def as_layout(self) -> dict[str, Any]:
        value = self.as_source()
        value["tokens"] = [token.as_layout() for token in self.tokens]
        return value


def _camel_or_snake(mapping: dict[str, Any], camel: str, snake: str) -> Any:
    return mapping.get(camel, mapping.get(snake))


def _text_segments(layout: dict[str, Any]) -> list[tuple[int, int]]:
    anchor = _camel_or_snake(layout, "textAnchor", "text_anchor") or {}
    raw = _camel_or_snake(anchor, "textSegments", "text_segments") or []
    segments = []
    for segment in raw:
        try:
            start = int(_camel_or_snake(segment, "startIndex", "start_index") or 0)
            end = int(_camel_or_snake(segment, "endIndex", "end_index"))
        except (TypeError, ValueError):
            continue
        segments.append((start, end))
    return segments


def _anchor_text(full_text: str, layout: dict[str, Any]) -> str:
    return "".join(full_text[start:end] for start, end in _text_segments(layout))


def _bbox(layout: dict[str, Any], page: dict[str, Any]) -> tuple[float, float, float, float]:
    poly = _camel_or_snake(layout, "boundingPoly", "bounding_poly") or {}
    vertices = _camel_or_snake(poly, "normalizedVertices", "normalized_vertices") or []
    normalized = bool(vertices)
    if not vertices:
        vertices = poly.get("vertices") or []
    if not vertices:
        return (0.0, 0.0, 1.0, 1.0)

    dimension = page.get("dimension") or {}
    try:
        width = float(dimension.get("width") or 1)
        height = float(dimension.get("height") or 1)
    except (TypeError, ValueError):
        width = height = 1.0
    xs: list[float] = []
    ys: list[float] = []
    for vertex in vertices:
        try:
            x = float(vertex.get("x") or 0)
            y = float(vertex.get("y") or 0)
        except (TypeError, ValueError):
            continue
        xs.append(x if normalized else x / max(width, 1))
        ys.append(y if normalized else y / max(height, 1))
    if not xs or not ys:
        return (0.0, 0.0, 1.0, 1.0)
    return (min(xs), min(ys), max(xs), max(ys))


def _layout_range(layout: dict[str, Any]) -> tuple[int | None, int | None]:
    segments = _text_segments(layout)
    if not segments:
        return None, None
    return min(start for start, _ in segments), max(end for _, end in segments)


def _token_boxes(
    document: dict[str, Any], page: dict[str, Any], page_number: int
) -> list[TokenBox]:
    full_text = str(document.get("text") or "")
    output = []
    for token in page.get("tokens") or []:
        layout = token.get("layout") or {}
        text = _anchor_text(full_text, layout).strip()
        if not text:
            text = str(token.get("text") or "").strip()
        if not text:
            continue
        x0, y0, x1, y1 = _bbox(layout, page)
        start, end = _layout_range(layout)
        try:
            confidence = (
                float(layout["confidence"]) if layout.get("confidence") is not None else None
            )
        except (TypeError, ValueError):
            confidence = None
        output.append(TokenBox(page_number, text, x0, y0, x1, y1, confidence, start, end))
    return output


def _overlaps_anchor(token: TokenBox, start: int | None, end: int | None) -> bool:
    if None in (token.start, token.end, start, end):
        return False
    assert (
        token.start is not None and token.end is not None and start is not None and end is not None
    )
    return token.start < end and token.end > start


def _merge_token_groups(groups: list[list[TokenBox]]) -> list[list[TokenBox]]:
    if not groups:
        return []
    heights = [
        max(token.y1 for token in group) - min(token.y0 for token in group) for group in groups
    ]
    median_height = statistics.median(heights) if heights else 0.01
    clusters: list[dict[str, Any]] = []
    for group in sorted(groups, key=lambda item: sum(token.yc for token in item) / len(item)):
        yc = sum(token.yc for token in group) / len(group)
        y0 = min(token.y0 for token in group)
        y1 = max(token.y1 for token in group)
        chosen = None
        for cluster in reversed(clusters[-4:]):
            vertical_overlap = min(y1, cluster["y1"]) - max(y0, cluster["y0"])
            tolerance = max(0.004, median_height * 0.60)
            overlap_ratio = vertical_overlap / max(
                min(y1 - y0, cluster["y1"] - cluster["y0"]), 0.001
            )
            # Perspective makes cells on the right sit a few pixels lower than
            # cells on the left.  Centre proximity handles that.  Any positive
            # overlap is not enough: on photographed receipts adjacent slanted
            # rows overlap by 1-2 pixels and would otherwise chain into one
            # enormous row.
            if abs(yc - cluster["yc"]) <= tolerance or overlap_ratio >= 0.55:
                chosen = cluster
                break
        if chosen is None:
            clusters.append({"tokens": list(group), "yc": yc, "y0": y0, "y1": y1})
            continue
        chosen["tokens"].extend(group)
        chosen["y0"] = min(chosen["y0"], y0)
        chosen["y1"] = max(chosen["y1"], y1)
        chosen["yc"] = (chosen["y0"] + chosen["y1"]) / 2

    output = []
    for cluster in clusters:
        unique: dict[tuple[Any, ...], TokenBox] = {}
        for token in cluster["tokens"]:
            key = (
                token.start,
                token.end,
                round(token.x0, 5),
                round(token.y0, 5),
                token.text,
            )
            unique[key] = token
        output.append(sorted(unique.values(), key=lambda token: (token.x0, token.y0)))
    return output


def _line_rows(document: dict[str, Any], page: dict[str, Any], page_number: int) -> list[RowBox]:
    tokens = _token_boxes(document, page, page_number)
    rows: list[RowBox] = []
    for line in page.get("lines") or []:
        layout = line.get("layout") or {}
        start, end = _layout_range(layout)
        members = [token for token in tokens if _overlaps_anchor(token, start, end)]
        if not members:
            text = _anchor_text(str(document.get("text") or ""), layout).strip()
            if not text:
                continue
            x0, y0, x1, y1 = _bbox(layout, page)
            members = [TokenBox(page_number, text, x0, y0, x1, y1, None, start, end)]
        members = sorted(members, key=lambda token: (token.x0, token.y0))
        text = " ".join(token.text.strip() for token in members if token.text.strip())
        rows.append(
            RowBox(
                page_number,
                text,
                tuple(members),
                min(token.x0 for token in members),
                min(token.y0 for token in members),
                max(token.x1 for token in members),
                max(token.y1 for token in members),
            )
        )
    if not rows:
        rows = [
            RowBox(token.page, token.text, (token,), token.x0, token.y0, token.x1, token.y1)
            for token in tokens
        ]
    return sorted(rows, key=lambda row: (row.yc, row.x0))


def _visual_rows(
    document: dict[str, Any],
    page: dict[str, Any],
    page_number: int,
    line_rows: Sequence[RowBox] | None = None,
) -> list[RowBox]:
    physical = list(line_rows) if line_rows is not None else _line_rows(document, page, page_number)
    groups = [list(row.tokens) for row in physical]

    rows = []
    for row_tokens in _merge_token_groups(groups):
        if not row_tokens:
            continue
        text = " ".join(token.text.strip() for token in row_tokens if token.text.strip())
        rows.append(
            RowBox(
                page_number,
                text,
                tuple(row_tokens),
                min(token.x0 for token in row_tokens),
                min(token.y0 for token in row_tokens),
                max(token.x1 for token in row_tokens),
                max(token.y1 for token in row_tokens),
            )
        )
    return sorted(rows, key=lambda row: (row.y0, row.x0))


def _table_rows(
    document: dict[str, Any], page: dict[str, Any], page_number: int
) -> list[dict[str, Any]]:
    """Return native Document AI table cells without flattening row geometry."""

    full_text = str(document.get("text") or "")
    tokens = _token_boxes(document, page, page_number)
    tables: list[dict[str, Any]] = []
    for table in page.get("tables") or []:
        converted: dict[str, Any] = {
            "page": page_number,
            "bbox": _bbox(table.get("layout") or {}, page),
            "header_rows": [],
            "body_rows": [],
        }
        for source_name, target_name in (("headerRows", "header_rows"), ("bodyRows", "body_rows")):
            for source_row in table.get(source_name) or []:
                cells: list[RowBox] = []
                for cell in source_row.get("cells") or []:
                    layout = cell.get("layout") or {}
                    start, end = _layout_range(layout)
                    members = [token for token in tokens if _overlaps_anchor(token, start, end)]
                    text = _anchor_text(full_text, layout).strip()
                    if members:
                        members = sorted(members, key=lambda token: (token.x0, token.y0))
                        if not text:
                            text = " ".join(token.text for token in members)
                        x0 = min(token.x0 for token in members)
                        y0 = min(token.y0 for token in members)
                        x1 = max(token.x1 for token in members)
                        y1 = max(token.y1 for token in members)
                    else:
                        x0, y0, x1, y1 = _bbox(layout, page)
                        members = [TokenBox(page_number, text, x0, y0, x1, y1, None, start, end)]
                    cells.append(RowBox(page_number, text, tuple(members), x0, y0, x1, y1))
                if cells:
                    converted[target_name].append(cells)
        tables.append(converted)
    return tables


def _unwrap_documents(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error = payload["error"]
        raise RuntimeError(
            f"Document AI response is an error: HTTP {error.get('code', '?')} "
            f"{error.get('status', '')} {error.get('message', '')}".strip()
        )
    if isinstance(payload, dict) and isinstance(payload.get("document"), dict):
        return [payload["document"]]
    if isinstance(payload, dict) and "text" in payload and "pages" in payload:
        return [payload]
    if isinstance(payload, dict) and isinstance(payload.get("response"), dict):
        return _unwrap_documents(payload["response"])
    if isinstance(payload, dict) and isinstance(payload.get("responses"), list):
        output = []
        for response in payload["responses"]:
            output.extend(_unwrap_documents(response))
        return output
    if isinstance(payload, list):
        output = []
        for item in payload:
            output.extend(_unwrap_documents(item))
        return output
    raise ValueError("JSON does not contain a Document AI document")


def rows_from_payloads(
    payloads: Sequence[dict[str, Any]],
) -> tuple[list[RowBox], list[RowBox], list[dict[str, Any]], dict[str, Any]]:
    rows: list[RowBox] = []
    lines: list[RowBox] = []
    tables: list[dict[str, Any]] = []
    page_number = 0
    token_count = 0
    for payload in payloads:
        for document in _unwrap_documents(payload):
            for page in document.get("pages") or []:
                page_number += 1
                page_lines = _line_rows(document, page, page_number)
                page_rows = _visual_rows(document, page, page_number, page_lines)
                token_count += sum(len(row.tokens) for row in page_rows)
                lines.extend(page_lines)
                rows.extend(page_rows)
                tables.extend(_table_rows(document, page, page_number))
    return (
        rows,
        lines,
        tables,
        {
            "pages": page_number,
            "visual_rows": len(rows),
            "physical_lines": len(lines),
            "tables": len(tables),
            "tokens": token_count,
        },
    )
