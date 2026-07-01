# -*- coding: utf-8 -*-
"""科目安全阀 · Zihao 定:科目匹配现有则用,匹配不上**退回用户**(不静默硬建)。

两层:
① 反应层(工作即生效):MR.ERP 导入 report 报科目未匹配/不存在(泰文)时,把该失败**单独归为
   ERR_ACCOUNT_NEEDS_REVIEW**——提示用户"为该套账配置科目码",而非当普通失败或硬建科目。
② 主动层(调用方提供该套账科目表 mappings['_mrerp_accounts'] 时启用,像 own_tax 闸):推前校验
   将用到的科目码都在表内,不在→挡下退回。未提供科目表 → 主动层休眠(无从判断,不误挡)。

科目表拉取协议(bshlistboxdata.php)尚未打通 → 主动层现休眠,靠反应层兜底(见 known-facts §17)。
"""

from typing import Any, Dict, List, Optional

ACCOUNT_REVIEW_CODE = "ERR_ACCOUNT_NEEDS_REVIEW"

# report 备注里"科目"相关词 + "未找到/不正确"信号 → 判为科目问题(退回用户配置)
_ACCOUNT_WORDS = ("รหัสบัญชี", "บัญชี", "acccod", "glacc")
_NOTFOUND_WORDS = ("ไม่พบ", "ไม่ถูกต้อง", "ไม่มี")


def _is_account_note(note: Any) -> bool:
    n = str(note or "").lower()
    orig = str(note or "")
    has_acc = any(w.lower() in n for w in _ACCOUNT_WORDS)
    has_nf = any(w in orig for w in _NOTFOUND_WORDS)
    return has_acc and has_nf


def tag_account_review(reasons: List[Any]) -> List[str]:
    """失败原因里含科目未匹配 → 置顶 ERR_ACCOUNT_NEEDS_REVIEW(保留原文 · 幂等)。"""
    out = [str(r) for r in (reasons or [])]
    if any(_is_account_note(r) for r in out) and ACCOUNT_REVIEW_CODE not in out:
        return [ACCOUNT_REVIEW_CODE] + out
    return out


def known_accounts(mappings: Dict[str, Any]) -> Optional[set]:
    """该套账科目表(调用方从 ERP 拉后放 mappings['_mrerp_accounts'])· None=未提供。"""
    raw = (mappings or {}).get("_mrerp_accounts")
    if not raw:
        return None
    return {str(c).strip() for c in raw if str(c or "").strip()}


def missing_from_chart(codes: List[Any], mappings: Dict[str, Any]) -> List[str]:
    """已知不在该套账科目表的科目码(去重)。科目表未提供 → []（无从判断,不误挡）。"""
    chart = known_accounts(mappings)
    if chart is None:
        return []
    seen: set = set()
    out: List[str] = []
    for c in codes:
        c = str(c or "").strip()
        if c and c not in chart and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def configured_account_overrides(mappings: Dict[str, Any]) -> List[str]:
    """用户在 mappings 配的科目码覆盖值(键含 'acc' 的 _mrerp_* 项)· 主动层校验用。"""
    out: List[str] = []
    for k, v in (mappings or {}).items():
        if isinstance(k, str) and k.startswith("_mrerp_") and "acc" in k.lower():
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
    return out


def account_gate(mappings: Dict[str, Any]) -> List[str]:
    """主动层闸:返回【配置的科目码里已知不在该套账科目表】的(需退回用户)。科目表未提供 → []。"""
    return missing_from_chart(configured_account_overrides(mappings), mappings)
