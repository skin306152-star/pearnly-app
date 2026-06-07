# -*- coding: utf-8 -*-
"""POS 项目 schema 双跑总入口(POS 项目 · 启动调一次 · 与 alembic 0021+ 双跑)。

集中 POS/库存各表的幂等建表,startup 只调 bootstrap_pos_schema() 一行——避免 startup.py
随 PO 增多(A1 tenant_modules / A2 product_units / A3 库存 / B POS 表)而膨胀过 500 行。
每个子 ensure 自带 try/except 不互相阻断;这里再包一层兜底,任一失败不挡其余 + 不挡主服务。
"""

import logging

logger = logging.getLogger("mr-pilot")


def bootstrap_pos_schema() -> None:
    from services.inventory import store as inventory_store
    from services.modules import store as modules_store
    from services.products import units as product_units

    steps = (
        ("tenant_modules", modules_store.ensure_table),
        ("product_units", product_units.ensure_schema),
        ("inventory_core", inventory_store.ensure_schema),
    )
    for label, fn in steps:
        try:
            fn()
        except Exception as e:
            logger.warning(f"启动 POS schema {label} 失败(等 alembic): {e}")
