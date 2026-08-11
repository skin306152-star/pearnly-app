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
    "dms",  # 车行 DMS
)

_USAGE: ContextVar[Optional[Dict[str, Any]]] = ContextVar("ai_usage_context", default=None)


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

    已在归因域内则做补齐式合并:入口保持外层的,doc_type/pages 用本次传入的非空值补上。"""
    outer = _USAGE.get() or {}
    doc = (doc_type or "").strip() or None
    merged = {
        "entry_point": outer.get("entry_point") or _clean_entry(entry_point),
        "doc_type": doc or outer.get("doc_type"),
        "pages": _clean_pages(pages) or outer.get("pages"),
    }
    return _USAGE.set(merged)


def reset_usage_context(token: Token) -> None:
    _USAGE.reset(token)


def current() -> Optional[Dict[str, Any]]:
    return _USAGE.get()


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
