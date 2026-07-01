# -*- coding: utf-8 -*-
"""MR.ERP HTTP 直写传输层(S1 · 复活 2026-05 逆向 · 推翻旧铁律 #7)。

MR.ERP = 远程老 PHP 站(mrerp4sme.com)· 单 PHPSESSID / 无 CSRF / 无验证码
→ 可纯 requests 直连,不再靠 Playwright 模拟浏览器(脆且慢)。

对外只暴露 MrErpHttpAdapter,公开接口与 Playwright 版 MRERPAdapter 一致
(`__enter__/__exit__` + `upload_invoice_batch(histories, mappings) -> ImportResult`),
故经开关 MRERP_TRANSPORT=http 在 build_mrerp_adapter 一处切换即可,下游零改动。
"""

from services.erp.mrerp_http.adapter import MrErpHttpAdapter

__all__ = ["MrErpHttpAdapter"]
