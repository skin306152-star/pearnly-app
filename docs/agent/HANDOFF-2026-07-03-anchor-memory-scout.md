# 接力 · 结构化跨轮记忆(anchors 接线)· 侦察已完成待实现

> 2026-07-03 · /loop 任务① 起步即被 Zihao 暂停 · **只做了只读侦察,零代码改动**
> 下次续做:直接从「设计/实现」开工,不必重跑侦察。闸默认关,走 PR→CI→合并→prod 验证流程。

## 目标

让「把刚才那张推进 ERP」「把它改成 80」「刚才那笔」能定位上一轮碰过的对象——
在用户**不引用消息、只用「刚才/这笔/那张」指代**时。

## 关键发现

- `AgentContext.anchors: dict`(`contracts.py:81`)字段**已存在,管道 bridge→loop→executor→slots 全通,只是没人灌水**。
- `slots._ground` 的 anchor 分支(`slots.py:47-49`)是**死代码**(没有 slot 用 `source="anchor"`)。
- 引用消息这条精确锚**已完整可用**:`quoted_message_id` → `line_message_refs.lookup()`(`line_message_refs.py:173-210`),webhook→bridge(`line_agent_bridge.py:269`)→write_sink 透传。anchors 补的是「不引用只口头指代」的缺口。
- 现有「上一笔」定位:`mentions_last`(闭集词表)→ `find_last_posted`(最近一笔 posted LINE 单)。
- 现有隐式焦点锚:改错后写 `correctactive:<ws>:<doc>` 进 `line_pending_entry`(15min TTL,`line_correct.py:148-166`),`maybe_bare_undo` 用它做「裸取消=最近那张卡」。
- `push_to_erp`/`push_status` 的 `executor._locate_doc`(`:155-190`):无 keyword 时**每轮实时重查** `list_ocr_history` 取 `items[0]`——这是 DB 查询非跨轮记忆。

## anchors 该存什么(每用户一行)

| 键 | 来源 | 主键 |
|---|---|---|
| last_history_id | list_ocr_history / _locate_doc | purchase_docs.id |
| last_entry_doc_id | record_expense 落单 | purchase_doc id |
| last_pushed_endpoint_id | push_to_erp | erp_endpoints.id |
| last_doc_ids(可选) | list_history 结果 | id 列表 + keyword |

## 存哪(定方案 B)

**新建轻量表,照抄 `line_pending_intents`**(`line_intent_store.py:22-30`):PK `(tenant_id, line_user_id)`、
`anchors jsonb`、`expires_at`(~45min)、`apply_tenant_rls`。每用户单行 upsert,last-write-wins。
- ✘ A(line_chat_history 加列):该表按消息行且删 24h 前,会把 anchor 滚掉,语义错配。
- ✘ C(复用 line_pending_entry):`missing` 字段已被改错态机多态重载,易相撞,TTL 仅 15min。

## 最小实现(改动面最小方案 = executor 兜底,不动 manifest slot)

1. **新增** `services/line_binding/line_anchor_store.py`:表 + `get/set` + RLS + `ensure_table` 幂等;`startup.py` 注册 ensure。
2. **改** `core/feature_flags.py`:加 `agent_anchor_enabled_for(uid)`(照抄 `agent_write_enabled_for`)。默认关。
3. **改** `line_agent_bridge.py`:建 ctx 前 `load` anchors 传 `AgentContext(anchors=...)`;`handle_turn` 返回后从 `ctx.anchors` 持久化(**gated**,闸关则不 load/不传/不落,逐字节现状不变)。
4. **改** `loop.py`:工具成功后从 `result.data` 抽 id 收集进 `ctx.anchors`(纯内存,不直接落库)。⚠️ loop.py 已 495/500 满线——收集逻辑放新 helper 文件(如 `services/agent/anchor_collect.py`),loop 只调一行。
5. **改** `executor._locate_doc`:无 keyword 时优先 `ctx.anchors["last_history_id"]` 再回落 `items[0]`。

## 风险闸(实现时必做)

- **多租户**:新表 `apply_tenant_rls`,读写走 `get_cursor_rls(tenant_id)`。
- **TTL**:45min,`expires_at` 过滤。
- **anchor 指向对象已删/改**:**读时必复核**,复用现成死单安全网 `resolve_card_state`/`follow_corrected_from_to_live_leaf`(`line_message_refs.py:220-271`)、`_is_live`(`line_correct.py:169`)——SUPERSEDED 落最新活单、VOIDED/DISCARDED 诚实拒绝(事故先例 `line_stale_ref.py:6-8`)。绝不盲信。
- **并发同用户**:单行 upsert 天然安全。

## 验证要求

- 新文件 ≥1 测试;`_locate_doc` anchor 优先/回落/失效复核三条守门。
- 真机(163 号):发图识别一张 →「把刚才那张推进ERP」不带票号 → 命中同一张;再「改成80」命中同笔。
- 闸开 allowlist 金丝雀 → 放量。
