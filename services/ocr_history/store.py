# -*- coding: utf-8 -*-
"""OCR 识别历史(ocr_history 表)· 数据访问层门面(REFACTOR-WA · 按读/写域拆叶子)

原 798 行按域拆为:
  - queries.py  · 读取半边:list_ocr_history / get_ocr_history_detail /
                  get_history_pdf_info / find_ocr_by_hash / check_duplicate_invoice
  - hash_dedup.py · 文件哈希批量去重查询:find_ocr_by_hashes(R2B 跨单去重)
  - mutations.py · 写入半边:_extract_summary_fields / update_ocr_history_pages /
                  delete_ocr_history / delete_ocr_history_with_pdf_paths / insert_ocr_history

此处 re-export 回 services.ocr_history.store 命名空间(纯结构搬家 · 0 逻辑改)→
db.py / dal_reexports 经此暴露同一对象,db.xxx() / store.xxx() / from db import 调用点零改。
"""

from services.ocr_history.queries import (  # noqa: F401
    list_ocr_history,
    get_ocr_history_detail,
    get_history_pdf_info,
    find_ocr_by_hash,
    check_duplicate_invoice,
)
from services.ocr_history.hash_dedup import find_ocr_by_hashes  # noqa: F401
from services.ocr_history.agent_overview import docs_overview  # noqa: F401
from services.ocr_history.mutations import (  # noqa: F401
    _extract_summary_fields,
    update_ocr_history_pages,
    commit_staged_ocr_history,
    delete_ocr_history,
    delete_ocr_history_with_pdf_paths,
    insert_ocr_history,
    update_ocr_history_pdf_storage,
    update_history_official_name,
)
