# -*- coding: utf-8 -*-
"""路由注册表 —— FastAPI 应用挂哪些 router 的单一来源。

从 app.py 抽出(2026-07-26):入口文件顶到 499/500 行硬上限,再加一条路由就爆闸;而撑满
它的那三百多行全是「import 一个 router + include 一次」的机械清单,与应用装配本身
(lifespan/中间件/异常处理/静态挂载)不是一回事。清单搬到这里,加路由 = 加两行,app.py 恒定瘦。

顺序有意义:FastAPI 按注册顺序匹配,同前缀路由先注册者优先。本表逐条保持搬迁前的顺序;
tests/unit/test_route_registry_contract.py 与 tests/integration/test_core_routes_presence.py
锁「一条不多一条不少、路径全等」。
"""

from __future__ import annotations

import logging
import os

from routes.accounting_bank_routes import router as accounting_bank_router
from routes.accounting_books_routes import router as accounting_books_router
from routes.accounting_routes import router as accounting_router
from routes.admin_agent_routes import router as admin_agent_router
from routes.admin_cost_routes import router as admin_cost_router
from routes.admin_diagnostics_routes import router as admin_diagnostics_router
from routes.admin_dms_routes import router as admin_dms_router
from routes.admin_logs_routes import router as admin_logs_router
from routes.admin_migration_routes import router as admin_migration_router
from routes.admin_ocr_engine_routes import router as admin_ocr_engine_router
from routes.admin_pearnly_ai_routes import router as admin_pearnly_ai_router
from routes.admin_pos_entitlement_routes import router as admin_pos_entitlement_router
from routes.admin_settings_routes import router as admin_settings_router
from routes.admin_users_routes import router as admin_users_router
from routes.auth_email_code_routes import router as auth_email_code_router
from routes.bank_recon_routes import router as bank_recon_router
from routes.billing_routes import router as billing_router
from routes.categories_routes import router as categories_router
from routes.client_import_routes import router as client_import_router
from routes.client_pool_routes import router as client_pool_router
from routes.clients_routes import router as clients_router
from routes.companion_installer_routes import router as companion_installer_router
from routes.console_invite_routes import router as console_invite_router
from routes.console_roles_routes import router as console_roles_router
from routes.console_team_routes import router as console_team_router
from routes.dms_roster_routes import router as dms_roster_router
from routes.dms_routes import router as dms_router
from routes.daily_routes import router as daily_router
from routes.email_ingest_routes import router as email_ingest_router
from routes.erp_agent import router as erp_agent_router
from routes.erp_bridge_routes import router as erp_bridge_router
from routes.erp_mappings_routes import router as erp_mappings_router
from routes.erp_routes import router as erp_router
from routes.exceptions_routes import router as exceptions_router
from routes.export_routes import router as purchase_export_router
from routes.fileconv_routes import router as fileconv_router
from routes.front_desk_routes import router as front_desk_router
from routes.google_oauth_routes import router as google_oauth_router
from routes.history_routes import router as history_router
from routes.import_routes import router as import_router
from routes.inventory_report_routes import router as inventory_report_router
from routes.inventory_routes import router as inventory_router
from routes.line_account_merge_routes import router as line_account_merge_router
from routes.line_binding_routes import router as line_binding_router
from routes.line_card_image_routes import router as line_card_image_router
from routes.line_dms_webhook_routes import router as line_dms_webhook_router
from routes.line_liff_routes import router as line_liff_router
from routes.line_webhook_routes import router as line_webhook_router
from routes.login_routes import router as login_router
from routes.me_routes import router as me_router
from routes.meta_aliases_routes import router as meta_aliases_router
from routes.modules_routes import router as modules_router
from routes.notification_routes import router as notification_router
from routes.oauth_line_routes import router as oauth_line_router
from routes.oauth_routes import router as oauth_router
from routes.ocr_export_routes import router as ocr_export_router
from routes.ocr_jobs_routes import router as ocr_jobs_router
from routes.ocr_recognize_routes import router as ocr_recognize_router
from routes.pages_routes import router as pages_router
from routes.payroll_routes import router as payroll_router
from routes.pos_auth_routes import router as pos_auth_router
from routes.pos_modules_routes import router as pos_modules_router
from routes.pos_payment_routes import router as pos_payment_router
from routes.pos_report_routes import router as pos_report_router
from routes.pos_restaurant_admin_routes import router as pos_restaurant_admin_router
from routes.pos_restaurant_routes import router as pos_restaurant_router
from routes.pos_sales_log_routes import router as pos_sales_log_router
from routes.pos_sales_routes import router as pos_sales_router
from routes.pos_sheets_routes import router as pos_sheets_router
from routes.pos_taxinv_routes import router as pos_taxinv_router
from routes.pos_shift_routes import router as pos_shift_router
from routes.products_routes import router as products_router
from routes.purchase_config_routes import router as purchase_config_router
from routes.purchase_intake_routes import router as purchase_intake_router
from routes.purchase_routes import router as purchase_router
from routes.rd_routes import router as rd_router
from routes.recon_jobs_routes import router as recon_jobs_router
from routes.recon_routes import router as recon_router
from routes.report_routes import router as reports_router
from routes.sales_routes import router as sales_router
from routes.sales_seller_routes import router as sales_seller_router
from routes.sales_send_routes import router as sales_send_router
from routes.sales_settings_routes import router as sales_settings_router
from routes.security_routes import router as security_router
from routes.settings_routes import router as settings_router
from routes.steward_routes import router as steward_router
from routes.steward_session_routes import router as steward_session_router
from routes.steward_stream_routes import router as steward_stream_router
from routes.stock_card_routes import router as stock_card_router
from routes.summary_import_routes import router as summary_import_router
from routes.supplier_posting_routes import router as supplier_posting_router
from routes.tax_profile_routes import router as tax_profile_router
from routes.tax_routes import router as tax_router
from routes.tenant_routes import router as tenant_router
from routes.uploads_routes import router as uploads_router
from routes.vat_excel_routes import router as vat_excel_router
from routes.vat_report_checks_routes import router as vat_report_checks_router
from routes.workorder_bank_sales_routes import router as workorder_bank_sales_router
from routes.workorder_financials_routes import router as workorder_financials_router
from routes.workorder_review_routes import router as workorder_review_router
from routes.workorder_routes import router as workorder_router
from routes.workspace_routes import router as workspace_router
from services.auth.auth_signup import router as signup_router

logger = logging.getLogger("mr-pilot")

# 注册顺序 = 匹配优先级,逐条沿用搬迁前的顺序,别按字母重排。
ROUTERS = (
    reports_router,
    security_router,  # CSP 违规上报 /api/csp-report
    ocr_recognize_router,
    signup_router,
    recon_router,  # 销项税对账
    vat_excel_router,  # Excel 公式对账内测(skin306152 only)
    vat_report_checks_router,  # 销项税报告三查
    fileconv_router,  # 财务文件转换(pearnly_ai_m1 闸)
    payroll_router,  # ภ.ง.ด.1 工资预扣工具卡(pearnly_ai_m1 闸)
    notification_router,
    clients_router,
    products_router,
    modules_router,  # GET /api/me/modules
    inventory_router,
    inventory_report_router,
    pos_auth_router,
    pos_sales_router,
    pos_shift_router,  # 开/交班(连号+审计)
    pos_report_router,  # 报表 + 交接班台账
    pos_sales_log_router,  # 交易明细日志 + CSV 导出
    pos_taxinv_router,  # 补开全式税票(税号带出 + 发票 PDF · G2)
    pos_modules_router,
    pos_restaurant_router,
    pos_restaurant_admin_router,
    pos_payment_router,
    pos_sheets_router,  # Google Sheet 留档设置
    purchase_router,
    purchase_intake_router,
    summary_import_router,  # 汇总表 → 批量建单
    purchase_export_router,  # 进项外流 Excel/Drive/Sheet 导出
    google_oauth_router,  # 集成中心 Google Drive/Sheets 授权
    line_liff_router,
    purchase_config_router,
    supplier_posting_router,  # 供应商过账档案 CRUD(零 UI)
    accounting_router,
    accounting_books_router,
    accounting_bank_router,
    stock_card_router,  # 商品收发存报表(Stock Card · 移动加权平均 · accounting 模块闸)
    tax_router,
    sales_router,
    sales_seller_router,
    sales_settings_router,
    sales_send_router,
    uploads_router,
    console_team_router,
    console_invite_router,
    console_roles_router,
    erp_mappings_router,
    email_ingest_router,
    rd_router,  # 泰国 RD 税务
    workspace_router,
    client_import_router,  # 客户名录批量导入
    workorder_router,  # 工单制 API(pearnly_ai_m1 闸)
    workorder_financials_router,  # 月度报表 PDF/Excel 下载
    workorder_review_router,  # 审核队列与签批闭环
    workorder_bank_sales_router,  # 银行流水倒推销项建议
    front_desk_router,  # 目标驱动前门(m1+front_desk 双闸)
    steward_router,  # 智能管家(m1+steward 双闸 · 全只读)
    steward_session_router,  # 管家会话管理(列表/改名/删除 + 附件删除 + 余额 · 同双闸)
    steward_stream_router,  # 管家任务事件 SSE(步骤账本增量 · 同双闸)
    tax_profile_router,  # 税务画像/别名/义务清单(m1 闸)
    client_pool_router,  # LINE 待问客户池(m1+client_pool 双闸)
    settings_router,
    categories_router,
    pages_router,  # 静态页面 + 公开 meta
    me_router,
    line_binding_router,
    erp_router,  # ERP 推送
    erp_agent_router,  # Express Push · 本地 Agent 出站拉取 + token
    erp_bridge_router,  # ERP 桥 · 内网出站 + 管理端
    companion_installer_router,  # 小助手安装包下载
    dms_router,  # MR.ERP DMS · 身份证→订车单
    dms_roster_router,  # DMS 操作员花名册(owner-only)
    daily_router,  # Daily 周记账(daily_finance 闸 · 每用户独立租户隔离)
    line_dms_webhook_router,  # DMS 独立 LINE OA webhook
    admin_users_router,
    history_router,  # OCR 历史(含 assign_client)
    bank_recon_router,
    admin_migration_router,
    admin_cost_router,
    tenant_router,
    admin_logs_router,
    admin_settings_router,  # 平台钥匙闸(对话 Agent 总闸 + 灰度)
    admin_ocr_engine_router,
    admin_agent_router,
    admin_pos_entitlement_router,
    admin_pearnly_ai_router,
    admin_dms_router,
    exceptions_router,
    billing_router,
    admin_diagnostics_router,  # 含 internal/deploy*
    recon_jobs_router,
    ocr_jobs_router,
    import_router,  # 通用模板学习层 列映射接口
    auth_email_code_router,
    line_account_merge_router,
    oauth_router,
    oauth_line_router,
    line_webhook_router,
    line_card_image_router,  # 泰语图卡出图(公开)
    login_router,
    meta_aliases_router,  # /api/version + v1 OCR 别名
    ocr_export_router,
)


def _include_knowledge(app) -> None:
    """知识库(RAG + 死规则检查)· 从 pearnly-knowledge 沙盒迁入。

    KNOWLEDGE_ENABLED 默认未设 → 路由不挂载(线上隐身 · 现有用户零影响);
    仅挂载时注册真实 host provider,让契约层有真实后端接线。"""
    if os.environ.get("KNOWLEDGE_ENABLED") != "1":
        return
    from routes.knowledge_ask_routes import router as knowledge_ask_router
    from routes.knowledge_risk_routes import router as knowledge_risk_router
    from routes.knowledge_routes import router as knowledge_router
    from routes.knowledge_rules_routes import router as knowledge_rules_router
    from services.knowledge import contract as kb_contract
    from services.knowledge.host_provider import MainHostProvider

    kb_contract.use_provider(MainHostProvider())
    for router in (
        knowledge_router,
        knowledge_rules_router,
        knowledge_ask_router,
        knowledge_risk_router,
    ):
        app.include_router(router)
    logger.info("knowledge base routes mounted (KNOWLEDGE_ENABLED=1)")


def include_all(app) -> None:
    """把全部路由挂到 app 上(顺序即 ROUTERS 顺序)。"""
    for router in ROUTERS:
        app.include_router(router)
    _include_knowledge(app)
