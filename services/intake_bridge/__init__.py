# -*- coding: utf-8 -*-
"""OCR 确认 → 正式单据转换桥(录入工作台「确认」的真正落点)。

问题:录入向导第4步「确认」此前只翻 ocr_history.staged=FALSE(services/ocr_history/
mutations.commit_staged_ocr_history),不落 purchase_docs/sales_documents —— 商品收发存
报表读的正是这两张表(status='posted'/'issued'),"确认完"与"过账完"因此脱节,报表恒空。

本域把确认接上真实建账:convert.py 编排,purchase_leg.py / sales_leg.py 分别处理两条腿。
逐张 history 独立 SAVEPOINT(一张失败不拖累其它张);幂等靠 purchase_docs/sales_documents.
ocr_history_id 的部分唯一索引(alembic 0098)。
"""
