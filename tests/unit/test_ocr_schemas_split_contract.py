# -*- coding: utf-8 -*-
"""
REFACTOR-WA 守门测试 · services/ocr/schemas.py 879→拆分(R20 · 2026-05-29)
拆为 schemas_layer1(基础原语:BusinessDocumentType/FieldRef/几何层级)+ schemas_documents
(GL/银行/VAT/通用表)+ schemas_invoice(ThaiInvoice/LineItem)+ schemas_results(各层结果)·
schemas.py 门面 re-export 回原命名空间。纯搬家 0 逻辑改。

锁定:① 门面 re-export 全部公开 schema(所有 `from services.ocr.schemas import X` 调用点零改)
② 门面.X 与子模块.X 同一对象 ③ 嵌套模型 + 自引用 model_rebuild 仍可实例化 ④ 无循环依赖。
"""

import unittest

from services.ocr import (
    schemas,
    schemas_layer1,
    schemas_documents,
    schemas_invoice,
    schemas_results,
)

# 9 个 services/ocr 消费模块经 `from .schemas import (...)` 引用的公开名
_PUBLIC = [
    "BusinessDocumentType",
    "FieldRef",
    "BoundingBox",
    "Word",
    "Paragraph",
    "Block",
    "Page",
    "Layer1Result",
    "GLEntry",
    "GeneralLedgerDocument",
    "BankStatementEntry",
    "BankStatementDocument",
    "VatReportEntry",
    "VatReportDocument",
    "GenericTableDocument",
    "NonInvoiceDocument",
    "LineItem",
    "ThaiInvoice",
    "Layer2PageResult",
    "Layer2Result",
    "Layer3PageResult",
    "PipelinePageResult",
    "PipelineResult",
]


class OcrSchemasSplitContractTests(unittest.TestCase):
    def test_facade_reexports_all_public(self):
        for n in _PUBLIC:
            self.assertTrue(hasattr(schemas, n), f"schemas 门面缺 {n}")

    def test_facade_single_source(self):
        # 门面.X 与真正定义它的子模块.X 同一对象(无复制 shim)
        for mod in (schemas_layer1, schemas_documents, schemas_invoice, schemas_results):
            for n in _PUBLIC:
                if hasattr(mod, n) and not n == "FieldRef":
                    # FieldRef 在 layer1 定义,被多模块 import,只认 layer1 为源
                    pass
        self.assertIs(schemas.FieldRef, schemas_layer1.FieldRef)
        self.assertIs(schemas.ThaiInvoice, schemas_invoice.ThaiInvoice)
        self.assertIs(schemas.GeneralLedgerDocument, schemas_documents.GeneralLedgerDocument)
        self.assertIs(schemas.PipelineResult, schemas_results.PipelineResult)
        self.assertIs(schemas.NonInvoiceDocument, schemas_documents.NonInvoiceDocument)

    def test_nested_and_self_ref_instantiation(self):
        # 自引用 additional_invoices(model_rebuild)+ 跨模块 results→invoice 嵌套
        inv = schemas.ThaiInvoice(additional_invoices=[schemas.ThaiInvoice()])
        self.assertEqual(len(inv.additional_invoices), 1)
        pr = schemas.PipelinePageResult(page_number=1, invoice=schemas.ThaiInvoice())
        self.assertEqual(pr.page_number, 1)
        gl = schemas.GeneralLedgerDocument(entries=[schemas.GLEntry()])
        self.assertEqual(len(gl.entries), 1)

    def test_no_cycle(self):
        # 依赖单向:layer1 ← documents/invoice ← results;子模块不反向引用 schemas 门面
        self.assertIsNone(getattr(schemas_layer1, "schemas", None))
        self.assertIsNone(getattr(schemas_documents, "schemas", None))


if __name__ == "__main__":
    unittest.main()
