# -*- coding: utf-8 -*-
"""销项聚合引擎(批次 SA-1):非 POS 客户的月度销项权威源候选。

从 EDC 卡机结算单 + 银行入账 + 销售税票/小票倒推按日销售汇总(会计现状人脑干的活),
产出建议月合计与跨渠道关联/冲突/缺口逐笔点名。纯函数域,零 I/O 零 DB;采用与否由
会计在审核队列裁决(SA-2 接线),本包绝不自动拍板。
"""

from services.sales_agg.aggregate import INCLUSION_RULES, aggregate_month

__all__ = ["INCLUSION_RULES", "aggregate_month"]
