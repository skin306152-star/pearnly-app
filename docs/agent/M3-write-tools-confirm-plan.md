# M3 · 写工具确认握手 · 实现规格(复用现有零件 · 不发明)

> 原则(Zihao 2026-07-01):**按 code 背后逻辑做,不自创,拿市场成熟方案迭代适配**。

> ## ⚠️ 修订②(2026-07-01·commit `cbecfde9`):统一逻辑——记账高置信直录,不先确认
>
> Zihao 再定义:**要不要回问 = 看「确定性 × 可逆性」,不是「读 vs 写」一刀切**。修订①把记账做成
> 「先出确认按钮」是过度设计(等于多一步)。最终形态:
> - **记账 = 高置信直录**(`used_l2=False`·复用 `confidence.grade` 直接过账·可撤销)→ 不回问;
>   缺金额/方向不明 = 不确定 → 大脑**文字追问**(不入账)。`ToolSpec` 拆两义:`confirm`(执行前先复述·
>   留给推 ERP 等**不可逆**动作)与 `writes`(写工具·写关时隐藏 + 走 `record_sink`)。
> - **人话 + 卡叠加**(非二选一):模型调 `record_expense` 随带一句暖话 `step.say` → 经 `ack_text`
>   显示在数据卡上方(替代 `ack_message` 死板模板);数字全在卡(零编造),大脑只写卡外那句。
> - **双人格 `_SYSTEM`**:账务侧(碰钱=暖而利落·确定就做)+ 陪伴侧(闲聊看氛围·难过先安慰·逗趣俏皮)。
> - 卡渲染两纯函数抽到 `services/line_binding/line_record_card.py`(line_expense 510→455)。
>   `RATCHET-EXEMPT: services/line_binding/line_record_card.py`(新文件·从 line_expense 抽出·非新债)。
> - **推 ERP(以后)= 唯一走「先复述确认」的写工具**(`confirm=True`·不可逆·推错要去 ERP 删)。
>
> 下面修订①与 §2.1~§2.3 的「按钮/文字确认」对记账不再适用;确认机制留给推 ERP。§2.4 安全仍全立。

> ## ⚠️ 修订①(2026-07-01·commit `500ada57`):确认改走「现有富卡 + 确认按钮」,弃文字握手
>
> Zihao 指出确认应复用那张精致数据卡,不是纯文字。复查代码证实:现有 `line_card_actions`
> 的「草稿卡 + [ยืนยัน]/[ยกเลิก] 按钮 + postback(`ACTION_CONFIRM`)+ nonce 令牌」**本就是**
> "确认-再-落库 + 幂等"的成熟机制(即下表 Stripe/乐观-Undo 那两行的真等价物)。下文 §2.1~§2.3 的
> 「文字复述 + 文字是/否 + `line_pending_entry` 待办」是**重复造轮子,已废弃删除**。
>
> **现行设计**:Agent 提议 `record_expense` → 接地建草稿 → `record_sink` 走现有
> `line_expense._do_record`(`used_l2=True` → 置信判 `needs_review` → 出草稿卡 + 确认按钮);
> 确认由**卡片按钮 + 现成 postback + nonce** 完成(非文字)。金额没接地 → 大脑用文字追问。
> 卡即回复,`loop` 返 `RECORD_CARD_SENT` 哨兵让入口消费本轮不再发文字。写子闸
> `AGENT_WRITE_TOOLS` 仍默认关(关=记账 defer 回旧乐观路,旧路 `_do_record` 一样出这张卡)。
> 已删:`line_agent_confirm` 模块+测试、`loop._confirm_observation`、`copy_map.record_confirm/
> cancelled`、`bridge._persist_record_pending/AGENTREC`。§2.4 安全约束仍全部成立。
>
> 下面 §0 的成熟方案对照仍有效(只是我们选了"卡+按钮 postback"这条,而非"文字确认"那条)。

## 0. 市场成熟形状 ↔ 我们已有的等价物

| 成熟方案 | 形状 | 我们 code 里的等价物(已 prod) |
|---|---|---|
| Anthropic 工具审批 / OpenAI function-call 确认 | 模型提议动作 → 人点头 → 才执行 | `line_correct`:复述 → 是/否 → 执行 |
| Stripe PaymentIntent `requires_confirmation→succeeded` + 幂等 key | 挂起态 + 幂等令牌 | `line_pending_entry`(挂起) + `line_booker` 铸 nonce token(幂等) |
| AWS Lex `ConfirmationPrompt` | 会话槽位确认态 | `conversation.save/peek/pop_pending` + `missing` 前缀状态机 |
| 乐观 UI + Undo(Gmail 撤回) | 先执行 + 可撤 | 现有记账:入账 → 卡带撤销 |

**结论**:确认握手不需要新造,`line_correct` 就是模板;存储 `line_pending_entry` 就是现成的"记住半截待办"。

## 1. 现状缺口(为什么 loop 现在做不了写)

- `services/agent/loop.py` 只支持 `tool / reply / defer` 三态,**`ToolSpec.confirm` 字段定义了但没消费**。
- 记账意图现在从 loop **defer 回旧路**,旧路用"乐观入账+撤销"(`_do_record`→`line_booker.book_and_mint`)。
- 写工具(B 档)要的是"先复述+确认再执行",这一档 loop 里不存在 = 唯一真缺口。

## 2. 设计(记账做第一个 · 不碰 MR.ERP)

### 2.1 数据流(镜像 line_correct)
```
用户: "记一笔 咖啡 50"
  → loop 判 record 意图 → 提议 tool=record_expense(confirm=True), args={amount,vendor,note...}
  → slots 接地(金额必过 amount_grounded,编造一律拦)
  → 因 confirm=True:【不执行】,改为:
       save_pending(draft=ExpenseDraft(args), missing="agentrec:<ws>")   ← 复用 line_pending_entry
       返回复述句:"记一笔:咖啡 ฿50 · 确认吗?(回复 ใช่/是 入账,ไม่/否 取消)"
用户下一条: "是"
  → 入口 line_expense 在 agent 前【先查待办】(镜像 line_correct_flow.route 的 peek_pending)
  → 命中 agentrec: 前缀 + is_confirm(text) → pop_pending → _do_record(stored draft) → 入账 + 结果卡
  → is_cancel(text)/新话题 → clear_pending
```

### 2.2 复用清单(几乎不新写)
- **存储**:`conversation.save_pending / peek_pending / pop_pending / clear_pending`(`line_pending_entry` 表)——**零改动**。记账待确认参数本身就是 `ExpenseDraft`,`draft` 列直接装。
- **状态编码**:`missing` 加新前缀 `agentrec:`(与 `line_correct` 的 `_PREFIX/_VAL_PREFIX/...` 并列)。
- **是/否判定**:`line_classify.is_confirm` / `is_cancel_intent`(改错流已在用,同一把)。
- **金额接地**:`services/expense/line_l2.to_draft`(已强制 amount_grounded,LLM 不编金额)或 `slots.py`。
- **执行 + 幂等 + 计费 + 结果卡**:`line_expense._do_record` → `line_booker.book_and_mint`(铸 nonce·幂等·dup 警告·置信过账)+ `_charge_line_l2`。**全现成,一行不改。**

### 2.3 只新增这几处(最小面)
1. `services/agent/manifest.py`:加 `record_expense` ToolSpec(bucket="B", confirm=True, slots=amount/vendor/note/date...)。
2. `services/agent/loop.py`:`step.kind=="tool"` 且 `spec.confirm` 且已接地 → 走 `_request_confirm(ctx, tool, grounded)`:持久化待办 + 返回复述句(不执行)。保持 loop 纯:持久化经注入的 confirm sink,便于测试。
3. `services/line_binding/line_expense.py`:在 `try_agent_turn` **之前**加一段"先查 agent 待办"(镜像 `line_correct_flow.route` 位置),命中 `agentrec:` → 是/否/新话题 三分支。
4. `services/agent/executor.py`:`record_expense` B-handler(确认后执行路,内部调 `_do_record` 同款编排)。
5. 文案:复述句进 `copy_map` + `agent_i18n`↔`i18n-data.js`(四语·key parity 守)。
6. 测试:loop confirm 档单测 + 入口待办分支契约测试 + 记账端到端(是→入账 / 否→清 / 超时→清)。

### 2.4 安全(全守铁律)
- **灰度开关**:新增子闸 `AGENT_WRITE_TOOLS`(默认关)。关 = 记账仍 defer 走旧乐观路,**逐字节现状**;开才启用 confirm 工具。建好+push+真机测都不改现有行为,验稳才开灯。
- **additive-only**:任何异常/未接地/开关关 → defer 回旧路,记账照常完成,能力只增不减。
- **金额绝不编**:必过 amount_grounded,编造转反问,不流到入账。
- **幂等**:`book_and_mint` 铸 nonce;重复"是"→ pop 已清待办,第二次无待办不二次入账。
- **计费不绕**:执行走 `_charge_line_l2`(与旧路同口径)。
- **TTL**:`line_pending_entry` 15 分钟过期自动失效(现成)。

## 3. 记账走 confirm-first 还是保持乐观+撤销?(留真机定)
记账现状是"乐观入账+撤销"(快)。本规格让 **agent 路**的记账走 confirm-first(复述→是→入账),证通握手机制。是否给记账每次加确认步(略慢)vs 保持乐观,**开关开后真机体验再定**——机制先建好,UX 参数后调。可逆高频操作(记账)可回落乐观;不可逆敏感操作(推 ERP·M3 下一个)必须 confirm-first。

## 4. 顺序
1. 本规格 → Zihao 确认方向。
2. 建 manifest+loop confirm 档+store 复用+executor handler,子闸默认关,自带测试。
3. 真机 LINE 端到端(skin)验:是→入账、否→清、超时→清、金额不接地→反问。
4. 稳 → 开 `AGENT_WRITE_TOOLS` 灰度 skin → 放量。
5. 复制到推 ERP(等 MR.ERP 窗口稳)/ 改错(line_correct 接进工具)。
