"""PDF rendering for file conversion, preserving every page."""

import logging

logger = logging.getLogger(__name__)


def rasterize_pdf(pdf_bytes: bytes, dpi: int = 144):
    """扫描件 PDF 逐页栅格化为 PNG(消费 PyMuPDF,不碰 OCR 管线)。失败返回 None。"""
    try:
        import fitz  # PyMuPDF
    except ImportError:  # pragma: no cover
        logger.error("ocr_bridge: PyMuPDF (fitz) 未安装 · 无法栅格化扫描件")
        return None
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        return [
            doc.load_page(i).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
            for i in range(doc.page_count)
        ]
    except Exception as e:  # noqa: BLE001
        logger.info("ocr_bridge: 扫描件栅格化失败 · %s: %s", type(e).__name__, e)
        return None
    finally:
        if doc is not None:
            doc.close()
