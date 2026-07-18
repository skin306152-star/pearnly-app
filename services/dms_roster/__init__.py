# -*- coding: utf-8 -*-
"""Pearnly DMS 操作员花名册(波3 · DL-8)。

老板在 /dms 门户维护「操作员=租户下 member 用户」的角色档案:每人自己的 DMS 凭据(各自
erp_endpoints)+ 各自 LINE 绑定(line_dms_bindings)+ 本包的显示名/角色/启停档案。销售只用
LINE,凭据配置只在老板门户(根治「管理员账密对销售可见」)。store=DAL,service=编排。
"""
