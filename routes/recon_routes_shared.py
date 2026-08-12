# -*- coding: utf-8 -*-
"""recon 路由跨组共享 helper（user key + 计费页数口径）· recon_routes 拆分。"""

from typing import List, Tuple


def _user_key(user):
    return (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip() or None


_ROWS_PER_PAGE_BILLING = 40  # v0.58 · 居中计费:一页约 40 笔 · 防密集账单按页低估


def _pdf_billing_units(page_count: int, row_count: int) -> int:
    """v118.35.0.58 · 银行对账 PDF/图片计费『页数』· 居中口径 max(实际页数, ⌈行数/N⌉)。
    对齐 ฿1.5/页规则 · 修复此前误按交易行数计费(超收 10-34 倍)的 bug。
    既不让多页大账单超收 · 也不让一页塞很多笔的密集账单被低估 · 图片=1 页。"""
    import math as _m

    pages = max(1, int(page_count or 0))
    rows = max(0, int(row_count or 0))
    return max(pages, _m.ceil(rows / _ROWS_PER_PAGE_BILLING))


# 事后扣费的「字符」档扩展名(与 charge_ocr_async 调用点逐字一致)· 预检按同一组切分。
_EXCEL_BILLING_EXTS = {".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".doc"}


def _file_ext(filename: str) -> str:
    return ("." + (filename or "").lower().rsplit(".", 1)[-1]) if "." in (filename or "") else ""


def estimate_recon_units(files: List[Tuple[bytes, str]]) -> Tuple[int, int]:
    """估算对账批的计费单位 (pdf_units, excel_chars) · 预检估价用。

    PDF/图片按件 1 页(与既有预检口径一致,这里只补 Excel/CSV 的字符折算);
    Excel/CSV 字符文件走 _excel_char_count_estimate 便宜的结构读取。估值口径 =
    解析前文本量,与事后实扣的解析后字符数可能有小偏差;预检从宽,不加安全系数。
    """
    from core import db as _db

    pdf_units = 0
    excel_chars = 0
    for b, fn in files or []:
        if _file_ext(fn) in _EXCEL_BILLING_EXTS:
            excel_chars += int(_db._excel_char_count_estimate(b, fn) or 0)
        else:
            pdf_units += 1
    return pdf_units, excel_chars


async def estimate_upload_units(uploads) -> Tuple[int, int]:
    """UploadFile 版估算单位:只读 Excel/CSV 类文件的字节做字符估算 · 读后 seek(0) 还原,
    不干扰后续 _stage_uploads / 解析重读。PDF/图片不读(按件 1 页)。"""
    from core import db as _db

    pdf_units = 0
    excel_chars = 0
    for u in uploads or []:
        fn = getattr(u, "filename", None) or ""
        if _file_ext(fn) in _EXCEL_BILLING_EXTS:
            content = await u.read()
            excel_chars += int(_db._excel_char_count_estimate(content, fn) or 0)
            await u.seek(0)
        else:
            pdf_units += 1
    return pdf_units, excel_chars
