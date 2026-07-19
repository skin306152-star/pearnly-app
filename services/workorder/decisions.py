# -*- coding: utf-8 -*-
"""工单裁决通道的唯一词汇表(纯常量叶子模块 · 2026-07-10 simplify 收敛)。

裁决动词 / 方向裁定 kind /「不计入合计」语义集 / 方向不明 flag_reason 前缀——此前散在
api.py、reconcile_gates.py、conservation.py、evidence.py 里各自重声明,注释都写「与另一处
同一张表」,但那张表并不存在(改一处极易漏改另一处)。收敛到此成真·单一事实源。

零依赖:不 import 任何本包模块,避免循环导入。api/reconcile_gates/conservation/... 都从这里
取词,本模块绝不反向依赖它们。static/ai/ai-review-queue.js 无法 import,前缀数组旁有同步注释。
"""

from __future__ import annotations

# 裁决动词。金额裁决 face_value/recalc/exclude(W3 的 A/E/X)+ 方向票 assign_kind + 豁免 waive。
FACE_VALUE = "face_value"  # 采信票面 OCR 读数
RECALC = "recalc"  # 人工看原票补正
EXCLUDE = "exclude"  # 剔除,不计入合计
ASSIGN_KIND = "assign_kind"  # 方向不明票的人工定向裁决(带裁定 kind)
WAIVE = "waive"  # 显式放行一件无法归位的料(带 reason,备忘留痕)

# assign_kind 的裁定 kind:进项票 / 销项票 / 非税票 / 银行流水。
PURCHASE_INVOICE = "purchase_invoice"
SALES_DOC = "sales_doc"
NON_TAX = "non_tax"
BANK_STATEMENT = "bank_statement"
ASSIGN_KINDS = (PURCHASE_INVOICE, SALES_DOC, NON_TAX, BANK_STATEMENT)

# 「不计入合计」语义集:剔除与豁免都不进 Σ、不进 unresolved(豁免另在备忘留痕)。
NON_COUNTING = frozenset({EXCLUDE, WAIVE})

# 银行对账 review 清单人审裁决(MC1-b3 · E2 债):accept=采信某候选票为该笔流水的匹配 /
# reject=否掉全部候选。与上面的裁决动词同族(同落 human_decision 事件)但独立成一对——
# 它裁决的对象是银行流水行(statement_tx_id),不是 work_order_item,不共用 item 校验路径。
# 银行对账是佐证层:这对动词绝不进 R1/R2/R4 税额计算,只覆盖 R3 呈现(services/workorder/
# bank_recon_review.py + api._bank_recon 的读侧覆盖)。
BANK_RECON_ACCEPT = "bank_recon_accept"
BANK_RECON_REJECT = "bank_recon_reject"

# 方向不明票的 flag_reason:税号/名称锚点判不出进/销(direction_ambiguous)。kind=unknown,
# 必须人工定向(assign_kind)。SALES_DIRECTION_UNHANDLED 是 MC1-c.1 前「自家==卖方判死」的旧码
# ——现已改为 sort 自动归 sales_doc 堆(见 SALES_DOC_REVIEW),此常量仅为存量工单的 flag_reason
# 向后兼容保留(reconcile 的 ambiguous 收编口径、conservation 的方向判据仍认它)。
DIRECTION_AMBIGUOUS = "direction_ambiguous"
SALES_DIRECTION_UNHANDLED = "sales_direction_unhandled"
DIRECTION_PREFIXES = (DIRECTION_AMBIGUOUS, SALES_DIRECTION_UNHANDLED)

# 自动判定的本方销项票 flag_reason(MC1-c.1):seller==自家税号/名集 → sort 归 SALES_DOC 堆,
# 默认 flagged 留一次人工过目(拍板① · 配 MC1-b 批量键盘流一键确认),不再判死为 unknown。
# 刻意不进 DIRECTION_PREFIXES:它是「机器已判本方销项」而非「方向不明」,reconcile R1 不把它
# 当 unresolved 停机(佐证聚合不阻断出税),人工仍可 assign_kind 改判(客户拍错票的兜底)。
SALES_DOC_REVIEW = "sales_doc_review"
