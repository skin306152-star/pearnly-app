# -*- coding: utf-8 -*-
"""汇总表列角色识别 · 全仓单一事实源(泰/英/中表头 → 列下标)。

零依赖叶子模块:录入工作台(summary_import)与工单 R2 销项聚合
(services/workorder/steps/reconcile_gates)共用这一份词典与算法,不各写一套。
前端 src/home/dms-intake-batch.ts 的 GUESS 是同一份词典的镜像,以本模块为准。

算法 = 最长命中优先的贪心配对:每个表头只归一个角色,每个角色只占一列。
「先从左找第一个命中关键词的列」那种朴素扫描在真实客户版式上会静默错列——冰厂 7-11
月度汇总表头 `วันที่ | ยอด | ราคา | ยอดเงินก่อน vat | ยอดเงิน vat | ยอดเงินรวม` 里,裸
关键词 `vat` 先撞上税前列「ยอดเงินก่อน vat」、裸 `ยอด` 先撞上数量列「ยอด」,于是销售额取成
数量之和、销项税取成税前之和,还一路 used=True 不报错。最长命中让「ยอดเงินก่อน」(11 字)
压过「vat」(3 字),角色独占让数量列不再抢销售额位。
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# 泰文组合符号(上/下元音与声调,零宽)+ 空白。pdfplumber 从 PDF 文字层抽表头时按 x 坐标
# 排序,而这些符号零宽、x 定位在下一个字符右侧,于是被排到基字符之后——真件冰厂 7-11 PDF
# 里「ยอดเงินก่อน vat」抽出来是「ยอดเงนิ กอ่ น vat」,子串匹配全部落空,销项与销售额直接对调。
# Unicode 归一化(NFC/NFD/NFKC)救不了(实测三种全无效),故匹配前双侧剥符号比骨架:
# 剥完两者逐字相同,而不同角色的骨架仍互不相同,优先级(长度序)也原样保持。
_THAI_MARKS = re.compile(r"[ัิ-ฺ็-๎\s]")

DATE = "date"
QUANTITY = "quantity"
UNIT_PRICE = "unit_price"
SUBTOTAL = "subtotal"
VAT = "vat"
TOTAL = "total"

# 角色识别关键词(全小写子串匹配)。同一角色的复合词必须比别的角色的裸词长,长度即优先级:
# 「ยอดเงิน vat」(vat)压过「ยอด」(quantity),「ยอดเงินก่อน」(subtotal)压过「vat」。
# 新增关键词前先想清楚它会不会成为另一角色复合词的子串——那会把优先级翻过来。
GUESS: Dict[str, List[str]] = {
    DATE: ["date", "วันที่", "日期"],
    QUANTITY: ["qty", "quantity", "จำนวน", "ปริมาณ", "ยอด", "数量"],
    UNIT_PRICE: ["unit price", "price", "ราคา", "单价"],
    SUBTOTAL: [
        "subtotal",
        "sub total",
        "before vat",
        "excl vat",
        "excluding vat",
        "net amount",
        "sales amount",
        "sales",
        "ก่อน vat",
        "ก่อนแวต",
        "ก่อนภาษี",
        "ยอดเงินก่อน",
        "ยอดขาย",
        "จำนวนเงิน",
        "มูลค่า",
        "税前",
        "净额",
    ],
    VAT: [
        "vat amount",
        "tax amount",
        "vat",
        "tax",
        "ภาษีขาย",
        "ภาษีมูลค่าเพิ่ม",
        "ภาษี",
        "ยอดเงิน vat",
        "แวต",
        "税额",
    ],
    TOTAL: [
        "grand total",
        "total amount",
        "total",
        "incl vat",
        "including vat",
        "ยอดเงินรวม",
        "รวมทั้งสิ้น",
        "รวมเงิน",
        "ยอดรวม",
        "รวม",
        "总额",
        "合计",
    ],
}

ROLES = (DATE, QUANTITY, UNIT_PRICE, SUBTOTAL, VAT, TOTAL)


def skeleton(text: str) -> str:
    """表头骨架:小写 + 剥泰文组合符号与空白。PDF 文字层的声调错位只动符号不动辅音骨架。"""
    return _THAI_MARKS.sub("", str(text or "").lower())


def _score(header: str, keywords: List[str]) -> int:
    """表头对某角色的命中分 = 命中的最长关键词骨架长度;没命中为 0。

    分数用骨架长度而非原词长度,两侧同尺度,复合词压过裸词的优先级不受剥符号影响。
    """
    low = skeleton(header)
    return max((len(s) for s in (skeleton(kw) for kw in keywords) if s and s in low), default=0)


def detect_columns(headers: List[str]) -> Dict[str, Optional[int]]:
    """表头列表 → {角色: 列下标|None}。返回值总是含全部 ROLES 键(未识别的为 None)。

    贪心:所有 (角色, 列, 分) 候选按分降序,先到先得,角色与列各自只用一次。同分时按
    (角色声明序, 列序) 稳定裁决——让结果与表头顺序无关的抖动绝迹,便于测试钉死。
    """
    cells = [str(h or "").strip() for h in headers]
    candidates = []
    for role_rank, role in enumerate(ROLES):
        for idx, cell in enumerate(cells):
            score = _score(cell, GUESS[role])
            if score:
                candidates.append((-score, role_rank, idx, role))
    candidates.sort()

    out: Dict[str, Optional[int]] = {role: None for role in ROLES}
    taken: set = set()
    for _score_key, _rank, idx, role in candidates:
        if out[role] is not None or idx in taken:
            continue
        out[role] = idx
        taken.add(idx)
    return out
