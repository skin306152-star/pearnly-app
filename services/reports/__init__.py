# -*- coding: utf-8 -*-
"""跨模块报表适配层(N1 · 导航三门商业级完善 P0-3)。

只做"数据形状适配"——把已经算好的月度报表(services/workorder 的 r6_financials
只读投影)转换成 services/fileconv 引擎认识的 Table/ConvertResult,复用它的
PDF/Excel 渲染,不重算一个钱字段,不碰 services/workorder 内部实现。
"""

from services.reports.financials_pdf import build_financials_convert_result

__all__ = ["build_financials_convert_result"]
