# -*- coding: utf-8 -*-
"""POS 小票合规字段 ensure + 小票二维码载荷(SM 缺口批次 G1/G4)。

workspace_clients 两列(与 alembic 0094 同源 · prod 不跑 alembic,启动期经 bootstrap_pos_schema
双跑生效):

- pos_register_no:税务局收银机登记号。票面规则=有号才印整行,没号不印(不印空标签)。
- pos_receipt_qr_enabled:小票二维码开关,**默认关**。码内容是 G2「凭小票号补开全式税票」
  通路的公网入口;G2 未施工前开着就是死链(扫码 404),故 G2 落地前保持 FALSE,随 G2 批次开。

qr_payload 是码内容的**单一定义处**:G2 施工若定了别的路径,只改这里,不必追渲染层。
"""

from __future__ import annotations

import os
from urllib.parse import quote


def ensure_receipt_schema() -> None:
    """幂等加列(startup 经 bootstrap_pos_schema 调 · DDL 必须 commit=True)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS pos_register_no text")
        cur.execute(
            "ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS pos_receipt_qr_enabled "
            "boolean NOT NULL DEFAULT FALSE"
        )


def qr_payload(*, workspace_client_id: int, receipt_no: str) -> str:
    """小票二维码内容 = 凭小票号申请全式税票的公网入口(G2 通路预定路由)。

    workspace_client_id 是全局唯一 BIGSERIAL,足以定位账套;小票号在账套内定位交易
    (get_sale_by_receipt 已有)。base 域名同 line_proof 的惯例走 PEARNLY_BASE_URL。
    """
    base = (os.environ.get("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")
    return f"{base}/pos/full-tax-invoice?ws={workspace_client_id}&no={quote(receipt_no or '')}"
