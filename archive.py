# -*- coding: utf-8 -*-
"""
Mr.Pilot · v0.7 智能归档模块
职责:根据用户的命名模板和一条 ocr_history 记录,生成合法的归档文件名。
此版本不处理 ZIP 打包(v0.7.2 再做),只负责"给文件起个好名字"。
"""
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 默认命名模板 · 所有新用户初始就是这套规则
# 例:2026-04-15_DHL_运费_THB1250
DEFAULT_TEMPLATE: List[Dict[str, Any]] = [
    {"type": "date",     "format": "YYYY-MM-DD"},
    {"type": "sep",      "val": "_"},
    {"type": "seller",   "short": True},
    {"type": "sep",      "val": "_"},
    {"type": "category"},
    {"type": "sep",      "val": "_"},
    {"type": "amount",   "with_currency": True},
]

# 默认文件夹策略
DEFAULT_FOLDER_STRATEGY = "by_month_seller"

# 文件名非法字符(Windows + Linux + macOS 共同禁用的)
# / \ : * ? " < > | 以及控制字符
ILLEGAL_CHARS_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# 文件名最大长度(保守取 180 · 留给后缀和 zip 路径)
MAX_FILENAME_LEN = 180


def _sanitize(text: str) -> str:
    """清理文件名不合法的字符 + 空格转下划线"""
    if not text:
        return ""
    text = str(text).strip()
    # 把非法字符换成下划线
    text = ILLEGAL_CHARS_RE.sub("_", text)
    # 空格也转下划线(文件名里有空格对 ERP / shell 不友好)
    text = re.sub(r"\s+", "_", text)
    # 折叠连续的下划线 / 短横
    text = re.sub(r"([_\-])\1+", r"\1", text)
    return text.strip("._-")


def _short_seller(name: str) -> str:
    """供应商简称:取前 20 字,去掉 "บริษัท / Co.,Ltd. / จำกัด" 之类后缀"""
    if not name:
        return ""
    s = name.strip()
    # 去掉常见的公司后缀词
    patterns = [
        r"\s*บริษัท\s*", r"\s*จำกัด\s*", r"\s*\(มหาชน\)\s*",
        r"\s*Co\.?,?\s*Ltd\.?\s*$", r"\s*Company\s*Limited\s*$",
        r"\s*Public\s+Company\s+Limited\s*$", r"\s*PCL\.?\s*$",
        r"\s*Inc\.?\s*$", r"\s*Ltd\.?\s*$",
        r"\s*有限公司\s*", r"\s*股份有限公司\s*",
    ]
    for p in patterns:
        s = re.sub(p, " ", s, flags=re.IGNORECASE).strip()
    # 限长:纯 ASCII(英文/数字)给 30 字 · 含中/泰文给 20 字(中泰文单字信息量大)
    is_ascii = all(ord(c) < 128 for c in s)
    max_len = 30 if is_ascii else 20
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return _sanitize(s)


def _format_date(raw: str, fmt: str) -> str:
    """把日期按用户要的格式输出 · 输入可能是 YYYY-MM-DD 也可能是别的格式"""
    if not raw:
        return ""
    # 试着解析常见格式
    import datetime
    raw = str(raw).strip()
    for parse_fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            d = datetime.datetime.strptime(raw[:10], parse_fmt)
            # 转换用户的输出格式
            out_fmt = (fmt or "YYYY-MM-DD") \
                .replace("YYYY", "%Y") \
                .replace("YY",   "%y") \
                .replace("MM",   "%m") \
                .replace("DD",   "%d")
            return d.strftime(out_fmt)
        except ValueError:
            continue
    # 解析失败 · 原样返回前 10 字
    return _sanitize(raw[:10])


def _format_amount(value: Any, with_currency: bool) -> str:
    """金额格式化:1234.5 → "THB1235" 或 "1235" """
    if value is None or value == "":
        return ""
    try:
        n = float(str(value).replace(",", ""))
        s = f"{int(round(n))}"  # 整数化省空间
        return f"THB{s}" if with_currency else s
    except (ValueError, TypeError):
        return ""


def build_archive_name(history_record: Dict[str, Any],
                       template: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    核心:按模板+一条历史记录生成归档名(不含 .pdf 后缀)

    history_record 结构(从 ocr_history 表读的字段,或 merged_fields):
      - date / invoice_date
      - seller_name
      - buyer_name
      - total_amount
      - category_tag (v0.7 新增)
      - invoice_number
    """
    if not template:
        template = DEFAULT_TEMPLATE

    # 兼容两种数据结构:一种是 db 行(扁平),一种是 merged_fields 嵌套
    mf = history_record.get("merged_fields") or history_record

    parts: List[str] = []
    for token in template:
        t_type = token.get("type")

        if t_type == "sep":
            parts.append(str(token.get("val", "_")))
            continue

        elif t_type == "date":
            raw = mf.get("date") or mf.get("invoice_date") or history_record.get("date")
            val = _format_date(raw or "", token.get("format", "YYYY-MM-DD"))

        elif t_type == "seller":
            raw = mf.get("seller_name") or history_record.get("seller_name") or ""
            val = _short_seller(raw) if token.get("short", True) else _sanitize(raw)

        elif t_type == "buyer":
            raw = mf.get("buyer_name") or history_record.get("buyer_name") or ""
            val = _short_seller(raw) if token.get("short", True) else _sanitize(raw)

        elif t_type == "category":
            raw = mf.get("category") or history_record.get("category_tag") or ""
            val = _sanitize(raw)[:10]

        elif t_type == "amount":
            raw = mf.get("total_amount") or history_record.get("total_amount")
            val = _format_amount(raw, token.get("with_currency", True))

        elif t_type == "invoice_no":
            raw = mf.get("invoice_number") or history_record.get("invoice_number") or ""
            val = _sanitize(raw)

        elif t_type == "note":
            val = _sanitize(str(token.get("val", "")))

        else:
            logger.warning(f"archive: unknown token type {t_type}")
            val = ""

        parts.append(val)

    # 合并 · 相邻的空字段会导致双分隔符,要清理
    name = "".join(parts)
    # 折叠连续的 _ _ _ 或 - - -
    name = re.sub(r"([_\-\s])\1+", r"\1", name)
    # 去掉首尾的分隔符
    name = name.strip("_-. ")

    # 兜底:如果名字空了,用原文件名或 unknown
    if not name:
        name = _sanitize(history_record.get("filename", "") or "unknown")

    # 限长
    if len(name) > MAX_FILENAME_LEN:
        name = name[:MAX_FILENAME_LEN].rstrip("_-. ")

    return name


def preview_name(merged_fields: Dict[str, Any],
                 template: Optional[List[Dict[str, Any]]] = None) -> str:
    """给前端实时预览用 · 传 merged_fields 直接出名字"""
    return build_archive_name({"merged_fields": merged_fields}, template)
