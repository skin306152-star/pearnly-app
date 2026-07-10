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

# assign_kind 的裁定 kind:进项票 / 销项票 / 非税票。
PURCHASE_INVOICE = "purchase_invoice"
SALES_DOC = "sales_doc"
NON_TAX = "non_tax"
ASSIGN_KINDS = (PURCHASE_INVOICE, SALES_DOC, NON_TAX)

# 「不计入合计」语义集:剔除与豁免都不进 Σ、不进 unresolved(豁免另在备忘留痕)。
NON_COUNTING = frozenset({EXCLUDE, WAIVE})

# 方向不明票的 flag_reason:税号/名称锚点判不出进/销(direction_ambiguous),或自家命中卖方
# =疑似本方销项票(sales_direction_unhandled)。两者都 kind=unknown,都必须人工定向(assign_kind)。
DIRECTION_AMBIGUOUS = "direction_ambiguous"
SALES_DIRECTION_UNHANDLED = "sales_direction_unhandled"
DIRECTION_PREFIXES = (DIRECTION_AMBIGUOUS, SALES_DIRECTION_UNHANDLED)
