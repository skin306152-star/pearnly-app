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

# 会计手录四类单据(P2-B)· 逐 direction 冻结键集。与上面 v1 的两条老路分开列,不合并:
# 老路的键集是老小助手在生产消费的东西,往里塞新键会让"这个键该不该出现在采购载荷里"
# 无从判断。
#
# ⚠️ 这张表只管"云端自己产什么",判不了对错 —— 判对错的是 bridge_contract.py 里桥端
# 消费契约的镜像(BRIDGE_ACCEPTED_KEYS / BRIDGE_REQUIRED_KEYS)。两张表都要过,缺一个
# 就回到 P2-B 那种"自己验自己全绿、真实下行路径一类都走不通"的假绿。
DOCTYPE_PAYLOAD_KEYS = {
    "ar_receipt": frozenset(
        {
            "payload_version",
            "direction",
            "doc_type",
            "doctype",
            "account_set",
            "receipt_date",
            "customer_code",
            "wht_amount",
            "wht_isrun_zr_prefix",
            "shortfall_amount",
            "allocations",
            "channels",
            "advance",
            "allow_unallocated",
            "userid",
            "depcod",
            "prior_docnum",
            "source",
        }
    ),
    "ap_payment": frozenset(
        {
            "payload_version",
            "direction",
            "doc_type",
            "doctype",
            "account_set",
            "payment_date",
            "supplier_code",
            "payee_code",
            "wht_amount",
            "settlements",
            "channels",
            "withholding",
            "userid",
            "depcod",
            "prior_docnum",
            "source",
        }
    ),
    "gl_journal": frozenset(
        {
            "payload_version",
            "direction",
            "doc_type",
            "doctype",
            "account_set",
            "voucher_date",
            "journal_code",
            "voucher_no",
            "description",
            "total_amount",
            "lines",
            "vat",
            "userid",
            "source",
        }
    ),
    "stock_adjust": frozenset(
        {
            "payload_version",
            "direction",
            "doc_type",
            "doctype",
            "subtype",
            "account_set",
            "doc_date",
            "isrun_prefix",
            "loccod",
            "remark",
            "offset_account",
            "lines",
            "userid",
            "depcod",
            "prior_docnum",
            "source",
        }
    ),
}
