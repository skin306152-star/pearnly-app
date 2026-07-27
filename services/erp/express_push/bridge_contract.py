# -*- coding: utf-8 -*-
"""桥端消费契约的镜像:桥收什么键、桥读哪些键。**逐字抄自桥仓,不是我们自己的设计**。

为什么必须单独立一份镜像:云端与桥端各有一套"契约冻结"测试,但两套都在照自己的镜子 ——
云端断言「组装产物 ⊆ 云端自己的常量」,桥端断言「白名单 == 桥端测试里的自家副本」,
中间没有任何一处把云端产物喂给桥端去看。P2-B 实测结果就是四类下行路径**一类都走不通**:
三类被载荷白名单当场 bad_payload,唯一过白名单的手工凭证死在 INVALID_DOC_DATE
(云端发佛历 docdate_be,桥端读公历 voucher_date),而两边的闸全绿。

镜像的三张表各挡一刀:
  BRIDGE_ACCEPTED_KEYS   桥 `cloud_jobs._ALL_WRITE_PAYLOAD_KEYS` —— 顶层键超出即整单拒
  BRIDGE_REQUIRED_KEYS   桥 `writepath/doc_*.validate` 硬要的顶层键 —— 缺一个即拒单
  BRIDGE_REQUIRED_ROW_KEYS 桥逐行读的子表键 —— 名字不对不报错,是**静默丢字段**

来源(逐字抄自 pearnly-companion,只读,不在本仓改桥):
  `bridge/cloud_jobs.py` 的 `_WRITE_PAYLOAD_KEYS` / `_DOC_PAYLOAD_KEYS`
  `bridge/writepath/doc_{receipt,payment,journal,stock_adjust}.py` 的 `validate` / `_plan_*`

同步方式(**桥端改了这里也要跟着改**,否则这份镜像会开始放行桥端已经不认的载荷):
  改完这里跑 `python -m unittest tests.unit.test_express_bridge_contract`。有桥仓的机器上
  `test_mirror_matches_bridge_whitelist_exactly` 会把镜像与桥端白名单逐键对等比一次,抄漏
  当场红;没有桥仓的机器(CI)比不了 —— 所以谁改契约谁在本机跑,别指望 CI 兜。

改这里的唯一合法理由是桥端真的改了(且桥已发版、装机量滚完)。反过来云端想加键:先去桥
仓登记 + bump 桥版本 + 发版,再回来改这份镜像 —— 桥不随主站 webhook 部署,顺序反了就是
一段"云端已上线、桥还认不得"的空窗。
"""

from __future__ import annotations

# 桥端 bridge/cloud_jobs.py `_WRITE_PAYLOAD_KEYS`(express payload v1 全集,采购/销项老路)。
_BRIDGE_V1_KEYS = frozenset(
    {
        "payload_version",
        "direction",
        "doctype",
        "account_set",
        "docdate_be",
        "vat_period_be",
        "ref_no",
        # 「知道了,还是推」· 会计确认后放行落第二张(桥端 writepath/duplicate_gate)。
        # 云端目前不发这个键 —— 镜像照抄是为了让「桥收什么」这份表保持完整,
        # 少一个键会让下次对镜比出假差异,而不是挡住什么。
        "duplicate_confirmed",
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

# 桥端 bridge/cloud_jobs.py `_DOC_PAYLOAD_KEYS`(会计手录四类单据)。
_BRIDGE_DOC_KEYS = frozenset(
    {
        "doc_type",
        "userid",
        "depcod",
        # 收款
        "receipt_date",
        "customer_code",
        "allocations",
        "allow_unallocated",
        "wht_amount",
        "wht_isrun_zr_prefix",
        "shortfall_amount",
        "output_vat_on_receipt",
        # 付款
        "payment_date",
        "supplier_code",
        "payee_code",
        "settlements",
        "withholding",
        "input_vat_on_payment",
        # 收付款共用
        "channels",
        "advance",
        # 手工凭证
        "voucher_date",
        "journal_code",
        "voucher_no",
        "description",
        "vat",
        # 库存调整
        "doc_date",
        "subtype",
        "isrun_prefix",
        "loccod",
        "remark",
        "offset_account",
    }
)

# 桥端 `cloud_jobs._ALL_WRITE_PAYLOAD_KEYS`:顶层键不在这个并集里 = 整单 bad_payload。
BRIDGE_ACCEPTED_KEYS = _BRIDGE_V1_KEYS | _BRIDGE_DOC_KEYS

# 桥端 `writepath/doc_*.validate` 逐个点名要的顶层键(缺 = DocValidation.ok False)。
# 收款的 allocations 严格说可以空(挂账收款须显式 allow_unallocated),但正常单据必带,
# 缺它就说明云端根本没在发这个字段名 —— 这里钉的是"字段名对不对",不是"能不能空"。
BRIDGE_REQUIRED_KEYS = {
    "ar_receipt": frozenset(
        {"doc_type", "account_set", "receipt_date", "customer_code", "allocations", "channels"}
    ),
    "ap_payment": frozenset(
        {"doc_type", "account_set", "payment_date", "supplier_code", "settlements", "channels"}
    ),
    "gl_journal": frozenset(
        {"doc_type", "account_set", "voucher_date", "journal_code", "description", "lines"}
    ),
    "stock_adjust": frozenset(
        {"doc_type", "account_set", "doc_date", "isrun_prefix", "remark", "lines"}
    ),
}

# 桥端逐行读的子表键。这一层比顶层更凶:桥端对子表用 `.get()`,名字不对不抛错,
# 而是当"没给"处理 —— 渠道前缀丢了会 ACCOUNT_NOT_RESOLVED,批号丢了会挑错来源批,
# 都不是当场炸,是几个月后成本对不上。
BRIDGE_REQUIRED_ROW_KEYS = {
    "ar_receipt": {
        "channels": frozenset({"isrun_zr_prefix", "kind", "amount"}),
        "allocations": frozenset({"doc_no", "rectyp", "amount"}),
    },
    "ap_payment": {
        "channels": frozenset({"isrun_zp_prefix", "amount", "is_cheque"}),
        "settlements": frozenset({"doc_no", "rectyp", "amount"}),
    },
    "gl_journal": {"lines": frozenset({"account", "side", "amount"})},
    "stock_adjust": {"lines": frozenset({"stock_code", "qty", "unit_price"})},
}

# 桥端逐**对象**(不是数组)读的嵌套键。与上面同一类风险,但顶层键存在就骗过了
# BRIDGE_REQUIRED_KEYS —— 收款的预收腿科目、带税凭证的税期都藏在这一层。
BRIDGE_REQUIRED_NESTED_KEYS = {
    "ar_receipt": {"advance": frozenset({"doc_no", "amount", "isrun_zr_prefix"})},
    "ap_payment": {"withholding": frozenset({"tax_type", "tax_amount", "base_amount", "tax_rate"})},
    "gl_journal": {"vat": frozenset({"vat_rec", "vat_period", "base_amount", "vat_amount"})},
    "stock_adjust": {},
}

# 桥端读、但云端只在某个条件下才发的顶层键(条件成立却没发 = 桥端当场拒单)。
# 值是「触发条件的说明」,给读代码的人看的;机械闸在 test_express_bridge_contract。
BRIDGE_CONDITIONAL_KEYS = {
    "ar_receipt": {"wht_isrun_zr_prefix": "wht_amount > 0"},
}

DOC_TYPES = tuple(BRIDGE_REQUIRED_KEYS)
