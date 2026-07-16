# -*- coding: utf-8 -*-
"""盘点(纯函数):上传后即出的零成本分组摘要,零 AI 成本、零 OCR。

复用工单 sort 步的零成本信号(services/workorder/steps/sort._bin_by_file)——它是「按文件名/
扩展名/表头当场定堆」的唯一事实源(图片/银行流水/销售汇总/GL/不支持格式),前门盘点不另写
一套判据,只把它的结论翻成盘点卡的展示分组。传了真实盘上路径时表头判据(xlsx 流水/GL 标题行)
自动生效;只有文件名时按扩展名归组,不读盘(纯函数默认路径)。

「不认识」项(不支持格式/无名 PDF/图片)= 需确认后详细识别,不是错误:诚实列数,不吞不炸
(§二 2.3 盘点卡:认出 N / 不认识 M)。深度 OCR 在 confirm 开工单后才跑,盘点阶段不承诺识别结果。
"""

from __future__ import annotations

from pathlib import Path

from services.workorder import kinds
from services.workorder.steps import sort as sort_step

# 盘点卡展示分组(前端按 key 出四语文案 + 计数)。与工单 kind 不是同一命名空间:kind 是
# 「一件料本身是什么」,这里是「盘点卡怎么把它归堆给人看」——图片/无名 PDF 在工单里 kind
# 仍 unknown(待 OCR),盘点卡按「像票据的图片 / 待识别 PDF」分开列,信息量更高。
IMAGE = "image"  # 图片,可能是票据
BANK_STATEMENT = "bank_statement"  # 银行流水(文件名/表头认出)
SPREADSHEET = "spreadsheet"  # 表格(Excel/CSV,可能是销售汇总)
GL_LEDGER = "gl_ledger"  # GL 台账(佐证件)
PDF_UNIDENTIFIED = "pdf_unidentified"  # PDF,待详细识别
UNRECOGNIZED = "unrecognized"  # 不支持格式/打不开,确认后也识别不了

# 展示顺序:先「认出」的高信号组,再「待识别 / 不认识」,与盘点卡自上而下阅读一致。
GROUP_ORDER = (
    IMAGE,
    BANK_STATEMENT,
    SPREADSHEET,
    GL_LEDGER,
    PDF_UNIDENTIFIED,
    UNRECOGNIZED,
)

_IMAGE_EXTS = sort_step.IMAGE_EXTS


def classify(file_ref: str) -> str:
    """单件料 → 盘点展示分组(零成本)。file_ref 可为纯文件名(不读盘)或真实盘上路径
    (xlsx 表头判据随之生效)。归组口径全部委托 sort._bin_by_file,前门不重复判据。"""
    decided = sort_step._bin_by_file(file_ref)
    if decided is None:
        # sort 留给 classify 过 OCR 的两类:图片 / 无名 PDF。盘点卡分开列。
        ext = Path(file_ref or "").suffix.lower()
        return IMAGE if ext in _IMAGE_EXTS else PDF_UNIDENTIFIED
    kind = decided[0]
    if kind == kinds.GL_LEDGER:
        return GL_LEDGER
    if kind == kinds.BANK_STATEMENT:
        return BANK_STATEMENT
    if kind == kinds.SALES_SUMMARY:
        return SPREADSHEET
    return UNRECOGNIZED  # non_tax / 不支持格式


def summarize(file_refs) -> dict:
    """一批料 → 盘点摘要:{"groups": [{"group","count","names"}...按 GROUP_ORDER],
    "total","recognized","unrecognized"}。空批返回全零结构(四态诚实,不返 None)。"""
    buckets: dict[str, list[str]] = {}
    for ref in file_refs or []:
        name = Path(ref or "").name
        buckets.setdefault(classify(ref), []).append(name)

    groups = [
        {"group": g, "count": len(buckets[g]), "names": buckets[g]}
        for g in GROUP_ORDER
        if buckets.get(g)
    ]
    total = sum(len(v) for v in buckets.values())
    unrecognized = len(buckets.get(UNRECOGNIZED, []))
    return {
        "groups": groups,
        "total": total,
        "recognized": total - unrecognized,
        "unrecognized": unrecognized,
    }
