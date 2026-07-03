# 主动触达(月结/报税提醒)· 设计 + 施工(v1:每月一条 VAT 申报截止提醒)

> 2026-07-03 · P2 backlog 第四件。现状唯一主动推送=对账完成回推(worker finally 挂
> line_notify);"异常主动说"已存在(exception_high + notification_rules 用户自建规则 opt-in),
> 真缺口=**没人提醒月结/报税**。侦察结论带 file:line 见本窗交接。

## v1 范围(刻意最小)

**每月 10–15 日窗口,给绑定 LINE 的用户发一条**:「别忘了申报上月 VAT(ภ.พ.30),
纸质 15 号截止;想看上月汇总直接问我」——四语确定性文案,语言跟随对话
(line_lang.card_lang)。不带金额数字(不做跨租户重计算,想看数字用户一句话问 Agent 即得,
这正是 Agent 的入口教育)。

落选(v2 再议):带上月汇总数字(要跨租户逐户算)、按 tax_filings 底稿算真实待缴
(只覆盖用过报税模块的租户)、异常主动说(已有 opt-in 路)。

## 触发与防骚扰(push 是花钱面,防线必须硬)

- **无 cron 复用现有 tick**:挂 `background_loops.run_recovery_tick`(erp_retry 30s cadence
  "顺带跑"既有先例;startup.py 满线不碰)。进程内 1h 节流 + 日窗口先判(无 DB 免费退出)。
- **每用户每期恰一条**:`notification_logs` 做去重台账(template_code=`tax_due_nudge`·
  event_ref=期号 YYYY-MM·发送前查有即跳),重启/多 worker 不重发。
- **闸 `agent_proactive_nudge` 默认关**(per-user 判):关=一条不发现状不变;
  金丝雀 skin+163 → 真机人类门 → 放量。LINE push 免费 500 条/月,v1 每用户每月 1 条,
  当前用户量级下远够;放量前在本文档记一笔量级预估。
- 逐用户 try/except,单户失败不连坐;发送结果 sent/failed 全落台账(可审计)。

## 验收

- 单测:窗口外不发/闸关不发/去重不重发/发送落台账/单户异常不连坐。
- 人类门(真机):prod 一次性脚本对 skin 强制触发 → LINE 收到四语正确的一条提醒;
  同期再触发不重发(去重证明)。验过等 7/10 自然窗口真跑一轮再放量。
