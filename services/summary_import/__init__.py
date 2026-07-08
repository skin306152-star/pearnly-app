# -*- coding: utf-8 -*-
"""汇总表 → 批量建单(录入工作台第三卡)。

场景:客户只给一份月度汇总(冰厂给 7-11 的销售汇总),没有逐单发票。把汇总表 + 用户补的
已知字段(客户/税号/商品/付款方式/单号规则)转成 Pearnly 能建单(purchase_docs/sales_documents)
且能推 ERP(ocr_history)的数据,不走 OCR。

分层(单一职责):
  parse   — 二进制 xlsx/csv → 表头 + 行(复用 recon 的通用表格 I/O leaf 工具)
  mapping — 列映射 + 批次常量 → 每行规范化 fields(F 契约 schema)+ 甲乙方落位
  judge   — 复用 ERP 侧现成税号锚点判方向 + 付款判现金/赊账,产出「有数据自动/无数据兜底」结论
  commit  — 每行:建账本草稿(采购/销项)+ 写 ocr_history(推送读源),逐行独立不连坐
"""
