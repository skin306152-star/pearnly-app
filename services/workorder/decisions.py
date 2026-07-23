# -*- coding: utf-8 -*-
"""工单裁决词汇表 + 人工裁决合并回放语义(纯叶子模块 · 2026-07-10 simplify 收敛)。

裁决动词 / 方向裁定 kind /「不计入合计」语义集 / 方向不明 flag_reason 前缀——此前散在
api.py、reconcile_gates.py、conservation.py、evidence.py 里各自重声明,注释都写「与另一处
同一张表」,但那张表并不存在(改一处极易漏改另一处)。收敛到此成真·单一事实源。

human_decision 的合并回放(replay_records / kind_of)也收在此:方向槽(assign_kind 携带的 kind)
与金额槽(recalc / face_value / exclude / waive)并存于同一记录,同一件先裁方向再补金额(或反之)
不再互相顶掉。此前 reconcile / conservation / evidence / freeze / recon 各处各写一份 latest-wins
单槽回放,recalc-last 丢方向、assign-last 丢改数,酿成「R1 放行、守恒闸压回 PENDING」半死锁——
回放语义在此与词汇同源,消费方一律取用,不再各判一套。

零依赖:不 import 任何本包模块,避免循环导入。api/reconcile_gates/conservation/... 都从这里
取词,本模块绝不反向依赖它们。static/ai/ai-review-queue.js 无法 import,前缀数组旁有同步注释。
"""

from __future__ import annotations

EVT_DECISION = "human_decision"

# 裁决动词。金额裁决 face_value/recalc/exclude(W3 的 A/E/X)+ 方向票 assign_kind + 豁免 waive。
FACE_VALUE = "face_value"  # 采信票面 OCR 读数
RECALC = "recalc"  # 人工看原票补正
EXCLUDE = "exclude"  # 剔除,不计入合计
ASSIGN_KIND = "assign_kind"  # 方向不明票的人工定向裁决(带裁定 kind)
WAIVE = "waive"  # 显式放行一件无法归位的料(带 reason,备忘留痕)

# assign_kind 的裁定 kind:进项票 / 销项票 / 非税票 / 银行流水。
PURCHASE_INVOICE = "purchase_invoice"
SALES_DOC = "sales_doc"
NON_TAX = "non_tax"
BANK_STATEMENT = "bank_statement"
ASSIGN_KINDS = (PURCHASE_INVOICE, SALES_DOC, NON_TAX, BANK_STATEMENT)

# 「不计入合计」语义集:剔除与豁免都不进 Σ、不进 unresolved(豁免另在备忘留痕)。
NON_COUNTING = frozenset({EXCLUDE, WAIVE})

# 银行对账 review 清单人审裁决(MC1-b3 · E2 债):accept=采信某候选票为该笔流水的匹配 /
# reject=否掉全部候选。与上面的裁决动词同族(同落 human_decision 事件)但独立成一对——
# 它裁决的对象是银行流水行(statement_tx_id),不是 work_order_item,不共用 item 校验路径。
# 银行对账是佐证层:这对动词绝不进 R1/R2/R4 税额计算,只覆盖 R3 呈现(services/workorder/
# bank_recon_review.py + api._bank_recon 的读侧覆盖)。
BANK_RECON_ACCEPT = "bank_recon_accept"
BANK_RECON_REJECT = "bank_recon_reject"

# 方向不明票的 flag_reason:税号/名称锚点判不出进/销(direction_ambiguous)。kind=unknown,
# 必须人工定向(assign_kind)。SALES_DIRECTION_UNHANDLED 是 MC1-c.1 前「自家==卖方判死」的旧码
# ——现已改为 sort 自动归 sales_doc 堆(见 SALES_DOC_REVIEW),此常量仅为存量工单的 flag_reason
# 向后兼容保留(reconcile 的 ambiguous 收编口径、conservation 的方向判据仍认它)。
DIRECTION_AMBIGUOUS = "direction_ambiguous"
SALES_DIRECTION_UNHANDLED = "sales_direction_unhandled"
# 票面印了 VAT 但读不出(B-2):此前 _has_vat 把「读花」和「本来就没有」都归成 False,件因此
# 从「无税务要素」出口被当 non_tax 静默排除。读不出方向也就无从判,交人定向 —— 走同一条方向
# 通道即可,无裁决则 R1 停机点名,裁成进项后票面税额还要再过 A-5 那道读花闸。
VAT_UNREADABLE = "vat_unreadable"
DIRECTION_PREFIXES = (DIRECTION_AMBIGUOUS, SALES_DIRECTION_UNHANDLED, VAT_UNREADABLE)

# 自动判定的本方销项票 flag_reason(MC1-c.1):seller==自家税号/名集 → sort 归 SALES_DOC 堆,
# 默认 flagged 留一次人工过目(拍板① · 配 MC1-b 批量键盘流一键确认),不再判死为 unknown。
# 刻意不进 DIRECTION_PREFIXES:它是「机器已判本方销项」而非「方向不明」,reconcile R1 不把它
# 当 unresolved 停机(佐证聚合不阻断出税),人工仍可 assign_kind 改判(客户拍错票的兜底)。
SALES_DOC_REVIEW = "sales_doc_review"


def replay_records(events: list[dict]) -> dict:
    """按 item_id 合并回放 human_decision → {item_id: {"event_id", "payload", "actor", "at"}}。

    payload 为合并槽(方向 kind 与金额 decision/values 并存):assign_kind 只写 kind 槽——此前若整
    记录是 NON_COUNTING(剔除/豁免)则作废重来(改主意重新定向);其余动词 update 金额槽,kind 槽
    保留。event_id/actor/at 取该 item 最新一条贡献事件的元数据。wrapper 形状对齐
    evidence.replay_items_by_type:消费方读 rec["payload"] 即拿合并 payload,读法零改动。
    """
    out: dict = {}
    for e in events:
        if e.get("event_type") != EVT_DECISION:
            continue
        p = e.get("payload") or {}
        iid = p.get("item_id")
        if not iid:
            continue
        prev = out.get(iid)
        payload = dict(prev["payload"]) if prev else {}
        if p.get("decision") == ASSIGN_KIND:
            if payload.get("decision") in NON_COUNTING:
                payload = {}  # 豁免/剔除后又改判方向=改主意,旧的不计入裁决作废
            payload["kind"] = p.get("kind")
            payload.setdefault("decision", ASSIGN_KIND)
        else:
            payload.update({k: v for k, v in p.items() if k != "item_id"})
        out[iid] = {
            "event_id": e.get("id"),
            "payload": payload,
            "actor": e.get("actor"),
            "at": e.get("created_at"),
        }
    return out


def payload_view(records: dict) -> dict:
    """replay_records 输出 → {item_id: 合并 payload}。守恒桶/闸只吃 payload 不要元数据,此前
    各调用点各写一遍拆壳推导——收敛到此,管线里只流转一种形状语义。已有 records 的双需调用方
    (回放一次,元数据/payload 各取所需)用本视图,别再 replay 第二遍。"""
    return {iid: rec["payload"] for iid, rec in records.items()}


def replay_payloads(events: list[dict]) -> dict:
    """事件流 → payload 视图(只需 payload 的单需调用方一步到位)。"""
    return payload_view(replay_records(events))


# 合并裁决的终态仲裁结果(terminal_of 返回值第一元)。
TERMINAL_WAIVED = "waived"
TERMINAL_EXCLUDED = "excluded"
TERMINAL_ASSIGNED = "assigned"
TERMINAL_PENDING = "pending"


def terminal_of(payload: dict | None) -> tuple[str, str | None]:
    """合并 payload 的终态仲裁 → (terminal, kind)。优先序单源:豁免 > 剔除 > 已定向 > 待裁决。

    P0-0 把回放归了源,但「kind 槽与 NON_COUNTING 并存时谁说了算」曾散回各消费方自裁且互相
    矛盾(守恒桶判 EXCLUDED、排除投影却按 kind 在场放行离堆)——终态问题一律问这里。
    """
    p = payload or {}
    decision = p.get("decision")
    if decision == WAIVE:
        return TERMINAL_WAIVED, p.get("kind")
    if decision == EXCLUDE:
        return TERMINAL_EXCLUDED, p.get("kind")
    if p.get("kind"):
        return TERMINAL_ASSIGNED, p.get("kind")
    return TERMINAL_PENDING, None


def kind_of(item: dict, records: dict) -> str:
    """人工方向裁决压过分类 kind,不回写 item 行(kind 槽独立于金额裁决)。records 为
    replay_records 的 wrapper 输出;无裁定方向则回落 item 自身 kind。"""
    payload = (records.get(item["id"]) or {}).get("payload") or {}
    return payload.get("kind") or item["kind"]


# items.kind 的「未定堆」值。与 kinds.UNKNOWN 同值——本模块守零依赖(见模块头),照 assign_kind
# 那几个 kind 常量的先例在此复制,不 import kinds。
_UNKNOWN_KIND = "unknown"


def is_direction_channel(item: dict, ruled_kind: str | None) -> bool:
    """这件走不走方向裁决通道 —— R1 收编(reconcile_gates.direction_items)与守恒归桶
    (conservation._bucket_of)共用这一份判据。

    两个分支管不相交的两类件:前缀命中 = 机器判了方向不明、人还没裁(必须进通道才会被
    _apply_direction 点名 unresolved,否则 R1 静默少算);ruled_kind 在场 = 人已裁过,
    不管机器当初为什么 flag(ocr_error:* 这类也算)。

    此前两处各写一份、靠 docstring 里一句「与对方同口径」维系同步,不同步一次的后果就是
    「人裁了 → R1 不收编 → 守恒闸压回待裁决 → 裁多少次都出不了包」。判据只留这一处。
    """
    if item.get("kind") != _UNKNOWN_KIND:
        return False
    return bool(ruled_kind) or str(item.get("flag_reason") or "").startswith(DIRECTION_PREFIXES)
