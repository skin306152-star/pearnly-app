# -*- coding: utf-8 -*-
"""
Mr.Pilot · v0.17 · M6 邮箱附件抓取
职责:
  - 从用户邮箱(IMAP)拉取未读邮件 · 提取 PDF/图片附件
  - 喂给 Gemini OCR → 写 ocr_history · 触发自动 ERP 推送
  - 记录抓取日志到 email_ingest_logs
  - 单账号账号 + 应用密码(不走 OAuth · MVP 简化)

安全:
  - 密码用 Fernet 对称加密 · 密钥从环境变量 EMAIL_ENCRYPTION_KEY 读
  - 首次运行如无密钥会生成一个 · 打印到日志 · 部署者必须保存到环境变量

本模块本轮只做骨架 + 加密工具 · 真实抓取逻辑放到 _fetch_imap_attachments
下一轮再接到 FastAPI 定时任务和前端接口
"""

# 模块拆分(2026-06-02 · REFACTOR-WB-modularize · 本文件 = re-export facade):
#   email_ingest_crypto  · 密码加解密 + 可用性
#   email_ingest_imap    · IMAP 预设/常量 + MIME/连接/抓取 helper
#   email_ingest_pipeline· 单附件摄取 + 自动推送 + 账号抓取编排 + 连接测试

from services.email_ingest.email_ingest_crypto import (  # noqa: F401  public re-export
    _get_fernet,
    encrypt_password,
    decrypt_password,
    is_available,
)
from services.email_ingest.email_ingest_imap import (  # noqa: F401  public re-export
    IMAP_PRESETS,
    _SUPPORTED_EXTS,
    INITIAL_DAYS_BACK,
    MAX_EMAILS_PER_RUN,
    _decode_mime,
    _extract_attachments,
    _connect_imap,
    _search_unread_with_attachments,
    _fetch_email,
    _mark_seen,
)
from services.email_ingest.email_ingest_pipeline import (  # noqa: F401  public re-export
    _ingest_one_attachment,
    _auto_push_if_configured,
    run_account_ingest,
    test_connection,
)
