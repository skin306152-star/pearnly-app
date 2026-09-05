"""Generic grid extraction shared by the image bridge."""

from services.fileconv.model import (
    GENERIC_TABLE,
    STATUS_OCR_INCOMPLETE,
    STATUS_OCR_UNAVAILABLE,
    STATUS_OK,
    ConvertResult,
    Table,
)


def convert_generic(images, source_name, ocr_doc_type, call, tenant_id, api_key):
    from services.fileconv.ocr_bridge import _read_page, _reject, _DOC_TYPE_TO_FILECONV

    """非台账/流水类:忠实抽网格,不假装能勾稽任意表(issues 为空 = 无守恒可判,诚实)。"""
    headers = []
    grid = []
    for image_bytes in images:
        page = _read_page(image_bytes, "generic_table", call, tenant_id, api_key)
        if not page.ok:
            status = STATUS_OCR_INCOMPLETE if page.incomplete else STATUS_OCR_UNAVAILABLE
            return _reject(status, source_name, "OCR 未能读出可用网格")
        doc = page.document
        if not headers and doc.headers:
            headers = list(doc.headers)
        for row in doc.rows:
            grid.append([row.get(h, "") for h in headers] if headers else list(row.values()))
    table = Table(name="Table", columns=headers or ["col1"], rows=grid)
    return ConvertResult(
        doc_type=_DOC_TYPE_TO_FILECONV.get(ocr_doc_type, GENERIC_TABLE),
        status=STATUS_OK,
        source_name=source_name,
        tables=[table],
        issues=[],
        stats={"row_count": len(grid), "engine": "ocr_image_direct", "pages": len(images)},
    )
