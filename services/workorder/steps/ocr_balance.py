# -*- coding: utf-8 -*-
"""工单 OCR 接用户钱包(余额闸 + 逐件扣费)· 与 ocr_cost_cap 平级,互不改写。

两笔钱分得清,两个原因码绝不合并——出路完全不同:
  · ocr_cost_cap = 我们付给模型厂商的内部成本(ai_usage.cost_thb)→ stuck
    ocr_cost_cap_exceeded,意思是「我们这边跑超预算了」,人工 /run 重给预算;
  · 本模块 = 用户钱包(tenant_credits.balance_thb)→ stuck insufficient_balance,
    意思是「你该充值了」,充完点继续。

口径与老站(/home 识别中心)一字不差,本模块只管「工单侧怎么接线」:
  闸 = db.get_billing_status_combined(services/billing/account_status.py 单一事实源,含豁免
       直通与查库异常 fail-open——查库炸了不挡用户,老站什么样这里什么样);
  扣 = db.charge_ocr(services/billing/charge.py 单原子事务 + SELECT FOR UPDATE + 三表齐写)。
定价、扣费、豁免判据一行都不重写。

计费单位 = 一件一页,且管线只跑一页(ocr_pipeline.read_first_page 传 max_pages=PAGES_PER_ITEM)。
两者必须同步改:只收一页却让管线按默认 50 页跑,我们付 30 页的钱、用户付 1 页的钱,同一份票
从 /home 挪到 /ai 就打 1/30——收入漏损 + 可套利的定价洞。收几页就烧几页。

身份锚(闸与扣费必须是同一个人):豁免 users.is_billing_exempt 是逐人判的(account_status),
闸看上传人、扣费看账套 owner 会让「给这个客户开豁免」两头落空——置在 owner 上则 classify 不扣
但操作员传料仍 402,置在操作员上则传料放行而 classify 照扣。两处一律走 resolve_billing_user。

幂等锚(会计看到多扣一次就不再信任):
  ① 只处理 pending 件是 classify.run 的幂等基石——reaper 收尸续跑 / 人工 /run / 补料自驱
     都打不到已定堆件,重跑天然不重扣;
  ② 复用件(ocr_reuse 命中,reused_from 非 None)零 OCR 零成本 → 不扣。与老站「文件哈希缓存
     命中直接 return、走不到闸也走不到扣」是同一条规则的两种形态;
  ③ OCR 抛异常 / 撞 quota 待补的件没有读数 → 不扣(失败不收钱)。
history_id 不是幂等键(老站也不是,它只是流水描述里给 usage-history 做 LIKE join 的关联串)。

扣费走同步 charge_ocr(不是 charge_ocr_async 的 fire-and-forget):classify 跑在后台 run 的
worker 线程里,同步扣才能让下一件的余额复查看到刚扣掉的钱;worker 线程无 event loop,派发式
异步扣在这里会静默漏扣(services/ocr/recognize/persist.py 踩过这个坑)。

余额回查同样走 get_billing_status_combined 自己的连接(独立短事务),绝不在长活步事务
ctx.cur 里攥锁——钱表带 SELECT FOR UPDATE,比 ai_usage 更经不起攥(死锁根因见 ocr_cost_cap)。
"""

from __future__ import annotations

import logging
import os
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Optional

from services.workorder.steps import ocr_ledger

logger = logging.getLogger(__name__)

# stuck 原因码 = 全站计费闸统一码(services/billing/account_status.py 单一事实源),前端
# static/ai/ai-fail-render.js 认的也是这个词,不另造工单专属码。
STUCK_REASON = "insufficient_balance"

# 一件计一页、也只烧一页(见模块 docstring 的计费单位);kind 用老站的 "pdf" 档(页价)。
PAGES_PER_ITEM = 1
_CHARGE_KIND = "pdf"

_FLAG_ENV = "PEARNLY_WORKORDER_BILLING"
_TRUTHY = ("1", "true", "on", "yes")


def enabled() -> bool:
    """/ai 识别链路计费总闸。默认关:今天 /ai 邀请用户开箱余额 0(发号只开门不送钱),
    闸一开全员当天识别不了——先清点存量租户余额 / 发启动额度 / 设豁免,再置 1 开闸。
    急停 = 把 env PEARNLY_WORKORDER_BILLING 改回 0 重启(一行,不改码)。"""
    return os.environ.get(_FLAG_ENV, "0").strip().lower() in _TRUTHY


def _default_billing_status(user_id, tenant_id) -> dict:
    from core import db

    return db.get_billing_status_combined(user_id, tenant_id)


def _default_charge_ocr(user_id, tenant_id, kind, units, history_id, description) -> dict:
    from core import db

    return db.charge_ocr(user_id, tenant_id, kind, units, history_id, description)


def _default_estimate(pages_used: int, pages: int) -> float:
    from core import db

    return float(db.estimate_pdf_cost_thb(pages_used, pages))


def resolve_billing_user(cur, tenant_id, workspace_client_id) -> Optional[str]:
    """闸与扣费共用的计费身份 = 客户账套 owner user(见模块 docstring 的身份锚)。

    解不出(未绑客户 / 无 owner / 查询出错)→ None:按租户收钱、永不豁免,与 Wallet 在
    owner 缺失时的回落逐字同口径(from_ctx 的 user_id 也是 None)。
    """
    return ocr_ledger.owner_user_of_client(cur, tenant_id, workspace_client_id)


def _shortfall(cost, balance) -> Optional[Decimal]:
    """还差多少才够跑完;够跑(≤0)→ None,那一句就别说,不报「还差 0.00」。钱全程 Decimal。"""
    short = Decimal(str(cost or 0)) - Decimal(str(balance or 0))
    return short.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if short > 0 else None


def batch_denial(billing_user_id, tenant_id, file_count: int) -> Optional[dict]:
    """入料端点的整批预检:够跑 → None;不够 → 402 的 detail 体(老站四键 + shortfall)。

    /ai 两条入料路径(工单补料 / 总台建合同)共用这一条闸,行为不许分叉。billing_user_id 由
    resolve_billing_user 给,不许直接拿登录用户——那是另一个人。

    闸关 / 无料 / 豁免 / 查库异常一律放行:计费问题绝不把「传料」这个动作本身弄挂,余额真见底
    还有 classify 逐件复查兜底。预估按一件一页(整批 file_count 页)。

    shortfall(还差多少)是给失败卡回答「充多少够」的:余额够却仍被拒(非余额原因)时为 null,
    前端据此少说那一句——报一个算错的缺口比不报更糟。
    """
    if not enabled() or int(file_count or 0) <= 0:
        return None
    try:
        user_id = str(billing_user_id) if billing_user_id else None
        status = _billing_status(user_id, str(tenant_id) if tenant_id else None) or {}
        if status.get("allowed") or status.get("is_exempt"):
            return None
        used = int(status.get("pages_used_this_month") or 0)
        cost = _estimate(used, int(file_count))
        balance = status.get("balance_thb", 0.0)
        short = _shortfall(cost, balance)
        return {
            "code": STUCK_REASON,
            "balance": balance,
            "estimated_cost": cost,
            "pages_used_this_month": used,
            "shortfall": float(short) if short else None,
        }
    except Exception as exc:  # noqa: BLE001 - 预检失败按放行(fail-open,与老站闸同口径)
        logger.warning("工单补料余额预检跳过(放行): %s", exc)
        return None


def from_ctx(ctx, owner: Optional[dict], images: list, reused: dict) -> Optional["Wallet"]:
    """按工单归属建钱包账;闸关 / 本批没有要真烧的件 → None(零查库零扣费,现状逐字节不变)。

    全复用批不建账,是照老站「指纹缓存先于余额闸」——命中不产生新成本,余额 0 也该给复用。

    owner["user_id"] 与闸的 resolve_billing_user 出自同一个查询(ocr_ledger.owner_user_of_client),
    豁免因此在两处判到同一个人身上。

    owner 解不出(工单未绑客户 / 客户无 owner user)不能像识别台账那样优雅跳过,跳过等于免费:
    work_orders.tenant_id NOT NULL 保证租户永远在,charge_ocr 的 user_id 允许 NULL,故回落成
    「按租户收钱,流水不记到人头上」。
    """
    if not enabled():
        return None
    if not any(it["id"] not in reused for it in images or []):
        return None
    return Wallet(user_id=(owner or {}).get("user_id"), tenant_id=str(ctx.tenant_id))


def _item_name(item: dict) -> str:
    return item.get("original_name") or Path(item.get("file_ref") or "").name or str(item.get("id"))


class Wallet:
    """一次跑批的用户钱包:还够不够跑(exhausted)+ 一件消费完就结账(settle)。

    余额只可能因为自己扣钱而变少,故状态缓存到「扣过一笔」才标脏、下次才回查真库:复用件、
    失败件不脏,不为它们多打一次 SELECT(老站一次 SELECT 三表 JOIN 也不便宜)。
    """

    def __init__(self, *, user_id, tenant_id: str):
        self._user_id = user_id
        self._tenant_id = tenant_id
        self._status: Optional[dict] = None

    def _refresh(self) -> dict:
        try:
            self._status = (
                _billing_status(str(self._user_id) if self._user_id else None, self._tenant_id)
                or {}
            )
        except Exception as exc:  # noqa: BLE001 - 查库炸了不挡用户(继承老站 fail-open)
            logger.warning("工单余额回查失败(放行不挡跑批): %s", exc)
            self._status = {"allowed": True, "is_exempt": False, "error_code": "lookup_error"}
        return self._status

    def status(self) -> dict:
        if self._status is None:
            return self._refresh()
        return self._status

    def exhausted(self) -> bool:
        """钱花完了没(豁免恒 False;查库异常 fail-open 恒 False,不把跑批堵死)。"""
        st = self.status()
        return not (st.get("allowed") or st.get("is_exempt"))

    def shortfall_reason(self, items_left: int) -> str:
        """停机原因码,尽量带上「还差多少」:"insufficient_balance:6.00"。

        工单卡要回答「充多少够把剩下的跑完」,只给一个裸码等于让会计自己去猜。缺口 =
        剩余件数按当月阶梯价的估价 − 现有余额,与入料端 402 的 estimated_cost 同一条定价
        (services/billing/pricing,Decimal 全程,不用 float 算钱)。

        算不出就退回裸码(前端对无参数码有不带金额的降级句):少说一句,好过报一个错数字。
        """
        try:
            st = self.status()
            pages = max(0, int(items_left or 0)) * PAGES_PER_ITEM
            if pages <= 0:
                return STUCK_REASON
            used = int(st.get("pages_used_this_month") or 0)
            short = _shortfall(_estimate(used, pages), st.get("balance_thb"))
            return f"{STUCK_REASON}:{short}" if short else STUCK_REASON
        except Exception as exc:  # noqa: BLE001 - 估不出缺口不值得把停机诊断本身弄挂
            logger.warning("余额缺口估算失败(原因码退回裸码): %s", exc)
            return STUCK_REASON

    def settle(self, item: dict, ocr, reused_from, history_id) -> bool:
        """一件消费完 → 该扣的扣掉;返回「钱花完了,别再投料」。

        复用件(reused_from 非 None)与失败件(ocr 不是读数 dict)按幂等锚 ②③ 不扣。
        """
        if reused_from is None and isinstance(ocr, dict):
            self._charge(item, history_id)
        return self.exhausted()

    def _charge(self, item: dict, history_id) -> dict:
        """按老站同一定价扣同一个钱包(单原子事务在 charge_ocr 内),扣完标脏等下次回查。

        扣费失败只 log 不抛:OCR 已经跑完了,把一个已完成的识别翻成崩溃对用户毫无价值
        (与老站 charge_ocr_async 吞错同口径,漏扣有 log 可追)。
        豁免账号在这里就早返(同 entrypoints.charge_successful_ocr 的先例),不劳 charge_ocr
        再走一遍;它们的状态恒不脏,复查也不会多打 SELECT。
        """
        if self.status().get("is_exempt"):
            return {"ok": True, "charged_thb": 0.0, "exempt": True}
        hid = str(history_id) if history_id else None
        suffix = f" · {hid[:8]}" if hid else ""
        desc = f"OCR {_CHARGE_KIND} · {_item_name(item)}{suffix}"
        try:
            out = (
                _charge_ocr(self._user_id, self._tenant_id, _CHARGE_KIND, PAGES_PER_ITEM, hid, desc)
                or {}
            )
        except Exception as exc:  # noqa: BLE001 - 已完成的识别不因扣费异常翻成崩溃
            logger.error("工单 OCR 扣费异常(item=%s): %s", item.get("id"), exc)
            out = {"ok": False, "error": str(exc)[:200]}
        if not out.get("ok"):
            logger.warning("工单 OCR 扣费失败(item=%s): %s", item.get("id"), out.get("error"))
        self._status = None  # 标脏:下一件的 exhausted() 回查真库,不吃过期余额
        return out


# 注入点:模块级绑定,测试用 ocr_balance._xxx = fake 替换,绝不触真库/真钱路径。
_billing_status = _default_billing_status
_charge_ocr = _default_charge_ocr
_estimate = _default_estimate
