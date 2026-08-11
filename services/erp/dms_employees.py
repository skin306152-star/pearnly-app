# -*- coding: utf-8 -*-
"""DMS 员工表(users)取数 —— 顾问匹配的精确层:登录名 ↔ 员工。

顾问下拉(bshsd txtusers,行 [id, code, name, tel])的 code 列是【员工编号】(txtuserscode)
不是登录名:测试站两列相等只是录入习惯,2026-08-12 探针员工(337 · WKC99 · wkuser99)实证
两者可以不同。拿登录名去比 code 列,在「编号 ≠ 登录名」的车行一律落空;更坏的是 A 的编号
恰好等于 B 的登录名时会把提成算到 B 头上。员工表是唯一带登录名的表,精确匹配只能走这里。

权限退化:员工列表页未必对销售账号开放(可能 500 / 弹回登录页)。取不到就返回 None
让调用方回落启发式匹配 —— 「拿不到名册」不等于「这个人不存在」。配了 admin 凭据组时先
借它重试一次(与客户档写操作同一个懒切会话入口)。

员工在员工表却不在顾问下拉是合法状态(下拉过滤 = 职位 6 + 挂团队),意思是「这个人没有
当顾问的资格」,不是取数失败。
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 员工列表接口(与 cus/drfcbc 同一套 showdata listing 范式)。sd="" 即不过滤取全量;
# 单页 500 行覆盖单店全部员工 —— 员工表比顾问名册还小,不值得为它再写一套翻页。
_LIST_PATH = "users/component/showdata.php"
_LIST_BODY = {"sdtamt": "500", "sdtpage": "1", "sd": "", "selcolsort": "1", "selcolsorttype": "1"}

_ROW_RE = re.compile(r'data-val="([^"]+)"')
_CELL_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)
_FIELDS = ("code", "login", "name")
# showdata 结果体前缀:有结果 dt:: / 空结果 ndt::(同 _parse_customer_rows)。认得出这两个
# 才敢把「没有行」判成「员工表没人」而不是「取数挂了」。
_LIST_MARKERS = ("dt::", "ndt::")


def _text(raw: str) -> str:
    """<p> 内文 → 纯文本;DMS 的空占位 "-" 归一成空串。"""
    value = html.unescape(re.sub(r"<.*?>", "", raw)).strip()
    return "" if value == "-" else value


def parse_employee_rows(body: str) -> Optional[List[Dict[str, str]]]:
    """员工列表 HTML 片段 → [{"id", "code", "login", "name"}].

    一行 = 一个 data-val="<员工id>" 块,块内 <p> 按序是 编号 / 登录名 / 姓名。一个 <p> 都
    没有的 data-val 块不是员工行(分页/表头之类的控件),跳过。
    空 body、或结果体(dt::/ndt::)里没有行 → [](员工表真的没人 / 搜索无结果);有内容却一
    行都解不出 → None(错误页、被踢回登录页、或 DMS 换了模板)。两者必须分得开:前者可以
    照常判「不在员工表」,后者只能退化到启发层。
    """
    text = (body or "").strip()
    if not text:
        return []
    marks = list(_ROW_RE.finditer(text))
    rows: List[Dict[str, str]] = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        cells = [_text(c) for c in _CELL_RE.findall(text[mark.end() : end])]
        if not any(cells):
            continue
        cells += [""] * (len(_FIELDS) - len(cells))
        rows.append({"id": mark.group(1), **dict(zip(_FIELDS, cells))})
    if rows:
        return rows
    return [] if text.startswith(_LIST_MARKERS) else None


def fetch_employees(cl: Any) -> Optional[List[Dict[str, str]]]:
    """员工表全量;取数或解析失败 → None(退化信号,别当成「员工表为空」)。

    cl 鸭子类型吃 DMSClient(_post_text + 可选 admin 会话入口),本模块不 import client 侧
    任何东西 —— ops 会 import 它,反向引用就成环了。
    """
    rows = _fetch_once(cl)
    if rows is None:
        rows = _fetch_via_admin(cl)
    if rows is None:
        logger.warning("[dms employees] employee list unavailable; advisor match degrades")
    return rows


def _fetch_once(cl: Any) -> Optional[List[Dict[str, str]]]:
    """当前会话拉一次。HTTP 非 200(_post_text 抛 DMSClientError)与格式异常同等对待。"""
    try:
        return parse_employee_rows(cl._post_text(_LIST_PATH, dict(_LIST_BODY)))
    except Exception:
        logger.debug("[dms employees] fetch failed on current session", exc_info=True)
        return None


def _fetch_via_admin(cl: Any) -> Optional[List[Dict[str, str]]]:
    """借 admin 凭据组重试(销售账号常没有员工页权限)。没配 admin → 不重试。

    _admin_transport 只是「配没配」的判据,读它不会触发懒登录;真正切会话的是
    _writer_session(admin 登录本身失败会从这里抛出来)。
    """
    if getattr(cl, "_admin_transport", None) is None:
        return None
    try:
        with cl._writer_session():
            return _fetch_once(cl)
    except Exception:
        logger.debug("[dms employees] admin retry failed", exc_info=True)
        return None


def match_by_login(employees: Optional[List[dict]], username: str) -> Optional[Dict[str, str]]:
    """DMS 登录名 → 员工行(strip + casefold 精确比 login 列)。零/多命中 → None。

    只比 login 列:编号列(code)撞上别人的登录名正是这一层要修的错配。多命中 = 员工表里
    有重复登录名,猜谁都可能把提成记到别人头上,一律弃权。
    """
    needle = (username or "").strip().casefold()
    if not needle:
        return None
    hits = [e for e in employees or [] if str(e.get("login") or "").strip().casefold() == needle]
    return hits[0] if len(hits) == 1 else None
