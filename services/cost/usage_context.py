# -*- coding: utf-8 -*-
"""AI 调用的成本归因上下文:入口 + 单据类型 + 页数。

问题:ai_usage 只记 task/provider/model,回答不了「这笔钱哪个入口烧的、读的什么票、几页」。
定价按 1.5 铢/页走,而银行对账单实际约 2.2 铢/页 —— 差价被混合均值藏住,逐入口成本要可见,
先得让每一行落账带上归因。

与 ai_gateway/attribution 的分工:那个管「记到谁名下」(task/租户/trace,账本主键侧);
这里管「这次调用的业务形状」(入口/单据/页数,分析维度侧)。两者独立设独立读,互不覆盖。

嵌套语义:entry_point 外层优先(最外层才是真正的产品入口,内层管线不该把它掀翻),
doc_type/pages 内层可补(路由知道入口却不知道页数,页数要到渲染完才有)。
故内层 set 只填外层留空的字段,不改已定的入口。

线程注意:contextvars 是线程本地。页级并发(ocr/page_runner · ocr/direct_read)在 submit 时
用 contextvars.copy_context().run,捕获的是主线程设好的值,归因照常跟进工作线程;新增
fan-out 的并发点必须照抄这个写法,否则子线程落的账 entry_point 为空(展示归「未归因」)。
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# 入口枚举 = 成本面板的分组键。拿不准的调用点宁可标粗(模块所属的大入口),不可标错——
# 标错会把银行长表的高成本摊进别人头上,正是这次要根治的问题。
ENTRY_POINTS: Tuple[str, ...] = (
    "web_upload",  # 网页上传(识别/复核主路径)
    "line",  # LINE 图片/语音
    "steward",  # 管家对话触发
    "workorder",  # 工单跑批
    "fileconv",  # 文件转换
    "email",  # 邮件收料
    "purchase_intake",  # 采购进料
    "bank_recon",  # 银行对账
    "vat_recon",  # 收入/VAT 对账(GL-VAT、销项汇总、发票批量核对)
    "dms",  # 车行 DMS
)

_USAGE: ContextVar[Optional[Dict[str, Any]]] = ContextVar("ai_usage_context", default=None)


class _PageSlot:
    """一次请求的页数,只许被落账取走一次。

    一份 N 页票会产生多行 ai_usage(逐页一次调用,难页再升一次高精档)。若每行都记 N,
    SUM(pages) 就按调用次数翻倍,每页成本被稀释成假的便宜 —— 正是这次要拆穿的那种混合均值。
    故页数记在其中一行,其余行留 NULL:SUM(pages) 等于真实文档页数,分母是对的。

    取值要加锁:页级并发经 copy_context 共享同一个 slot 对象,裸 check-then-clear 会让
    两个线程都取到,页数记两遍。"""

    __slots__ = ("_pages", "_lock")

    def __init__(self, pages: Optional[int]):
        self._pages = pages
        self._lock = threading.Lock()

    @property
    def pages(self) -> Optional[int]:
        return self._pages

    def take(self) -> Optional[int]:
        with self._lock:
            pages, self._pages = self._pages, None
            return pages


def _clean_pages(pages: Any) -> Optional[int]:
    """页数归一:非正数/非数字一律当未知(NULL),不落 0 —— 0 会把 cost_per_page 的分母污染成
    「有页数但为零」,与「不知道几页」在报表上是两回事。"""
    try:
        n = int(pages)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def _clean_entry(entry_point: Any) -> Optional[str]:
    """入口归一。枚举外的值照原样留下并告警:吞掉会让成本悄悄消失在「未归因」里,
    留下则在面板上直接现形,好改。归因绝不因值不合法而抛异常打断 AI 主路径。"""
    value = (entry_point or "").strip()
    if not value:
        return None
    if value not in ENTRY_POINTS:
        logger.warning("usage_context: 未登记的 entry_point=%r(照原样落账)", value[:40])
    return value


def set_usage_context(
    entry_point: str,
    doc_type: Optional[str] = None,
    pages: Optional[int] = None,
) -> Token:
    """设归因,返回 token(调用方 finally 里 reset_usage_context)。

    已在归因域内则做补齐式合并:入口保持外层的,doc_type/pages 用本次传入的非空值补上
    (外层已有页数则保留外层的 slot,不另开 —— 否则同一份票的页数会被记两遍)。"""
    outer = _USAGE.get() or {}
    doc = (doc_type or "").strip() or None
    slot = outer.get("_page_slot")
    clean_pages = _clean_pages(pages)
    # 外层已有待取页数就保留它,否则本次传了页数才开新 slot(同一份票的页数只落一行)。
    if clean_pages and (slot is None or slot.pages is None):
        slot = _PageSlot(clean_pages)
    merged = {
        "entry_point": outer.get("entry_point") or _clean_entry(entry_point),
        "doc_type": doc or outer.get("doc_type"),
        "_page_slot": slot,
    }
    return _USAGE.set(merged)


def reset_usage_context(token: Token) -> None:
    _USAGE.reset(token)


def current() -> Optional[Dict[str, Any]]:
    """当前归因(只读视图)。pages 是本次请求的文档页数,读几次都在;
    真正落账取值走 take_pages(),那条是一次性的。"""
    ctx = _USAGE.get()
    if ctx is None:
        return None
    slot = ctx.get("_page_slot")
    return {
        "entry_point": ctx.get("entry_point"),
        "doc_type": ctx.get("doc_type"),
        "pages": slot.pages if slot is not None else None,
    }


def take_pages() -> Optional[int]:
    """取走本请求的页数(只有第一次拿得到)。落账点专用,见 _PageSlot 的 why。"""
    ctx = _USAGE.get() or {}
    slot = ctx.get("_page_slot")
    return slot.take() if slot is not None else None


@contextmanager
def usage_context(
    entry_point: str,
    doc_type: Optional[str] = None,
    pages: Optional[int] = None,
):
    """调用点用的一层包装(入口只加 with,不重构)。"""
    token = set_usage_context(entry_point, doc_type=doc_type, pages=pages)
    try:
        yield
    finally:
        reset_usage_context(token)
