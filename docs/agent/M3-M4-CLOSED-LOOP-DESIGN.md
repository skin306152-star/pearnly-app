# M3/M4 闭环设计 · LINE 对话 Agent「真正干活」总方案(Phase 0 · 待审批)

> 交付物性质:**纯设计文档,未改任何产品代码**。每条结论带真实文件/行号(2026-07-02 通读核实)。
> 审批后才进入实现阶段;实现全部在独立分支 + 默认关的 feature flag 后面,推 ERP 接真钱路与
> 真机 E2E 永远是人类的门。
>
> 要解决的核心痛点(产品负责人原话):**"产品做好后,里面很多 bug、对话翻车、新旧大脑冲突,
> Agent 的 LINE 对话框不能真正干活、干不好活。"** 本方案三条主线正面回应:
> ① 验证 harness 先行(§4,抓翻车的探测器);② 新旧大脑冲突消解成单一决策者(§3);
> ③ 写能力(记账全家桶 + 推 ERP confirm-first)收进工具闭环(§6)。

---

## 1. 现状核实(逐条对代码验真伪)

### 1.1 里程碑摘要验证结果

| 摘要断言 | 核实 | 证据 |
|---|---|---|
| M0 钥匙闸已上线 | ✅ 属实 | `core/feature_flags.py:22-44`(`agent_enabled`/`agent_write_tools` 双闸,fail-closed);`services/platform_settings/store.py:91-107`(总闸+rollout+allowlist) |
| M1 插座已上线 | ✅ 属实 | `services/agent/` 全套:manifest 8 工具(`manifest.py:18-149`)、slots 接地闸(`slots.py:55-87`)、executor 7 只读+1 写(`executor.py:33-144`) |
| M2 换脑(真 agent 循环)已上线 | ✅ 属实 | `services/agent/loop.py:311-419` `handle_turn` 多步循环;LINE 接线 `services/line_binding/line_expense.py:75-93` → `line_agent_route.route_gated` |
| rollout=all 全量 | ⚠️ 代码验证不了(prod DB 状态) | 消费侧逻辑在 `store.py:97`(rollout=all→True);全量与否要上 prod 查:`SELECT value FROM platform_settings WHERE key='agent_enabled'`。按 2026-07-01 交接为 all,采信但实现阶段先复核 |
| record_expense 代码完成 | ✅ 属实 | `executor.py:121-141`(建草稿·金额过 `to_draft` 接地);`manifest.py:80-122`(`writes=True, confirm=False` 高置信直录);sink 装配 `line_agent_bridge.py:36-53`(`used_l2=False` → `line_expense.py:348` `confidence_band="high"` 直录) |
| agent_write_tools 已全开 | ⚠️ 同上,prod DB 状态,代码只见消费侧(`feature_flags.py:33-44`) |
| 记账没做真机验证 | ✅ 属实(无任何真机验证产物;模拟器只注入模型层) |
| push_to_erp 是桩 | ✅ 属实 | `executor.py:143-144` 返 `not_implemented_m1` |
| loop 只有 tool/reply/defer 三态、confirm 没消费 | ✅ 属实 | `loop.py:32`(LoopStep.kind 注释)、`contracts.py:34` 定义了 `confirm` 字段;全 `services/agent/` grep `confirm` 无一处执行路径消费;`copy_map.confirm()`(`copy_map.py:79-81`)是死代码 |

### 1.2 文档与代码不符处(接手窗口别被误导)

1. **`scripts/agent_sim.py` 已失效(stale API)**:`agent_sim.py:62-65` 期望 `handle_turn` 返
   `None`=defer,但 `loop.py:311-321` 现在恒返 `TurnResult` dataclass → 模拟器会把
   `TurnResult(kind='defer_record')` 当"回复"打印,defer 判定全错。交接说的 scratchpad
   `line_sim.py`/`line_sim_write.py` 已不存在(scratchpad 为空)。→ §4 的 harness 是重建,不是沿用。
2. **`M3-write-tools-confirm-plan.md` 引用了不存在的 `line_classify.is_confirm`**(§2.2):
   `line_classify.py` 只有 `is_cancel_intent:293`/`is_delete_intent:299`/`detect_text_lang:446`;
   真实的"是/否"判定是 `line_correct.py:48` 的 `_YES` 元组 + `try_confirm:380`。且该 plan 的文字
   握手方案已被修订①②推翻(确认走卡片按钮+nonce),本文 §6.2 以修订②为准重写。
3. **MASTER-PLAN 的 "qwen3.5↔gemini 可切" 已过时**:qwen 2026-07-01 废除。现状
   `brain.py:23-30` `AGENT_BRAIN_BACKEND` 未设 → 跟随全局 `OCR_LLM_BACKEND=vertex`
   (gemini-2.5-flash)。可插拔机制仍在,只是没有第二后端。
4. **能力盘点数字全部过时**:AGENT-CAPABILITY-INVENTORY 写 497 入口/87 区,MASTER-PLAN 写
   512/91;`python scripts/agent_capability_audit.py` 实测(2026-07-02)= **92 功能区 / 516 入口**
   (A:17 区 56 入口 · B:36 区 235 入口 · C:15 区 106 入口 · D:24 区 119 入口)。数字只信脚本。
5. **`agent_i18n.py:61-79` 的 `agent.confirm.record` 键已无消费场景**(修订②记账直录),
   `agent.confirm.push`/`agent.confirm.cancelled` 将由 §6.2 消费;键保留不删(i18n parity 闸)。
6. **交接第 29 行"真 qwen-flash 在'咖啡50'时…"的验证描述已失效**——大脑已是 gemini,真机验证
   的对象是 Vertex gemini-2.5-flash,不是 qwen。

### 1.3 一处设计层面的真实缺口(现状核实中发现,非文档所列)

**大脑故障期间,灰度(=全量)用户的文字记账整体不可用。**
`line_agent_route.py:72-76`:crash → 安全兜底一句并**消费本轮**;`line_expense.py:115-139`
的 L1 确定性直录(不依赖任何 LLM 的 `parse_expense` 路)对 gated 用户永远排在 Agent 之后,
crash 时到不了。设计初衷是"绝不掉旧路地雷"(治情绪句被问价格),但地雷是**旧 LLM 大脑的误路**
和 `amount_no_item` 反问池(`line_expense.py:125-127`),L1 确定性直录本身不是地雷。
→ 后果:Vertex 抖 5 分钟,全量用户"กาแฟ 50"只收到"我在呢~"且**没入账**,能力回退。
§3.4 给分级兜底方案(Zihao 拍板项)。

---

## 2. 能力全景与缺口(M4 清单的事实底座)

实测(§1.2 第 4 条):A 档 17 功能区 56 入口,已做成工具的只覆盖 5 区:

| 已有工具(manifest.py:18-149) | 覆盖功能区 |
|---|---|
| list_history / history_summary | report_routes |
| balance | billing_credits_routes |
| usage_this_month | billing_records_routes |
| list_notifications | notification_routes |
| list_workspaces / switch_workspace(B 档导航) | workspace_routes |
| record_expense(B 档写) | purchase_intake_routes |

**A 档未接的 12 个功能区**(对照 `agent_registry.json` 全部 A 区):

| 功能区 | 对话价值 | M4 处置(§5 详设) |
|---|---|---|
| erp_listing_routes | ★高:"那张推了没"是高频真问题 | 做工具 `push_status` |
| rd_routes | ★高:税号核验(泰国场景刚需) | 做工具 `rd_lookup` |
| knowledge_ask_routes | ★高:产品问答有真数据源,别让大脑瞎编 | 做工具 `ask_knowledge` |
| erp_express_account_routes | 中:查账套配置 | 做工具 `erp_accounts`(与 push_status 合并回执) |
| accounting_books_routes | 中:账本汇总 | 做工具 `books_overview` |
| auth_me_routes / me_routes | 中:我的套餐/资料 | 做工具 `my_plan` |
| erp_export_routes | 低:导出链接类,LINE 里给 deeplink | 登记豁免(引导 App) |
| export_routes / ocr_export_routes | 低:同上,文件下载去 App/网页 | 登记豁免 |
| inventory_report_routes | 低:单入口库存报表 | 缓,M4.5 |
| meta_aliases_routes | 非用户能力(元数据) | 登记豁免 |

**B 档 36 区 235 入口**:M3 只做两类(记账全家桶 + 推 ERP),其余 B 档(对账/销售/采购/订阅…)
按 MASTER-PLAN 顺序留 M4 之后逐个报方案,本文不展开。

**豁免机制**(防"漏了最后才发现"):`agent_registry.json` 的值从 `"A"` 扩成
`{"bucket":"A","agent":"tool:push_status"}` / `{"bucket":"A","agent":"exempt:export-file"}`
结构(向后兼容旧字符串);`scripts/agent_capability_audit.py` 加第二道核对——A 档区必须
`tool:*` 或 `exempt:*` 之一,否则 FAIL(§7 的 M4 闭环判据)。

---

## 3. 新旧大脑冲突消解(终态架构 + 迁移路径 + 契约测试)

### 3.1 现状:一句话最多经过 4 个决策层、2 次 LLM

gated 用户一条文字消息在 `line_expense.handle_expense_text` 里的真实决策序
(`line_expense.py` 行号):

```
:36  normalize + 记忆
:68  ① line_correct_flow.route      确定性改错状态机(最高优先·在 Agent 前)
:78  ② line_agent_route.route_gated 新大脑(loop.py·LLM #1)
        reply/card_sent/crash → 消费本轮
        defer_record/defer_edit/无余额 → 落下去 ↓
:95-156 ③ 旧 L1 确定性层             income 拦截 / parse_multi 多笔卡 /
                                     parse_expense 直录 / pending 补金额 / amount_no_item 反问
:158-178 ④ 旧 LLM 大脑               line_agent.understand()(LLM #2)+ _dispatch_agent
:180-199 ⑤ 无 LLM 兜底               query/support/问答/unknown 池
```

**冲突实锤**(每条都能在代码里指到):

- **双 LLM 解读同一句话**:模型 defer(reason=edit)→ ④ `understand()` 第二次调 LLM 重新分类
  (`line_expense.py:164`)。两套意图 taxonomy 不同(loop 的 5 规则 vs `line_agent.py:25-46` 的
  7 intent × 5 speech_act × 9 chat_kind),同一句话两个大脑可以判出不同意图;成本 ×2;延迟 ×2。
- **旧路地雷仍可达**:模型主动 `defer(reason="record")` 但句子其实不是记账(模型误判)→
  ③ 的 `has_item_context` 反问池(`:125-127` `amount_no_item`)照旧能问出"这笔多少钱"——
  历史事故("老婆不爱我"被问价格)只是被 crash 隔离救了大半,defer 误判这条缝还在。
- **无余额 = 整个新大脑蒸发**:`line_agent_route.py:50-51` balance_ok=False 直接走旧路全套
  (含旧 LLM?不含——`:163` 同样查余额,所以落 ⑤ 确定性兜底)。行为不一致:同一句话,
  余额充足=暖回复,余额不足=模板池,用户视角是"人格分裂"。
- **消息掉缝**:③ 的 pending 补金额(`:118-124` `pop_pending` missing=amount)只有旧路会存;
  新大脑写路缺金额时走**文字追问**(loop 观测 `amount_ungrounded` 后模型问一句),但**不存
  pending**——用户下一轮回"50"重新进前门,靠对话记忆让模型再拼一次。模型拼失败 → 这轮"50"
  可能被 ③ 当 `amount_no_item` 反问,死循环感。

### 3.2 终态架构(大脑=唯一决策者,旧路=纯 fail-safe)

```
gated 用户消息(唯一入口序):
  0. 确定性前置(非"决策",是安全带,保留):
     line_correct_flow.route(改错状态机·会话态续接)     ← 有 pending 态才接管
     confirm/cancel postback(按钮,不走文本)
  1. 大脑(loop.handle_turn)= 唯一意图裁决者
     工具集 = A 档只读 + record_expense + record_multi + undo_entry + edit_entry
              + push_to_erp(confirm 档) + 套账导航
     出口五态不变:reply / card_sent / confirm_sent(新) / crash / defer(仅剩兜底义)
  2. fail-safe 层(只在 crash / 闸关时,绝不并行解读):
     crash + L1 可确定性解析的记账句 → L1 直录(无 LLM,§3.4)
     crash + 其它 → 安全兜底一句
     闸关(agent_enabled=False)→ 旧路逐字节不变(现状即如此)
  3. 旧 LLM 大脑 understand():gated 路径【零调用】;仅闸关用户走。
```

关键差异:**defer_record / defer_edit 从"交旧路重新解读"变成"不存在"**——记账/改错/撤销
都有工具了,模型没有理由 defer;`_defer_result`(`loop.py:422-428`)保留只为兼容闸关滚回。

### 3.3 迁移路径(每步独立可回退,能力只增不减)

| 步 | 做什么 | 闸 | 回退 |
|---|---|---|---|
| T1 | undo_entry + edit_entry 做成工具(§6.1),模型停 defer edit | `agent_write_tools`(已有) | 模型仍可 defer,旧路接住(现状行为) |
| T2 | record_multi 工具化(§6.1),撤掉 `loop.py:339` 的多笔前置 defer | 同上 | 保留前置 defer 代码一个版本,flag 切 |
| T3 | 无余额消息也进大脑(只读工具照跑,写工具隐藏+回执引导充值),消灭"人格分裂" | 新子闸 `agent_no_balance_chat`(默认关) | 关闸 = 现状(无余额走旧路) |
| T4 | crash 分级兜底(§3.4) | 代码常量,不用闸(纯 fail-safe 增强) | revert 单 commit |
| T5 | gated 路径物理绕开 ③④(`line_expense.py:95-178` 提为 `_legacy_route()`,gated 分支只走 correction+agent+failsafe) | 大闸 `agent_enabled` 本身 | 关总闸=旧路完整保留 |

T5 之后 `understand()` 只服务闸关用户;**代码不删**(rollback 资产),Zihao 拍板永久放量后
另立 removal 提案。

### 3.4 crash 分级兜底(修 §1.3 的可用性回退 · Zihao 拍板项)

```
crash 时(大脑故障,非模型裁决):
  if lqe.parse_expense(text).has_amount()
     and lqe.has_item_context(text)
     and not (lqe.is_question(text) or lqe.is_nonassertive(text))
     and not lqe.is_edit_request(text)
     and not parse_multi 命中:
        → L1 确定性直录(与 line_expense.py:128-139 同一函数,used_l2=False)
  else:
        → 安全兜底一句(现状)
```

守住的红线:兜底路**只直录、永不反问**(反问池才是历史地雷);四个否定条件全是现有确定性
函数,零新解析逻辑。风险:大脑挂时"咖啡50"入账走 L1 老词典归类(略糙),但**入账 > 丢账**。
若 Zihao 判"宁可不记也不许 L1 糙记",此步整个跳过,其余设计不受影响。

### 3.5 契约测试(证明"单一决策者 + 零能力回退")

全部进 `tests/unit/test_agent_single_decider.py`(新文件):

1. **每句话有且仅有一个系统处理**:harness(§4)驱动真实 `handle_expense_text`,
   monkeypatch 计数三处:`loop.handle_turn`、`line_agent.understand`、`_do_record`/回复出口。
   断言:任意语料轮次,(a) 恰好一个终端出口发声(say/card 恰一次);(b) gated 用户
   `understand()` 调用数 == 0(T5 后);(c) 每轮 LLM transport 调用 ≤ loop 自身步数
   (`transport.text_to_json` 计数,杜绝双脑)。
2. **能力矩阵 ⊇ 旧路(零能力回退)**:把旧路能力枚举成表——单笔记账/多笔/收入拦截/补金额/
   撤销/改错(字段×值×确认)/查汇总/查明细/闲聊池/产品问答/改错定位失败提示——每项一条
   语料 + 期望终态;新架构下逐条断言"有处理者且行为等价或更好"。旧路等价性已有
   `test_line_expense_agent_gate.py` 守闸关分支,补 gated 分支矩阵。
3. **manifest↔executor↔registry 三方一致**已有(`test_agent_manifest.py`),扩:凡 `confirm=True`
   必 `writes=True`;凡 writes 工具必有 sink 装配测试。

---

## 4. 验证 harness(重中之重 · 先于一切功能建)

### 4.1 形态:一份语料,两个跑法

现状没有可用探测器(§1.2:agent_sim 失效、line_sim 已删)。重建为**语料驱动**,语料是唯一
事实源,离线/在线共用:

```
tests/agent_corpus/corpus.jsonl        ← 永久回归资产(进 git)
scripts/agent_sim.py                   ← 重写:在线模式(prod·真模型·人眼验)
tests/unit/test_agent_corpus.py        ← 离线模式(CI·注入模型层·断言路由终态)
```

语料行 schema:

```json
{
  "id": "emo-th-01",
  "lang": "th",
  "text": "เมียไม่รักผมแล้ว",
  "setup": {"write": true, "balance": true, "history": [], "quoted": null},
  "scripted_steps": [{"kind":"reply","message":"..."}],
  "expected": {"terminal": "reply", "must_not": ["ราคา","เท่าไหร่","฿"], "no_record": true},
  "probe": "情绪句绝不被问价格、绝不入账"
}
```

- **离线(CI 闸)**:`decide` 注入 `scripted_steps`(loop.handle_turn 原生支持注入,
  `loop.py:315` `decide` 参数),跑**真实路由代码**(route_gated → handle_turn → sink/兜底),
  断言 `expected.terminal` + `must_not` + `no_record`(mock `_do_record` 计数)。
  测的是**管道**:给定模型任何一种输出(含故障输出),路由/护栏/兜底行为全对。
- **在线(prod 验收台)**:同一份语料,不注入 decide,真 Vertex 真 DB 真账号跑,打印
  USER/BOT/终态给人眼评。模型判意图对不对(离线测不了的那半)靠它 + 真机。

### 4.2 对抗语料规格(首版 ≥80 条,泰/中/英 × 类目全交叉)

每类给出代表条目与期望路由(terminal 用 `TurnResult.kind` + 入口级出口):

| 类目 | 例句 | 期望 |
|---|---|---|
| 情绪句 | เมียไม่รักผมแล้ว / 我好累 / I'm so tired | reply(陪伴人格);must_not 价格词;no_record |
| 俏皮 5555 | 5555 วันนี้รถติดมาก | reply;不入账;不被当数字 5555 记账 ★ |
| 否定句 | ไม่ต้องบันทึกกาแฟ 50 / 别记这笔咖啡50 | reply(不入账);no_record ★ |
| 假设句 | ถ้าซื้อ 100 จะเหลือเท่าไหร่ / 如果我花100呢 | reply 或查询;no_record |
| 一句多笔 | ค่าไฟ 50 ผัก 40 ข้าว 60 | defer_record → 多笔卡(T2 后:record_multi 工具卡) |
| "711"店号 vs 金额 | 711 น้ำ 20 / 在711买水20 | card_sent 金额=20 vendor=7-11;must_not 金额711 ★ |
| 中文问泰答 | (泰语账号)"本月花了多少" | reply 且**中文**回(`_reply_lang` loop.py:112-116) |
| 无余额 | (balance_ok=False)กาแฟ 50 | 现状:旧路直录;T3 后:大脑只读+引导 |
| 缺金额 | ซื้อกาแฟ / 买了咖啡 | reply 追问金额;no_record;下一轮"50"→ card_sent ★(两轮连测) |
| 改错 | แก้รายการล่าสุดเป็น 80 | 现状 defer_edit;T1 后 edit_entry 工具 → correct 流确认句 |
| 撤销 | ยกเลิกรายการล่าสุด / 撤销刚才那笔 | 现状 defer_edit/旧路;T1 后 undo_entry → 终态卡 |
| 查询零命中 | หาบิล starbucks(无数据) | reply 诚实"没找到";must_not"这笔多少钱" |
| 通知零命中 | มีแจ้งเตือนไหม(0 条) | reply "没有新通知"(观测 count 路 `loop.py:177-178`) |
| 切套账 | สลับไปสยามวัสดุ / 切到不存在的账套 | reply(成功确认 / 列候选让挑) |
| 推送状态(M4 后) | ใบ 7-11 ส่งเข้า ERP หรือยัง | reply 带真实推送状态;失败绝不说成功 |
| 推 ERP(M3 后) | ส่งใบล่าสุดเข้า MR.ERP | confirm_sent(确认卡);未点按钮绝不执行 ★ |
| 模型故障注入 | scripted: 坏 JSON / 空回复 / 不存在的工具 / 复读一屏零 | crash → 安全兜底;must_not 原样输出 ★ |
| 编造参数注入 | scripted: record_expense(amount=999) 但原文无 999 | 追问,不入账(slots+to_draft 双闸) ★ |
| 散文救援 | scripted: 干净人话没包 JSON | reply 原文(`_salvage_prose` loop.py:250-256) |
| 记账+情绪混合 | เหนื่อยมาก กาแฟ 50 | card_sent(BOOKKEEPER 先做事)+ 暖话 |

★ = 历史真事故或钱路红线,进 CI 必跑集。语料只加不删(回归资产);每修一个线上翻车,
先加一条语料复现,再修(test-first)。

### 4.3 harness 的边界诚实

离线测不了"真模型会不会选对工具"——那是提示词/模型质量,靠在线 sim + 真机(人类门)。
但历史翻车(问价格/一屏零/编金额/掉旧路)**全部是管道层问题**,离线全覆盖。CI 只跑离线。

---

## 5. M4 · A 档铺满(逐文件落地设计)

每个工具固定四件套:ToolSpec(manifest)+ executor 方法 + `REGISTRY_AREA` 登记 +
单测/语料。统一约束:走 `get_cursor_rls` 真实身份;回执数字只来自查询结果;
`_observe_payload`(`loop.py:138-187`)与 `fallbacks._VALUE_FB/_FALLBACK`(`fallbacks.py:15-90`)
同步补条目;`agent_i18n._T` + `static/i18n-data.js` 双侧加键(parity 测试守,改 js 必
`node --check`)。

| 工具 | 数据源(复用,零新查询逻辑) | slots | 回执要点 |
|---|---|---|---|
| `push_status` | `db.list_push_logs` / `db.has_recent_successful_push`(与 `routes/erp_push_log_routes.py:219-236` 同源) | keyword(user_text·店名/单号→先 list_history 定位 history_id) | 红线#3:status 原样人话化,failed/rows=0 绝不"成功";复用 `push_log_friendly` 的失败码人话 |
| `rd_lookup` | services/vat 现成 `lookup_vat`(RD 税局·带 rd_cache) | tax_id(user_text·13位) | 查无此号 ≠ 报错,诚实"税局查不到" |
| `ask_knowledge` | knowledge_ask_routes 背后的 service(知识库问答) | question(model_freeform) | 无命中 → 回落大脑自答但声明非官方 |
| `my_plan` | `db.get_billing_status_combined` + `_plan_permissions`(`executor.py:21-30` 同口径) | — | 套餐名/额度/到期 |
| `books_overview` | accounting_books_routes 背后 service | period(user_text) | 只读汇总 |
| `erp_accounts` | erp_express_account_routes 背后 service | — | 已配端点/账套列表(给 push confirm 的 endpoint 反问当数据源) |

顺序:push_status → rd_lookup → ask_knowledge(价值排序),每个独立 commit 独立可回退。
executor.py 现 144 行,+6 工具估 +180 行 → 拆 `executor_readonly.py`(文件头 `executor.py:8`
本就预告此拆法,facade re-export 保契约)。

M4 完成判据见 §7;`agent_registry.json` 结构升级与审计闸 FAIL 化见 §2 末段。

---

## 6. M3 · 写工具闭环(逐文件落地设计)

### 6.1 (a) 记账全家桶收成工具(大脑唯一决策者的前提)

**undo_entry**(撤销):
- manifest:bucket=B,writes=True,confirm=False(撤销本身可再恢复,`line_restore` 在),
  slots:`target`(user_text,可空="最近一笔")。
- executor:不自造逻辑,经注入 sink 调 `line_expense_qa.reply_undo`
  (签名见 `line_expense.py:238-248`,自带"对象不明确→提示 reply 不默认撤最近"的安全行为)。
- 接线:`line_agent_bridge._record_sink` 旁边加 `_undo_sink`;`AgentContext`(`contracts.py:64-78`)
  加 `quoted_message_id` 字段(撤"引用的那张"要用)。

**edit_entry**(改错):
- manifest:slots:`field`(user_text·seller/date/amount/category/payment)、
  `new_value`(user_text 接地——改错的新值必在原话里)、`target`(可空)。
- executor sink → `line_correct.request_correct`(`line_expense.py:253-266` 旧路同款入口),
  把 loop 模型抽的字段拼成旧 `u` dict 喂进去 → **复用 correct 流全套**:风险三档、
  `_apply_or_confirm`(`line_correct.py:206`)、是/否确认(`try_confirm:380` + `_YES:48`)、
  active 续接。**第二次 LLM 调用就此消失**(现状 defer_edit → `understand()` 重新抽一遍)。
- 改错会话态(correct:*/correctval:* pending)期间,`line_correct_flow.route` 仍在 Agent 前
  接管(`line_expense.py:68`)——这不是"第二决策者",是确定性状态机续接,保留。

**record_multi**(多笔):
- 现状 `loop.py:336-340` 确定性预判多笔就 defer。T2 改为工具:slots 无(执行器内
  `parse_multi` 重算,不信模型拆分),sink → `line_expense_multi.do_record_multi`
  (`line_expense.py:109-113` 旧路同款)。模型只负责"这是多笔记账"的意图,拆分/金额全确定性。
- 保险:预判 defer 代码保留一个版本,新工具灰度稳了再删。

三者全在 `agent_write_tools` 既有闸后(关=defer 回旧路,现状不变);金额/新值全走 user_text
接地(`slots.py:39-42`)+ `to_draft` 钱闸双保险。落点:executor 拆出 `executor_write.py`,
sink 装配集中 `line_agent_bridge.py`(现 100 行,+3 sink 约 +60 行,富余)。

### 6.2 (b) 推 ERP confirm-first 状态机(唯一不可逆写 · 全套新建)

**总原则**:loop 首次消费 `ToolSpec.confirm`;确认走**现成卡片按钮 + 一次性 nonce**
(修订②定案),不发明文字握手;真推送**只调用**现有推送编排,`services/erp/*` 一行不碰。

**新 flag**:`platform_settings` 键 `agent_push_erp`(默认无记录=关,fail-closed 与
`feature_flags.py:22-30` 同款消费函数 `agent_push_enabled_for`)。关 = push_to_erp 对模型
不可见(进 `_visible_tools` 过滤,`loop.py:190-193` 扩一个维度)= 现状逐字节不变。

**状态机**(镜像 `line_card_actions.handle_postback` 的 nonce 范式,`line_card_actions.py:211-269`):

```
① 用户:"ส่งใบ 7-11 เข้า ERP"
   loop:模型选 push_to_erp(slots: doc_keyword→user_text 接地)
② loop 新 confirm 档(spec.confirm=True):
   【不执行】→ confirm_sink(ctx, spec, grounded):
     a. 定位:list_history(keyword) 唯一命中 → history_id;零/多命中 → 反问(agent.ask.which_doc)
     b. 选端点:db.get_default_erp_endpoint;无 → agent.failure.no_endpoint;多端点且用户没点名
        → 反问 agent.ask.endpoint(候选来自真实配置)
     c. 预检幂等:db.has_recent_successful_push 命中 → 直接回 agent.ok.push_dup,不出确认卡
     d. line_action_nonce.mint(action_ref=json{kind:"agent_push",history_id,endpoint_id},
        ttl 短设 15min,非默认 72h——推送确认不该隔夜有效)
     e. 出确认卡:单据摘要(单号/卖家/金额=history 真实字段)+ [ยืนยันส่ง]/[ยกเลิก] 按钮
        (postback 新动作码 agent_push_confirm/agent_push_cancel,line_postback.py 加两常量)
   loop 返 TurnResult("card_sent")(复用既有 kind,入口已会处理,line_agent_route.py:69-71)
③ 用户点 [ยืนยันส่ง]:
   line_card_actions.handle_postback 分发新动作 → services/agent/push_confirm.py(新):
     a. nonce.consume 原子消费(双击/重放 → used → 回"已在处理/已推送"状态卡,不二次推)
     b. 权限:复用 routes/erp_routes_access._check_push_access 同款判定
     c. 即时回执 "กำลังส่ง..."(推送含 Playwright/requests 同步阻塞,
        webhook 是 async —— 镜像 erp_push_log_routes.py:112-114 的 to_thread,后台执行)
     d. 执行 = 逐行镜像 routes/erp_push_log_routes.py:34-162 的编排(唯一权威范式):
        get_ocr_history_detail → get_erp_endpoint → has_recent_successful_push 二次防重
        → erp_push.push_to_endpoint(只调用·不改)→ classify_push_status → insert_push_log
        (trigger="line_agent",审计)→ update_endpoint_stats → update_history_push_status
        → failed 且非用户数据错 → schedule_log_retry
     e. 结果 push 消息:成功 agent.ok.push(bill_no 来自响应);skipped_dup agent.ok.push_dup;
        失败 → 复用 push_log_friendly 失败码人话(红线#3:绝不把 failed 说成成功)
④ 用户点 [ยกเลิก] / nonce 过期:agent.confirm.cancelled / card_action_expired(均现成键)
```

**幂等三层**:nonce 一次性(层1·防双击)→ has_recent_successful_push(层2·防跨会话重推,
与网页手动推同口径)→ `erp_push_logs` 唯一状态源(层3·红线#2,不建第二套状态)。

**文件落点**(全部新文件或轻改,守 <500):
- `services/agent/confirm.py`(新):loop 的 confirm 档逻辑 + confirm_sink 契约
  (loop.py 现 428 行,confirm 分支控制在 ~25 行,溢出即把写档整段迁 confirm.py)。
- `services/agent/push_confirm.py`(新):③ 全部编排 + 每函数 ≥1 测试。
- `line_postback.py`(+2 动作码)、`line_card_actions.handle_postback`(+1 分发分支,~6 行)。
- `manifest.py`:push_to_erp ToolSpec(bucket=B,confirm=True,writes=True,
  REGISTRY_AREA→erp_push_log_routes)。
- **不碰**:`services/erp/*`(MR.ERP 窗口地盘)、`routes/erp_push_log_routes.py`(只镜像不改)。

**待人评审的接线口**(本文只设计,实现前单独过):push_to_endpoint 对 MR.ERP 直写新链路的
兼容性(另窗口在改 `services/erp/push_store.py`,adapter 语义可能在变)——实现排期上
push_confirm 的 d 步**等 MR.ERP 分支合 master 后再接**,confirm 状态机(a~c、e)可先建先测
(d 步暂 mock,flag 反正默认关)。

### 6.3 M3 后的 loop 决策全景(终态)

```
模型输出 → _parse_step
  reply → 出口护栏(_sane_reply)→ 发
  tool(A 档) → slots 接地 → 执行 → 观测 → 成文
  tool(writes=True, confirm=False:record/undo/edit/multi)→ 接地 → sink 直录/直办 → 卡
  tool(writes=True, confirm=True:push_to_erp)→ 接地 → confirm_sink → 确认卡(不执行)
  defer → 仅闸关兜底义
  crash → 分级兜底(§3.4)
```

---

## 7. 闭环验收定义(达标才算完,不许"基本完成")

**M4 闭环 =**
1. `agent_registry.json` 每个 A 档功能区状态 ∈ {tool:*, exempt:*},审计脚本第二道核对绿;
2. 审计闸从 warning 翻 FAIL 进 CI;
3. 每个新工具:manifest+executor+observe+fallback+i18n 四语齐 + ≥1 单测 + ≥2 条语料
   (正常 + 零命中/失败各一)全绿;
4. 在线 sim 全语料人眼过一轮,prod 真账号。

**M3 闭环 =**
1. 记账(录/多笔/撤/改)全是工具,gated 路径 `understand()` 调用数=0(契约测试 §3.5-1 绿);
2. 推 ERP:确认→执行→幂等(双击/重发/跨会话三层)→结果卡→失败诚实,全链单测 + 语料
   (确认卡出现≠执行,未点按钮 DB 无推送日志——这条是钱路核心断言);
3. 全部在闸后:`agent_push_erp` 默认关;关任意闸 = 对应能力逐字节回旧行为(gate 测试);
4. 语料回归全绿 + 真机验收(人类门)后才谈开闸。

---

## 8. 各道闸与人类门

**自动(机器守,CI 红=停)**
- flag 默认关(fail-closed,`store.py:91-107` 范式)· 关=现状 byte-identical(gate 契约测试)
- 语料回归 `test_agent_corpus.py`(离线,进全量 unittest)
- 单一决策者/零回退契约(§3.5)· manifest 三方一致(`test_agent_manifest.py` 扩)
- i18n key parity(`test_agent_i18n.py` 现成)+ `node --check` + `check_i18n --strict`
- 能力防漏审计(`agent_capability_audit.py` FAIL 化)
- 钱闸:金额接地双闸单测(slots + to_draft)· 推送幂等三层单测
- 常规六道闸 + 文件 <500(loop 428/line_expense 456/line_correct 491/line_quick_entry 499
  都逼近上限,**新逻辑一律新文件**)

**人类门(永不自动)**
- 推 ERP 接真钱路:d 步接真 `push_to_endpoint` + prod 开 `agent_push_erp`,均先报方案等批
- 真机 E2E:记账写工具真机验证(需绑 LINE 的号,skin 号未绑)、推 ERP 真机全流程
- 任何 rollout 放量/回收(超管后台)
- MR.ERP 分支合并时序(别撞另一窗口)
- §3.4 crash 分级兜底要不要 L1 糙记(产品取舍)

---

## 9. 分阶段施工顺序(每阶段自带测试与验收,独立分支,依次报批)

**Phase 1 · harness(先建探测器,零产品行为改动)**
1. corpus.jsonl 首版 ≥80 条(§4.2 全类目)
2. `test_agent_corpus.py` 离线跑真实路由(现状预期,翻车即现状 bug 清单——**本阶段的副产品
   就是一份"当前生产对话质量体检报告"**,直接回应"对话质量是当前生产问题")
3. 重写 `scripts/agent_sim.py`(修 §1.2-1 的 stale API,在线模式)
4. 契约测试骨架(单一决策者计数器,先按现状断言,T 步逐步收紧)
验收:CI 新增两测试文件全绿;体检报告交 Zihao。

**Phase 2 · M4 只读铺满(低风险,additive)**
push_status → rd_lookup → ask_knowledge → my_plan/books/erp_accounts;registry 结构升级 +
审计 FAIL 化收尾。验收:§7 M4 判据 1~3(判据 4 真机是人类门)。

**Phase 3 · M3 写闭环**
3a. undo/edit/multi 工具化(T1/T2)+ crash 分级兜底(T4,若批)+ 无余额进大脑(T3,若批)
3b. push confirm-first 状态机(a~c,e 步 + mock d 步,flag 默认关)
3c. 【人类门】MR.ERP 稳定后接真 d 步 → 真机 E2E → 报批开闸灰度
3d. T5 gated 路径物理绕开旧 LLM(单一决策者收官)
验收:§7 M3 判据;每个 T 步独立 commit 独立可 revert。

---

## 10. 风险与回退(每项秒级)

| 改动 | 风险 | 秒级回退 |
|---|---|---|
| M4 各只读工具 | 回执数字口径错 | 工具从 manifest 摘除一行(模型即看不见);或关不掉时 revert commit |
| undo/edit/multi 工具 | 误路(改错被当记账等) | `store.set_setting("agent_write_tools",{"rollout":"allowlist"},True)` 收灰度;defer 兜底恒在 |
| 推 ERP 全套 | 误推(钱·不可逆) | flag `agent_push_erp` 默认关;开后关闸=工具消失;nonce 15min 自灭;推错走既有 ERP 侧删单流程(人工) |
| crash 分级兜底 | L1 糙记 | revert 单 commit(无 flag,纯代码路径) |
| 无余额进大脑 | 算力成本 | 关 `agent_no_balance_chat` |
| T5 绕开旧路 | 未知边角掉能力 | 关总闸 `agent_enabled` 整层蒸发回旧路;语料矩阵先行兜住已知面 |
| 共享工作树 | 卷入 MR.ERP 窗口未提交文件 | 铁律:commit 必带显式 pathspec;不碰 services/erp/*;push 前 `git log` 自查 |
| 大脑供应商抖动 | 全量用户对话降级 | 现状=安全兜底;§3.4 后=记账保命;监控点:route_gated crash 率(现有 logger.warning 可聚合) |

---

## 附 · 本次通读的关键文件清单(接手窗口按图索骥)

新大脑:`services/agent/{loop,executor,manifest,contracts,slots,brain,fallbacks,copy_map,agent_i18n}.py`
接线:`services/line_binding/{line_agent_route,line_agent_bridge,line_expense,line_record_card,line_workspace,line_card_actions,line_action_nonce,line_postback}.py`
旧路:`services/expense/{line_agent,line_correct,line_correct_flow,line_quick_entry,line_classify,line_l2,conversation}.py`
入口:`routes/line_webhook_routes.py` · 推送范式:`routes/erp_push_log_routes.py:34-162`
闸:`core/feature_flags.py` + `services/platform_settings/store.py`
测试:`tests/unit/test_agent_{loop,executor,manifest,slots,i18n,brain_parse,capability_audit}.py`
+ `test_line_agent_route.py` + `test_line_expense_agent_gate.py`
