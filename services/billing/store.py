# -*- coding: utf-8 -*-
"""Google AI Studio 余额追踪(billing_balance_log)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
管理员每周更新一次真实余额 · 系统自动反推校准系数(calibration_factor)。

2026-05-25 · Earn 后台改造删除:add_balance_log / get_balance_summary
(Google「实际余额」卡下线 · 手动录入值会误导成自动余额 · 改由 admin 直达
Google 计费页自查)。保留 get_latest_balance + 表 billing_balance_log:
vat_excel_routes / recon_jobs 仍读 calibration_factor 兜底。
db.py 文件尾 re-export 回本命名空间 · 所有 ``db.xxx()`` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any

import db

logger = logging.getLogger(__name__)


def ensure_billing_balance_table():
    """启动时建余额追踪表 · 幂等"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS billing_balance_log (
                    id BIGSERIAL PRIMARY KEY,
                    real_balance_thb NUMERIC(12, 4) NOT NULL,
                    notes TEXT,
                    estimated_used_since_last NUMERIC(12, 4) DEFAULT 0,
                    real_used_since_last NUMERIC(12, 4) DEFAULT 0,
                    calibration_factor NUMERIC(6, 4) DEFAULT 1.0,
                    updated_by_user_id UUID,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_billing_log_created ON billing_balance_log(created_at DESC);
            """)
            logger.info("✅ billing_balance_log 表已就绪")
    except Exception as e:
        logger.error(f"ensure_billing_balance_table failed: {e}")


def get_latest_balance() -> Optional[Dict[str, Any]]:
    """拿最新一条余额记录"""
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM billing_balance_log
                ORDER BY created_at DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"get_latest_balance failed: {e}")
        return None
