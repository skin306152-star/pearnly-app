"""
v115 · Searchable PDF 生成模块

把图片 PDF (jsPDF 拍照生成的那种) + Gemini 已识别的文字 → 带不可见文字层的可搜索 PDF。

核心特性:
- 视觉跟原图 100% 一致(文字层 invisible · render_mode=3)
- 用户在 WPS / Adobe / Chrome 里 Ctrl+F 能搜
- 选中能复制(虽然位置不精确 · 但能拿到字符串)
- 泰文字符通过 Noto Sans Thai TTF 注入支持
- 失败不阻塞主流程 · 返回 None 让上层用原始 PDF

依赖:
- pip: pymupdf (fitz) >= 1.23
- system: fonts-noto-thai or fonts-thai-tlwg(Ubuntu apt 装)

性能:
- 一张 5MB image-PDF · 处理 + 重压缩 · 大概 200-500ms
- PyMuPDF 默认 garbage=4 + deflate · 输出文件通常会比原始 image-PDF 小
"""

import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# 优先用支持泰文的 unicode 字体(必须按可用顺序排)
THAI_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-VariableFont_wdth,wght.ttf",
    "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
    "/usr/share/fonts/truetype/tlwg/Loma.ttf",
    "/usr/share/fonts/truetype/tlwg/Norasi.ttf",
]

_thai_font_path: Optional[str] = None
for _p in THAI_FONT_CANDIDATES:
    if Path(_p).exists():
        _thai_font_path = _p
        logger.info(f"📝 v115 · using thai font: {_p}")
        break

if not _thai_font_path:
    logger.warning(
        "⚠️ v115 · 未找到泰文字体(noto / tlwg)· 泰文搜索可能不可用。"
        "建议:apt install fonts-noto-thai fonts-thai-tlwg"
    )


def extract_searchable_text_from_pages(pages: list) -> List[str]:
    """
    从 OCR 结果的 pages 提取每页用于搜索的文本。

    Returns:
        每页一个字符串 · 长度 == len(pages)
    """
    out = []
    for p in pages or []:
        parts = []
        # raw_text 优先(Vision fallback 流程会有)
        rt = p.get("raw_text")
        if rt and isinstance(rt, str):
            parts.append(rt.strip())
        # 字段也加进去 · 强化关键搜索能力
        f = p.get("fields") or {}
        for key in [
            "invoice_number",
            "invoice_no",
            "date",
            "due_date",
            "total_amount",
            "subtotal",
            "vat_amount",
            "seller_name",
            "seller_tax",
            "seller_address",
            "seller_phone",
            "buyer_name",
            "buyer_tax",
            "buyer_address",
            "po_number",
            "reference_no",
        ]:
            v = f.get(key)
            if v is None:
                continue
            sv = str(v).strip()
            if sv:
                parts.append(sv)
        # items 行项目
        items = f.get("items") or []
        if isinstance(items, list):
            for it in items:
                if not isinstance(it, dict):
                    continue
                for k in ["description", "name", "qty", "unit_price", "amount"]:
                    v = it.get(k)
                    if v is not None:
                        sv = str(v).strip()
                        if sv:
                            parts.append(sv)
        out.append(" ".join(parts))
    return out


def make_searchable_pdf(image_pdf_bytes: bytes, pages_texts: List[str]) -> Optional[bytes]:
    """
    把 image-PDF + 每页文字 → searchable PDF。

    Args:
        image_pdf_bytes: 原 image-PDF 字节流(jsPDF 生成的那种)
        pages_texts: 每页对应的搜索文字 · len 通常应 == 页数 · 不等也兼容

    Returns:
        新 PDF 字节流(invisible 文字层 + 重压缩)· 失败返回 None
    """
    if not image_pdf_bytes:
        return None
    try:
        import fitz  # PyMuPDF · 延迟 import 避免模块加载失败
    except ImportError as e:
        logger.error(f"v115 · PyMuPDF 未安装 · {e}")
        return None

    try:
        doc = fitz.open(stream=image_pdf_bytes, filetype="pdf")
        n_pages = len(doc)
        n_text = 0
        if n_pages == 0:
            # 退化/空 PDF · 没法做搜索层 · 直接返 None(caller 用原文件)· 防 tobytes "no objects"
            doc.close()
            logger.warning("v115 · make_searchable_pdf: 0 页 · 跳过搜索层")
            return None

        for page_idx in range(n_pages):
            text = ""
            if page_idx < len(pages_texts):
                text = (pages_texts[page_idx] or "").strip()
            if not text:
                continue

            page = doc[page_idx]
            rect = page.rect

            # 优先用泰文字体 · 失败 fallback helv
            inserted = False
            if _thai_font_path:
                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontsize=2,
                        render_mode=3,  # invisible · 不可见但可搜索/复制
                        fontfile=_thai_font_path,
                        fontname="thai",
                    )
                    inserted = True
                    n_text += 1
                except Exception as e:
                    logger.debug(f"v115 · thai font failed page {page_idx}: {e}")

            if not inserted:
                # fallback · helv 字体(英数字 OK · 泰文会被丢弃 · 但仍是 invisible)
                try:
                    page.insert_textbox(
                        rect,
                        text,
                        fontsize=2,
                        render_mode=3,
                        fontname="helv",
                    )
                    n_text += 1
                except Exception as e:
                    logger.warning(f"v115 · helv fallback failed page {page_idx}: {e}")

        # garbage=4 + deflate · 重压缩 · 通常输出比原始更小
        try:
            out_bytes = doc.tobytes(garbage=4, deflate=True)
        except Exception as _tb:
            # 个别退化 PDF garbage 回收报 "no objects found" · 退回不回收的简单导出
            logger.warning(f"v115 · tobytes(garbage) 失败 · 退回简单导出: {_tb}")
            out_bytes = doc.tobytes()
        doc.close()

        old_kb = len(image_pdf_bytes) // 1024
        new_kb = len(out_bytes) // 1024
        logger.info(
            f"✅ v115 · searchable PDF · {n_text}/{n_pages} pages indexed · "
            f"{old_kb}KB → {new_kb}KB"
        )
        return out_bytes
    except Exception as e:
        # 非致命:搜索层做不出就用原文件 · 降级为 warning 不刷 ERROR
        logger.warning(f"v115 · make_searchable_pdf 跳过(用原文件): {e}")
        return None


def health_check() -> dict:
    """启动检查 · 确认 PyMuPDF 可用 + 字体在"""
    info = {
        "pymupdf_available": False,
        "thai_font": _thai_font_path,
    }
    try:
        import fitz

        info["pymupdf_available"] = True
        info["pymupdf_version"] = getattr(fitz, "__version__", "unknown")
    except Exception:
        pass
    return info


# v115 · 让 `python pdf_searchable.py` 直接跑健康检查
# 部署后用法: /opt/mrpilot/venv/bin/python /opt/mrpilot/pdf_searchable.py
if __name__ == "__main__":
    import json

    print(json.dumps(health_check(), indent=2, ensure_ascii=False))
