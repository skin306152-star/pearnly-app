# -*- coding: utf-8 -*-
"""Pearnly AI Gateway / Model Router(P2E)。

业务代码只请求一个明确 task(line_text_understand / expense_category_choose / …),Gateway 负责
选供应商、超时、成本、日志;供应商名/模型名/prompt/API key 绝不进用户可见路径(LINE 回复/Flex 卡/
详情页)。第一版默认生产行为不变,只把模型供应商从业务代码解耦。见 docs/line-platform/03。
"""
