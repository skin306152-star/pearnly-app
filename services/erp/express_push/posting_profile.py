# -*- coding: utf-8 -*-
"""每账套「记账画像」· 决定这家客户的商品行怎么落账(纯函数 · 无 IO · 可单测)。

一个事务所替 N 个客户记账,每家账法不同:贸易/制造跑永续库存、服务/现销不碰库存。
系统不能写死一套再打补丁——把"怎么记账"从代码里的分支变成每账套的数据(画像),
画像从客户 Express 既有账的「记账指纹」推断(小助手上报),会计确认一次即锁。

posting_mode(有效自动过账车道):
  - non_stock      非库存主档:逐商品明细、不动库存。周期制/无库存客户默认。
  - direct_account 科目直记:连商品主档都不建,行挂 GL 科目。最省、GL 仍正确。
  - stock          永续库存(V2-b · gated):扣库存 + COGS。仅对确认真管库存的客户开。
  - manual_review  不安全自动落 → 交会计:永续客户但库存路未开 / 业态拿不准。
                   ★铁律:永续客户的采购绝不能悄悄按周期制(direct/non_stock)落——
                   会与其既有永续账双重计成本 / 错报存货。宁可 escalate,不可静默错账。

inventory_usage(从指纹推断的客观事实):none | perpetual | mixed | unknown。
判据阈值经 6 家真账套实测标定(见 test_posting_profile);动库存行占比 ≥0.60=perpetual、
≤0.15=none、之间=mixed。指纹缺失=unknown(不猜)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# 动库存行占比阈值(6 家真账标定:AsiaSports .87 / Moritomo .99 / SKChem .86 = perpetual;
# Saengjit 0 / 冰厂 .05 = none;WorldNaturalFood .38 = mixed)。行为钉死在单测,勿随手改。
_PERPETUAL_MIN = 0.60
_NONE_MAX = 0.15


@dataclass
class PostingProfile:
    """一家客户的记账画像。inventory_usage=客观事实,posting_mode=gate 感知后的有效车道。"""

    inventory_usage: str  # none | perpetual | mixed | unknown
    posting_mode: str  # non_stock | direct_account | stock | manual_review
    needs_confirm: bool  # 草案未经会计确认(锁前不当既定事实用)
    source: str  # inferred | confirmed | default
    reason: str  # 审计留痕:为什么落这个 mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inventory_usage": self.inventory_usage,
            "posting_mode": self.posting_mode,
            "needs_confirm": self.needs_confirm,
            "source": self.source,
            "reason": self.reason,
        }


def _moving_ratio(fp: Dict[str, Any]) -> Optional[float]:
    """动真实库存的明细行占比。行数缺/非法/为 0 → None(无从判断,不臆造)。"""
    try:
        lines = int(fp.get("stcrd_lines"))
        moving = int(fp.get("stcrd_lines_moving_stock"))
    except (TypeError, ValueError):
        return None
    if lines <= 0:
        return None
    return max(0.0, min(1.0, moving / lines))


def classify_inventory_usage(fingerprint: Optional[Dict[str, Any]]) -> str:
    """记账指纹 → 客观库存用量 none|perpetual|mixed|unknown。指纹缺失=unknown(不猜)。"""
    if not isinstance(fingerprint, dict):
        return "unknown"
    # 零库存主档 = 铁定不管库存(Saengjit:61 档全服务码 / 0 库存品),直接判 none。
    try:
        if int(fingerprint.get("stock_master_count")) == 0:
            return "none"
    except (TypeError, ValueError):
        pass
    r = _moving_ratio(fingerprint)
    if r is None:
        return "unknown"
    if r >= _PERPETUAL_MIN:
        return "perpetual"
    if r <= _NONE_MAX:
        return "none"
    return "mixed"


def infer_profile(
    fingerprint: Optional[Dict[str, Any]], *, stock_enabled: bool = False
) -> PostingProfile:
    """从指纹推断画像草案。stock_enabled=本端点 V2-b 库存路是否开(缺省 False=全局未开)。"""
    usage = classify_inventory_usage(fingerprint)
    if usage == "none":
        # 无库存客户:非库存主档安全落,推断即可直用(不必人裁)。
        return PostingProfile(
            "none", "non_stock", False, "inferred", "zero/near-zero stock movement"
        )
    if usage == "perpetual":
        if stock_enabled:
            return PostingProfile(
                "perpetual", "stock", True, "inferred", "high stock movement · stock lane on"
            )
        # ★永续客户但库存路未开:绝不静默按周期制落(会与既有永续账双重计成本)→ 交会计。
        return PostingProfile(
            "perpetual",
            "manual_review",
            True,
            "inferred",
            "perpetual client but stock lane off · escalate (no silent periodic post)",
        )
    if usage == "mixed":
        # 半库存半非库存:逐行车道人裁不了自动定,交会计一次锁画像。
        return PostingProfile(
            "mixed", "manual_review", True, "inferred", "mixed inventory usage · needs verdict"
        )
    # unknown(冷启动 / 旧 Agent 没上报指纹):保守走非库存 + 待确认,不一上来全堵人工。
    return PostingProfile(
        "unknown", "non_stock", True, "default", "no fingerprint · conservative non_stock"
    )


def profile_from_config(
    config: Optional[Dict[str, Any]], *, stock_enabled: bool = False
) -> PostingProfile:
    """取本端点画像:会计已确认的覆盖优先(compile-once),否则从上报指纹推断。

    config 键:posting_profile(会计确认后锁的覆盖)· catalog_fingerprint(小助手上报的记账指纹)。
    """
    config = config or {}
    override = config.get("posting_profile")
    if isinstance(override, dict) and override.get("posting_mode"):
        return PostingProfile(
            inventory_usage=str(override.get("inventory_usage") or "unknown"),
            posting_mode=str(override.get("posting_mode")),
            needs_confirm=False,
            source="confirmed",
            reason="accountant-confirmed override",
        )
    return infer_profile(config.get("catalog_fingerprint"), stock_enabled=stock_enabled)
