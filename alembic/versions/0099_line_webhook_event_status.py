# -*- coding: utf-8 -*-
"""LINE webhook 事件表加处理状态:处理失败的事件不再被永久钉成「已处理」。

Revision ID: 0099_line_webhook_event_status
Revises: 0098_docs_ocr_history_link
Create Date: 2026-08-11

原来 line_webhook_events 只有 (event_id, received_at):webhook 在处理前就 INSERT 抢占,
handler 抛异常后行仍在表里 → LINE 重投永远被拦 → 消息静默消失,且表里没有任何痕迹可查。
加状态列后拆成 claim(processing)→ mark_done / mark_failed 三段,失败留 last_error +
payload 供人工排查(48h TTL 照旧清)。

status DEFAULT 'done':建列前的存量行语义就是「已处理完」,默认值就地把它们钉住,不会因为
多了状态列被当成待处理重跑。failed 行不自动重放(handler 可能已部分写库,重放=重复入账),
可重投的路是回执让用户重发 —— 见 services/line_binding/line_webhook_dedup 顶注。

Dual-run:prod 无自动迁移钩子,真正建列靠 startup 幂等自愈
(services/line_binding/line_webhook_dedup.ensure_table 跑同一批 DDL),本版仅留档。
"""

from alembic import op

revision = "0099_line_webhook_event_status"
down_revision = "0098_docs_ocr_history_link"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("status", "text NOT NULL DEFAULT 'done'"),
    ("source", "text"),
    ("attempts", "int NOT NULL DEFAULT 1"),
    ("last_error", "text"),
    ("payload", "jsonb"),
    ("updated_at", "timestamptz"),
)


def upgrade() -> None:
    for name, spec in _COLUMNS:
        op.execute(f"ALTER TABLE line_webhook_events ADD COLUMN IF NOT EXISTS {name} {spec}")


def downgrade() -> None:
    for name, _spec in _COLUMNS:
        op.execute(f"ALTER TABLE line_webhook_events DROP COLUMN IF EXISTS {name}")
