# -*- coding: utf-8 -*-
"""通用模板学习层(ADR-006)· 新模板不再"解析失败"。

只负责"列映射"(header signature / 本地推断 / 用户确认 / 记忆),产出与 bank_recon_v2
完全兼容的 col_map,交给现有解析+对账逻辑。不重写对账。
"""
