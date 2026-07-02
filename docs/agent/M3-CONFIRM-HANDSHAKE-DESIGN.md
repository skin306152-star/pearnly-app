# M3 confirm-first 握手状态机 · 设计(LangGraph HITL checkpoint 范式)

> 2026-07-02 · Zihao 点题:loop.py 缺多轮「先复述+确认」握手状态机,参考 LangGraph
> human-in-the-loop checkpoint 范式(可中断、带持久状态的多轮确认)。本文是施工前方案
> (agent 前门属主路径,按铁律先报方案)。

## 0 · 现状与缺口(2026-07-02 实测)

- `ToolSpec.confirm` 字段定义了,**loop.py 从未消费**(全仓 grep 只有 push_to_erp 标 True)。
- push_to_erp 的确认是**工具内部自带**的专用机械(备料 → flex 卡 + nonce 按钮 → postback
  执行),不是 loop 层能力——每加一个需确认的工具都得重造一套卡片机械。
- 其余写工具(直录/冲销/改错)靠"可逆 + 旧路确定性闸"豁免确认,合理但不可扩展:
  DMS 建订车单、批量操作、对账写动作等下一批能力都需要确认,不能逐个手搓。

**缺的是**:loop 层通用的「复述 → 落检查点 → 等下一条消息 → 确认执行 / 否定取消」状态机。

## 1 · LangGraph 概念 → Pearnly 落位

| LangGraph | Pearnly 落位 |
|---|---|
| `interrupt()` 中断执行 | loop 执行工具前看 `spec.confirm=True` → 不执行,持久化检查点,回复复述文案,本轮结束 |
| checkpointer(持久状态) | 新表 `line_pending_actions`(照 `line_pending_intents` 范式:tenant+line_user 单活动行、TTL、DELETE RETURNING 单发单用) |
| `thread_id` | `(tenant_id, line_user_id)` —— LINE 会话天然线程 |
| `Command(resume=value)` | 下一条 inbound 文本先过 **resume 闸**(在 bridge 进大脑之前):确认词 → 取走检查点执行;否定词 → 取消+回执;其它 → 取消旧检查点(诚实带一句"上一件已取消")后正常进大脑 |
| interrupt 可带 payload | 检查点存 `{tool, args(已接地校验过的), restate_text, created_by_turn}` —— 恢复时**不重跑大脑**,直接执行存好的调用(防复述与执行不一致) |

## 2 · 状态机

```
           工具调用(spec.confirm=True 且机器闸开)
                     │ interrupt
                     ▼
   ┌── PENDING(检查点落库 · 复述已发 · TTL 15min)──┐
   │            │              │                    │
 确认词       否定词        其它消息              TTL 过期
   │            │              │                    │
   ▼            ▼              ▼                    ▼
CONFIRMED   CANCELLED     SUPERSEDED            EXPIRED
(执行存好   (回执"已取消") (取消+一句诚实注记,   (下次消息时静默清,
 的调用,                   新消息正常进大脑)      不打扰)
 结果回执)
```

- **单活动检查点**:同 intents,新的覆盖旧的(改主意=以最新为准)。
- **确认分类**:第一层确定性多语词表(确认/OK/ใช่/ยืนยัน/はい/好/推吧…;否定:取消/ไม่/算了…),
  词表未命中**不猜**→ SUPERSEDED(宁可让用户再说一次,不把闲聊当确认——钱路红线)。
  大脑不参与确认判定(与 image_intent"大脑无 push 权"同一条红线)。
- **幂等**:take = DELETE RETURNING;执行层复用现有三层幂等(nonce/近期成功/push_logs)。
- **与卡片机械的关系**:按钮卡(push)是**结构化 resume**,保留不动;本状态机服务
  没有卡片的文本确认场景。同一工具可两者并存(卡片优先,文本"确认"两字也认——
  resume 闸和 postback 消费同一检查点,谁先到谁执行,后到的撞 used 幂等)。

## 3 · 接线点(全部 additive · flag 默认关 = 现状逐字节)

1. `line_pending_actions` 表 + store(照 line_intent_store 克隆:ensure/自愈/TTL/take/peek)。
2. `loop.py` 执行工具处:`if spec.confirm and machine_on: return TurnResult(confirm_pending, restate)`
   (新 TurnResult 终态,bridge 据此存检查点+发复述)。
3. `line_agent_bridge.try_agent_turn` 入口最前:resume 闸(peek→分类→take 执行/取消/让位)。
4. flag `agent_confirm_machine`(fail-closed;关=push 现有卡片路照旧,其余工具照旧不确认)。
5. 复述文案:copy_map 加 `agent.confirm.generic`(四语,槽位=动作人话+对象+金额)。

## 4 · 首批消费者(机器先行,能力跟上)

| 工具 | 现状 | 上机器后 |
|---|---|---|
| push_to_erp | 卡片确认(不动) | 附加文本"确认"同义通道 |
| DMS 建订车单(待建) | 无 | 天生 confirm=True,直接用机器 |
| 批量重推/批量撤销(待建) | 无 | 同上 |
| record_expense 低置信档 | 降草稿卡 | 维持现状(卡片已够),不强上 |

## 5 · 验证(与 LI 同一套方法论)

- 状态机单测:五态迁移全覆盖 + 红线(未确认绝不执行 / 分类器崩=不执行 / 双确认幂等 /
  TTL 过期不执行 / SUPERSEDED 必带诚实注记)。
- 语料:确认词多语矩阵(含"好的推吧""ยืนยันเลย"等自然语)+ 陷阱词("不确认""确认一下再说"
  ——含确认字样但语义存疑 → 词表精确匹配不含糊,存疑=SUPERSEDED)。
- 模拟对话舱:多轮剧本(复述→隔一条闲聊→再确认=EXPIRED/SUPERSEDED 语义核对)。
- 500 轮混沌:随机消息序列,不变量=无检查点绝不执行、执行次数 ≤ 确认次数。

## 6 · 风险与回滚

- 风险:resume 闸挡在所有 LINE 文本最前——任何崩溃必须 fail-open 到现状路
  (try/except 全包,闸崩=当没有检查点)。
- 回滚:关 flag = 机器整段休眠;表保留无害。
- 不做:跨会话恢复语义(LINE 单线程即会话)、检查点历史栈(单活动行够用)、
  大脑参与确认判定(红线)。
