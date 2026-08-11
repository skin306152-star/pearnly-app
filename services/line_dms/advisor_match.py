# -*- coding: utf-8 -*-
"""把 LINE 操作员的 DMS 登录账号匹配成订车单的销售顾问(ที่ปรึกษาการขาย)。

DMS 按订车单的顾问栏算销售提成,而那一栏的值是我们 POST 上去的:测试站 probe 实证
「填谁存谁」,与登录账号无关,三键(usersval/txtusers/txtuserstel)留空则整单被拒收
(Korn 2026-08-11 确认)。旧实现恒填顾问主档第一行 → 全公司的单都记到同一个人头上。

匹配键 = DMS 登录名 ↔ 顾问主档 code 列(_bshsd("txtusers") 行形 [id, code, name, tel],
code 列即 DMS 登录名)。账号不在顾问名册(如老板借号、代录员)时,老板可在端点
config.booking_defaults.advisor_id 上钉死归属,钉死优先于名册匹配。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from services.line_dms.qa_util import find_row

logger = logging.getLogger(__name__)

_COL_CODE = 1
_COL_NAME = 2


def _cell(row: list, idx: int) -> str:
    if not row or len(row) <= idx or row[idx] is None:
        return ""
    return str(row[idx]).strip()


def _ref(row: list) -> Dict[str, str]:
    """会话里只留 id(DMS 认人的键)+ name(预览卡/回执给人看)。

    code/tel 建单层会按 id 从实时名册重解一次(_advisor_ref_strict),存进会话只会
    在主档改动后变陈旧,还多两处要维护。
    """
    return {"id": _cell(row, 0), "name": _cell(row, _COL_NAME)}


def match_advisor(advisors: List[list], dms_username: str) -> Optional[Dict[str, str]]:
    """DMS 登录名 → 顾问主档行;认不准就弃权(返 None),不猜。

    先比 code 列(登录名),没有再比 name 列(有些站把登录名直接当顾问名录进去)。
    同一层命中多行 = 名册里有重名/重号,此时填错提成要到月底对账才炸,拦下来反而当场
    有人喊 —— 所以多命中一律弃权。
    """
    needle = (dms_username or "").strip().casefold()
    if not needle:
        return None
    for col in (_COL_CODE, _COL_NAME):
        hits = [r for r in advisors or [] if _cell(r, col).casefold() == needle]
        if len(hits) == 1:
            return _ref(hits[0])
        if hits:
            return None
    return None


def resolve_operator_advisor(ep: Dict[str, Any]) -> Tuple[Optional[Dict[str, str]], str]:
    """端点 → (顾问, DMS 登录名)。返回的登录名只用于拦截话术,好让销售知道是哪个账号没对上。

    阻塞函数(解密 + 可能触发一次 DMS 登录抓主档),调用方经 _thr 调用。
    """
    cfg = (ep or {}).get("config") or {}
    pinned = dict(cfg.get("booking_defaults") or {})
    if str(pinned.get("advisor_id") or "").strip():
        return _pinned_advisor(ep, pinned), ""
    username = _dms_username(cfg)
    if not username:
        return None, ""
    from services.line_dms import masters_cache

    cached = masters_cache.read_fresh_masters(ep)
    hit = match_advisor((cached or {}).get("advisors") or [], username)
    if hit is None:
        # 拦截话术让人「去 DMS 名册加上这个账号再试」——主档缓存 12 小时,不现抓一次的话
        # 那句「再试一次」在半天内都是假的(缓存也可能是旧版分页只存了 10 行)。
        # 缓存本来就冷/过期时 get_masters 自己会现抓,不必 force(免得同一请求连抓两遍)。
        fresh = masters_cache.get_masters(ep, force_refresh=cached is not None) or {}
        hit = match_advisor(fresh.get("advisors") or [], username)
    return hit, username


def _pinned_advisor(ep: Dict[str, Any], pinned: Dict[str, Any]) -> Dict[str, str]:
    """老板在端点上钉死的归属(账号不在顾问名册时的出路)。

    name 缺就从已暖的主档缓存按 id 补一个给预览卡显示;补不到也照样放行 —— 建单层
    (_advisor_ref_strict)还会按 id 再解析一次拿权威名字。
    """
    from services.line_dms import masters_cache

    advisor_id = str(pinned.get("advisor_id") or "").strip()
    name = str(pinned.get("advisor_name") or "").strip()
    if not name:
        cached = masters_cache.read_fresh_masters(ep) or {}
        row = find_row(cached.get("advisors"), advisor_id)
        if row:
            name = _cell(row, _COL_NAME)
    return {"id": advisor_id, "name": name}


def _dms_username(cfg: Dict[str, Any]) -> str:
    """解出这位操作员自己的 DMS 登录名(花名册发号时落的 username_enc)。解不出 → 空串。

    解不出就当没匹配上(调用方发拦截话术),绝不猜账号 —— 猜错 = 提成算到别人头上。
    """
    from services.erp.erp_dms_push import _dms_plain_creds

    try:
        return _dms_plain_creds(cfg)[0].strip()
    except Exception:
        logger.warning("[dms advisor] resolve dms username failed", exc_info=True)
        return ""
