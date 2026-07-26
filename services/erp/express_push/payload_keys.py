# -*- coding: utf-8 -*-
"""Express 写载荷键契约(冻结 · 与桥端白名单机械对镜)。

桥(pearnly-companion bridge/cloud_jobs.py `_WRITE_PAYLOAD_KEYS`)对写载荷按白名单
当场拒:契约外键 = bad_payload,每一笔桥写活全部熄火,直到桥发新版 —— 桥不随主站
webhook 部署,窗口期以天计。历史上载荷键一直在加(stock_acccod / vat_capitalized /
prior_docnum / opening_stock),靠注释「加键同 PR 去桥登记」的口头约定迟早漏。

契约锁(routing_matrix 同范式):tests/unit/test_express_payload_keys.py 断言两个
mapper + preflight 补键的产物键集 ⊆ 本常量。mapper 新加键 → 测试当场红 → 必须来这里
登记(提交里留下机械痕迹),同时同步桥端 `_WRITE_PAYLOAD_KEYS`(那侧有冻结对镜测试
钉着)并发桥新版,之后才部署云端。
"""

from __future__ import annotations

# express payload v1 全集:build_express_payload / build_express_sales_payload 的
# 固定键 + 条件键(stock_acccod / vat_capitalized / prior_docnum)+ preflight 注入的
# opening_stock + finalize_payload 盖的 payload_version。
WRITE_PAYLOAD_KEYS = frozenset(
    {
        "payload_version",
        "direction",
        "doctype",
        "account_set",
        "docdate_be",
        "vat_period_be",
        "ref_no",
        "supplier",
        "customer",
        "vat_rate",
        "base_amount",
        "vat_amount",
        "total_amount",
        "lines",
        "items",
        "items_status",
        "items_account",
        "items_line_sum",
        "account_source",
        "account_review",
        "doctype_src",
        "doc_lane",
        "item_src",
        "source",
        "stock_acccod",
        "vat_capitalized",
        "prior_docnum",
        "opening_stock",
    }
)
