# 06 · Pearnly 卡片锚定动作框架(Anchored Action Framework)

> 2026-06-19 Zihao 拍板。LINE 命令路由的【统领原则】—— 改/撤/删/恢复/记账全归它管。
> 一句话:**用户引用哪张卡,Pearnly 就只处理哪张卡;没引用时才智能判断,判断不稳就问。**
> 这是 LINE 会计助手变聪明的关键:不是多会聊天,而是它清楚【这句话在处理哪一张票/哪一笔账/哪个上下文】。

## 0. 铁律(决策树)

```
用户发一句操作(改/撤/删/恢复/补料…):
├─ 有引用(reply 某张卡)→ 【强锚定 · Context Lock】
│    · 只用这张卡绑定的 doc_id,只围绕它理解
│    · 绝不换对象、绝不新建一笔、绝不误删别的
│    · 按这张卡【当前真实状态】能做的动作执行(resolve_card_state)
│    · 不是card动作的话(如发了句普通记账)→ 仍锚定:问"要对这张做什么?",不落新单
│    · 遇阻(已入账/已撤/已结期/无权限/过期)→ 诚实说明 + 给下一步入口,不硬做
│
└─ 无引用 → 【智能解析 · Confidence-Based Intent Routing】
     · 解析(动作, 目标)各自带置信度
     · 目标明确(唯一近单 / "上一笔/刚才那个" / 第N笔)且动作明确 → 高置信直接执行
     · 目标不明确(多张近单)→ 列候选追问"是 PTT、7-11 还是 OfficeMate?"
     · 追问后用户回答(第二张 / 7-11)→ 继承 pending,不当新任务【Dialogue State Tracking】
     · 破坏性动作低置信 → 永远问,不猜着删
```

**四句产品铁律:** 有锚定不猜;没锚定高置信执行;没锚定低置信追问;追问后回答沿用 pending context。

## 1. 有引用:强锚定(Context Lock / Scoped Action)

- 入口已有 `services/expense/line_stale_ref.locate_clarify_target`(引用→锁 doc_id→判状态)。
- 本框架**强化**:只要本轮有 quoted_message_id,**整句都归这张卡**,在记账/大脑之前拦截:
  - card 动作(改字段/删/撤/恢复/查看)→ 按状态执行(Slice 1/2 已做)。
  - 非 card 动作(看着像新记账、闲聊)→ **不落新单**,回"要对这张(฿X·卖家)做什么?改金额/分类/删除/查看"。
  - 状态阻碍 → 诚实 + 选项(撤销入账 / 打开详情 / 联系会计复核)。
- ★这是当前缺口:引用一张卡 + "咖啡 65" 现在会**另记一笔**(忽略锚)→ Slice 3 收口。

## 2. 无引用:置信度解析(Entity Resolution + Confidence Gating)

目标置信度(target_confidence)信号:
- 近窗口内**唯一**一张近单 → 高。
- 明确指代词("上一笔/刚才那个/最近/ล่าสุด")→ 指向 last → 高。
- "第N笔"+ 已查明细列表 → 高(命中列表)。
- 多张近单 + 无指代 → 低 → 列候选问。

执行规则:
- 目标高置信 + 动作明确 → 执行(破坏性动作仍走现有确认/可恢复)。
- 目标低置信 → **列候选**(最近 3–5 张:日期·卖家·฿额)让用户选,不猜着删。
- 动作不明确(只说"那个")→ 问要做什么。

## 3. 追问后:对话态继承(Dialogue State Tracking)

- 列候选问"改/删哪张?"时,存 pending(候选 doc_id 有序列表 + 待执行动作)。
- 用户回"第二张 / 7-11 / B" → 命中候选 → 继承动作执行,**不当新任务**。
- 复用 `conversation.pending`(detail:<ids> 已有"第N笔"机制)→ 扩成 (action, [ids]) 待选态。

## 4. 现状对照 + 缺口

| 能力 | 现状 |
|---|---|
| 引用→锁 doc_id 不回落别单 | ✅ Slice 1 |
| 卡片状态(活/被改/撤/删)处理 | ✅ Slice 1 + resolve_card_state |
| 引用死单→恢复闭环 | ✅ Slice 2a(撤销单)· ⏳ Slice 2b(草稿) |
| **引用→强制围绕·不落新单·不换对象** | ❌ Slice 3 |
| **无引用 置信度猜目标** | ❌ Slice 4 |
| **猜不准→列候选追问** | ❌ Slice 4 |
| **追问答案继承 pending** | ⚠️ 部分(第N笔有·猜目标追问没有)→ Slice 4 |

## 5. 分片

- **Slice 2b(进行中)**:草稿软删 + 恢复(补全恢复闭环)。
- **Slice 3 · 强锚定收口**:有引用 → 整句归这张卡,非 card 动作不落新单/不换对象/遇阻给选项。完成"锚定"半。
- **Slice 4 · 无引用智能解析**:置信度猜目标 + 列候选追问 + 追问答案继承 pending。完成"智能"半。
- 完成后:**用户引用哪张就只动哪张,没引用就带置信度猜、猜不准就列着问** —— 框架闭环。

## 6. 设想场景(≥20·维护见 04 覆盖表)

引用活单"改成办公用品"→直接改;引用"删除"→只删这张草稿;引用已入账"删除"→"已入账不能直接删·撤销/详情/复核";
引用 + "咖啡65"(像新单)→不落新单·问要对这张做什么;无引用"把刚才那个改成油费"(唯一近单)→高置信直接改;
无引用"那个删掉"(3张近单)→列 PTT/7-11/OfficeMate 问;问后答"第二张"→删第二张;答"7-11"→删 7-11 那张;
无引用"删掉"(无近单)→"没有可删的";破坏性低置信→永不猜删;引用过期 ref→查明细重选;
引用别套账卡→按 ref.ws;引用 + 闲聊→仍锚定问;指代"上一笔"→last;"最近三笔"→批量(detect_bulk_undo)。

## 7. 可引用卡片契约(Referable Card Contract)

> 强锚定的前提:用户引用的那张卡【必须】在系统里有锚点。否则引用即 `ANCHOR_EXPIRED`。
> 真机 bug(2026-06-20):拍票出"⚠️请确认"草稿卡、重复图重发卡、撤销终态卡 —— 引用它们说
> "金额改X / 删 / 谢谢 / 恢复" 全回 ANCHOR_EXPIRED。根因:这些卡走异步 push / `reply_messages_context`
> 发出,没登记 `message_id→doc_id`。

**契约:** 凡是【代表一张真实单据】的卡(入账 posted / 草稿 confirm / 可能重复 dup / 已撤销
voided / 已丢弃 discarded 终态),**发出时必须登记可引用锚点**(`line_message_refs.record`)+ 草稿/
入账/可能重复卡设焦点(`line_correct._set_active`)。不分状态:终态卡也登记(引用它仍可说"恢复");
引用后【允许的动作】由 `resolve_card_state`(当前真实状态)裁决,不由发卡时的状态写死。

**实现:** 统一走 `line_booker.anchor_card(sent, *, tenant_id, ws, line_user_id, doc_id, state, cur=None)`
—— 有 `cur`(调用方在事务中)用 `record` 不另开连接,无 `cur` 用 `record_safe` 自开;终态(voided/
discarded)只登记锚点不动焦点。拿不到 `sentMessages` id → 本次锚点缺(best-effort·绝不阻塞回执)。

**覆盖的出卡口(全部登记):** `emit_result_card`/`push_result_card`(reply/图片主路·原有 `_bind_refs`)、
图片重复快路 `line_image_fastpath._push_state_card`、终态卡 `line_card_actions._terminal_card`、
入账卡 `_send_posted`、改错重发卡 `send_state_card_reply`、缓存重建卡 `handle_ocr_cache_hit`。
