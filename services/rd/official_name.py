# -*- coding: utf-8 -*-
"""官方公司名核验 ③ · OCR 落库后后台按卖方税号查税局 RD 官方抬头并回填(并存·不动 AI 名)。

复用现成的 services/rd/rd_api.lookup_vat(已带 rd_cache 7 天缓存)。全程非致命、后台异步,
绝不拖慢 OCR 响应;RD 外部接口慢/挂只是这条不回填,识别照常。"""

import asyncio
import logging
import re

from core import db

logger = logging.getLogger(__name__)

_TAX13 = re.compile(r"^\d{13}$")


def _valid_tax(tax) -> str:
    t = re.sub(r"\D", "", str(tax or ""))
    return t if _TAX13.match(t) else ""


async def enrich_records(pairs, user_id, tenant_id) -> int:
    """pairs = [(history_id, seller_tax), ...]。查到官方名→回填。返回回填条数。"""
    from services.rd import rd_api

    done = 0
    seen_tax: dict = {}
    for hid, tax in pairs:
        t = _valid_tax(tax)
        if not hid or not t:
            continue
        try:
            res = seen_tax.get(t)
            if res is None:
                res = await asyncio.to_thread(rd_api.lookup_vat, t)
                seen_tax[t] = res
            if res.get("ok"):
                name = (res.get("data") or {}).get("name")
                if name and db.update_history_official_name(hid, name, user_id, tenant_id):
                    done += 1
        except Exception as e:
            logger.warning(f"official-name enrich skip (hid={hid}): {e}")
    return done


def schedule(pairs, user_id, tenant_id) -> None:
    """同步上下文里调度后台回填(无运行 loop 则跳过·best-effort)。"""
    if not pairs:
        return
    try:
        asyncio.create_task(enrich_records(pairs, user_id, tenant_id))
    except RuntimeError:
        pass
