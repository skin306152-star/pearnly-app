# -*- coding: utf-8 -*-
"""
services/ocr/schemas.py · OCR 管线共享 Pydantic schema 门面(REFACTOR-WA · R20)

原 879 行按域拆为 schemas_layer1(基础原语)/ schemas_documents(非发票文档)/
schemas_invoice(发票)/ schemas_results(各层结果)· 此处 re-export 回 services.ocr.schemas
命名空间 → 所有 `from .schemas import X` / `from services.ocr.schemas import X` 调用点零改。
"""

from services.ocr.schemas_layer1 import *  # noqa: F401,F403
from services.ocr.schemas_documents import *  # noqa: F401,F403
from services.ocr.schemas_invoice import *  # noqa: F401,F403
from services.ocr.schemas_results import *  # noqa: F401,F403

# 显式带出 import * 跳过的私有 helper / 类型别名(下游可能引用)
from services.ocr.schemas_layer1 import BusinessDocumentType  # noqa: F401
from services.ocr.schemas_documents import NonInvoiceDocument  # noqa: F401
from services.ocr.schemas_invoice import _coerce_to_str, _coerce_to_optional_str  # noqa: F401
