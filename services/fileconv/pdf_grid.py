# -*- coding: utf-8 -*-
"""PDF → 规整二维网格(行 × 列)· 三级降级链。

真实客户 PDF 的列位靠什么切开,取决于导出链留下了什么痕迹,一条路走不通:

  L1 extract_tables  pdfplumber 默认(lines/rect)策略。Excel/报表工具导出的 PDF 把单元格
                     边框画成 rect,默认策略吃这些边,切得逐格精确 —— 首选。
  L2 坐标聚类        无框线 PDF 走这条:top 聚行,x 投影空隙聚列。列边界必须用「投影空隙」
                     而不是单侧边缘 —— 破折号 `-` 是居中对齐,右边缘比同列数字左偏 9~10pt,
                     按 x1 聚类会把它甩出所有列(同一个错列 bug 换个形式复发)。
  L3 空白切分        fileconv.tables._split_cells(2+ 空格 / 泰数字边框)。最后兜底:列间只有
                     单空格的 PDF 它一刀切不开(整行返 1 格),故不能当主路。

**不用 text 策略**:实测 {"vertical_strategy":"text","horizontal_strategy":"text"} 会把表头切碎、
把金额从中间劈开('252,373.60 3,857' / ',710.80'),比不切还糟。

缺值一律 ""(空串),由取数方按「缺值跳过、绝不当 0」处理 —— 合并单元格给 None、无销售日给
'-',把它们读成 0 会让合计交叉校验产生假差额。
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

LEVEL_TABLE = "extract_tables"
LEVEL_CLUSTER = "coordinate_cluster"
LEVEL_SPLIT = "whitespace_split"

_MIN_COLUMNS = 2
_MIN_ROWS = 2
# 同一行的字词纵向抖动容差(pt)。报表行距远大于此,不会把相邻行并进来。
_ROW_TOL = 3.0
# 列间空隙阈值(pt)。破折号居中对齐时边缘可偏 9~10pt,阈值必须够大才不把它切成独立列;
# 又必须小于真实列距。5pt ≈ 半个字宽,是两者之间的安全带。
_COL_GAP = 5.0


@dataclass(frozen=True)
class Grid:
    """规整矩形网格。rows 每行长度相同,缺值为 ""。level 记录靠哪一级切开的(降级留痕)。"""

    rows: List[List[str]]
    level: str

    @property
    def degraded(self) -> bool:
        """没走成主路 = 列位可信度下降,上层据此标注/降级,不假装一样可靠。"""
        return self.level != LEVEL_TABLE


def _cell(value) -> str:
    return "" if value is None else str(value).replace("\n", " ").strip()


def _rectangular(rows: List[List[str]], level: str, *, pad_left: bool = False) -> Optional[Grid]:
    """补齐成矩形并做最低结构校验;撑不起表 → None。

    pad_left 决定短行往哪边补空:L1/L2 的格子本身就带列位,短行是真的右侧缺列,往右补;
    L3 靠空白切分,前置空列根本不产生格子(合计行只剩「合计 + 三个金额」),必须往左补才不
    把金额整体左移一格。补错的那一侧由合计行交叉校验兜底点名。
    """
    rows = [r for r in rows if any(c for c in r)]
    if len(rows) < _MIN_ROWS:
        return None
    width = max(len(r) for r in rows)
    if width < _MIN_COLUMNS:
        return None
    pad = (
        (lambda r: [""] * (width - len(r)) + r)
        if pad_left
        else (lambda r: r + [""] * (width - len(r)))
    )
    return Grid(rows=[pad(r) for r in rows], level=level)


def _from_extract_tables(pdf) -> Optional[Grid]:
    """L1:默认(lines/rect)策略。多页多表按序拼接——月度汇总跨页是同一张表。"""
    rows: List[List[str]] = []
    for page in pdf.pages:
        for table in page.extract_tables() or []:
            rows.extend([_cell(c) for c in row] for row in table)
    return _rectangular(rows, LEVEL_TABLE)


def _column_bands(words) -> List[tuple]:
    """x 投影空隙聚列 → [(左, 右)] 列区间。把所有字词的 [x0,x1] 投到一条轴上,
    间隙 < _COL_GAP 的合并,剩下的空隙即列边界。"""
    spans = sorted((float(w["x0"]), float(w["x1"])) for w in words)
    bands: List[list] = []
    for x0, x1 in spans:
        if bands and x0 - bands[-1][1] < _COL_GAP:
            bands[-1][1] = max(bands[-1][1], x1)
        else:
            bands.append([x0, x1])
    return [(lo, hi) for lo, hi in bands]


def _band_of(word, bands: List[tuple]) -> int:
    """字词归哪一列:取重叠最多的列区间(居中/右对齐都吃得住,不看单侧边缘)。"""
    x0, x1 = float(word["x0"]), float(word["x1"])
    overlaps = [min(x1, hi) - max(x0, lo) for lo, hi in bands]
    return max(range(len(bands)), key=lambda i: overlaps[i])


def _rows_by_top(words) -> List[list]:
    """top 坐标聚行(同一基线的字词归一行),行内按 x0 排序。"""
    lines: List[list] = []
    for w in sorted(words, key=lambda w: (float(w["top"]), float(w["x0"]))):
        if lines and abs(float(w["top"]) - float(lines[-1][0]["top"])) <= _ROW_TOL:
            lines[-1].append(w)
        else:
            lines.append([w])
    return lines


def _from_coordinates(pdf) -> Optional[Grid]:
    """L2:无框线 PDF 的坐标重建。逐页各自聚列(不同页版式可能不同),行按 top 聚。"""
    rows: List[List[str]] = []
    for page in pdf.pages:
        words = page.extract_words() or []
        if not words:
            continue
        bands = _column_bands(words)
        if len(bands) < _MIN_COLUMNS:
            continue
        for line in _rows_by_top(words):
            cells = [""] * len(bands)
            for w in line:
                i = _band_of(w, bands)
                cells[i] = f"{cells[i]} {w['text']}".strip() if cells[i] else str(w["text"])
            rows.append(cells)
    return _rectangular(rows, LEVEL_CLUSTER)


def _from_whitespace(pages: Optional[List[str]]) -> Optional[Grid]:
    """L3:空白切分兜底。切不开(整行一格)时 _rectangular 的列数下限会挡下来。"""
    from services.fileconv.tables import _split_cells

    rows = [_split_cells(line) for page in pages or [] for line in page.split("\n")]
    return _rectangular([r for r in rows if r], LEVEL_SPLIT, pad_left=True)


def extract_grid(pdf_bytes: bytes, *, pages_text: Optional[List[str]] = None) -> Optional[Grid]:
    """PDF 字节 → Grid;三级都切不出表 → None(交调用方诚实降级,绝不返半张表)。

    pages_text 是已抽好的文字层(调用方常已抽过),只给 L3 用,省一次重复解析。
    """
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber 未安装 · 无法切表")
        return _from_whitespace(pages_text)

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes or b"")) as pdf:
            return (
                _from_extract_tables(pdf) or _from_coordinates(pdf) or _from_whitespace(pages_text)
            )
    except Exception as e:  # noqa: BLE001 · 坏 PDF/缺字体都只是「切不出」,不该炸调用方
        logger.info("PDF 切表失败 · %s: %s", type(e).__name__, e)
        return _from_whitespace(pages_text)
