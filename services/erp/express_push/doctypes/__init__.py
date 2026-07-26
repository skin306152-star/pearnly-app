# -*- coding: utf-8 -*-
"""会计手录四类单据(收款/付款/手工凭证/库存调整)的载荷组装 + 写路总闸注册表。

与 mapper.py / sales_mapper.py 两条老路并列、互不干扰:老路吃 OCR 抽取结果推采购/销售票,
这四类吃会计在录入台填的表单。老路的 direction(purchase/sales)与本包的四个 direction
不重叠,桥门面按 direction 分派 —— 老载荷一个字节不变,老小助手照旧消费。

每个模块自带三样东西,桥端照 docstring 消费:
  DIRECTION / DOCTYPE   载荷判别键(direction 唯一,doctype 是它的常量伴生)
  build_*_payload       录入台表单 → 载荷(组装即校验,不闭合就退回填表的人)
  check_payload         写路总闸(重推/回放不经组装器,那条路只过这一道)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from services.erp.express_push.doctypes import ap_payment, ar_receipt, gl_journal, stock_adjust
from services.erp.express_push.doctypes.ap_payment import build_payment_payload
from services.erp.express_push.doctypes.ar_receipt import build_receipt_payload
from services.erp.express_push.doctypes.gl_journal import build_journal_payload
from services.erp.express_push.doctypes.stock_adjust import build_stock_adjust_payload

__all__ = [
    "WRITE_SPECS",
    "DoctypeSpec",
    "build_journal_payload",
    "build_payment_payload",
    "build_receipt_payload",
    "build_stock_adjust_payload",
]


@dataclass(frozen=True)
class DoctypeSpec:
    """一类单据在写路上的身份:direction → 唯一合法 doctype + 该类的总闸。"""

    direction: str
    doctype: str
    check: Callable[[Dict[str, Any]], Optional[str]]


WRITE_SPECS: Dict[str, DoctypeSpec] = {
    module.DIRECTION: DoctypeSpec(module.DIRECTION, module.DOCTYPE, module.check_payload)
    for module in (ar_receipt, ap_payment, gl_journal, stock_adjust)
}
