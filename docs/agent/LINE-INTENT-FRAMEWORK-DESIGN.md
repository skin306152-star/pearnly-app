# LINE 意图框架(LI)· 图/话统一进大脑 · 总设计

> Zihao 2026-07-02 拍板方向:"我要的是理解用户发这张图的目的、说一句话的目的,对着 Pearnly
> 的功能能力,带能力反问,用户确定,实现用户意图,遇阻告知并引导——一套全能框架。"
> 本框架只覆盖 **LINE 对话**;网页对话 Agent(MASTER-PLAN 旧 M5)继续搁置不动。
> 施工模式照 M3/M4:独立分支 · 闸默认关 · 语料先行 · 每块 CI 绿 · 真机验完再放量。

---

## 1. 现状事实底座(读真代码核实 · 2026-07-02)

**图片路(`services/ocr/line_image_ocr.py`)是写死的单管线**,大脑全程不参与:

```
发图 → 下载 → 支持格式/余额闸 → 去重快路(early_dup / 指纹缓存)
    → OCR pipeline → not_invoice 拦截
    → 记账闸开(line_expense_gate_open)且有套账:
         ingest_line_image 逐页入采购账(高置信正式入账/其余草稿)→ 扣费 → 数据卡
         ★不写 ocr_history(计费 history_id=None)
    → 否则:insert_ocr_history(source='line_bot')→ 扣费 → 异常 hook
```

**由此推出的三个硬事实(设计必须解决):**

1. **记账租户的图片今天无法推 ERP**:推送机械(定位/预检/幂等/日志)全挂在
   `ocr_history` 上,而记账路的图进的是 `purchase_docs`,两边不通。
2. **LINE 的图和话是两条独立事件**(LINE 无图片配文),"发图带话"必然是先后两条消息
   → 意图必须能跨消息拼装(话先图后 / 图先话后 / 反问后补答)。
3. **对话记忆已有雏形**:`line_chat_memory.note` 已记图片轮结果供后续文本追问;
   M3/M4 后大脑已具备 undo/edit/push 工具与 confirm-first 机械——**框架大部分是组装,
   不是新造**。

---

## 2. 意图模型(框架的心脏)

一张图/一句话背后的意图 = **目标组合 + 参数**,全部开放不写死:

```
intent = {
  goals:   {record? push? archive_only? nothing?}   # 可组合:都要/都不要/只其一
  push_to: <端点名|null>                              # 推哪个 ERP(MR.ERP/Express/…)
  book_to: <套账|null>                                # 记进哪个套账
  target:  <这张图|某张历史单>                          # 作用对象
}
```

**意图来源的优先级(高→低):**
1. 用户明说(伴随文字 / 反问后的回答)——唯一可信源
2. 高置信默认(普通单据 + 用户没说话 → 维持今天的自动记账,**默认路逐字节不变**)
3. 拿不准 → **带能力反问**,绝不猜写/猜推

**钱路红线(继承 M3/M4,一条不放松):** 推 ERP 永远 confirm-first 确认卡;金额永远来自
OCR/工具,模型不产数;意图不明绝不执行不可逆动作;大脑故障 fail-safe 回现状管线。

---

## 3. 逐块设计

### LI-2 · 图片进大脑(闸 `agent_image_intent` 默认关)

**改动点唯一**:`line_image_ocr.py` 在「OCR 完成、入账之前」加一个分流问询点:

```
OCR 完成 → not_invoice 照旧拦
→ 闸关 → 走现状(byte-identical,gate 契约测试锁)
→ 闸开:
   a. 有待决意图(pending intent·见 LI-3)→ 按意图直接执行对应终端(不再默认记账)
   b. 无待决意图 + 单据普通清晰 → 默认路:照今天自动记账(多数用户无感)
   c. 无待决意图 + 歧义信号(身份证/多种可能/低置信)→ 大脑收 OCR 摘要观察判目的,
      拿不准出反问(LI-3)
```

- 大脑**永远只读 OCR 出的文字摘要**(卖方/金额/单据类型/置信),不二读图片 → 零新增
  模型图像成本;判意图是一次 flash 文字调用(≈฿0.03,我们吸收,不向用户计费)。
- **计费零改动**(Zihao 2026-07-02 拍板):OCR 跑了就按现行扣,含"都不要";not_invoice
  维持现行口径不另立规矩。

**四个执行终端**(全部复用现有机械,不新造写路径):

| 终端 | 实现 | 备注 |
|---|---|---|
| record(记账) | 现有 `ingest_line_image` | 就是今天的默认路 |
| push(推 ERP) | **新增:写一行 `ocr_history`(source='line_bot')作为推送载体** → 复用 M3/M4 已真机验证的 push 备料+确认卡+幂等全套 | 解 §1 硬事实 1;`services/erp` 只调用不修改 |
| both(都要) | record + push 载体各写各的 | 查重靠 file_hash + duplicate 预检(现成) |
| archive_only(只存不记) | `insert_ocr_history` 即今天"记账闸关"的那条路 | 用户拿到识别结果卡 |
| nothing(都不要) | 只回识别摘要一句话,不落任何账 | 费已扣(拍板口径) |

### LI-3 · 带能力反问 + 多轮意图记忆

**待决意图表 `line_pending_intents`**(窄表,一用户一条活动意图):

```
line_user_id · tenant_id · workspace_client_id · intent jsonb · expires_at(默认 15min)
```
- 建表走迁移;⚠️ Supabase 会自动开 RLS——按 [[supabase-auto-enables-rls-new-tables]]
  当步决定 enroll 或显式 DISABLE,绝不留 deny-all 孤儿。
- 生命周期:话先图后(存意图等图)/ 反问后等答案 / 图先话后(话直接作用于刚入账那张,
  走已有 undo/edit/push 工具,不需要 pending)。新的无关消息 → 意图过期作废(不粘人)。

**反问的选项永远来自用户真实资产**(这是"带能力反问"的定义):
- 推哪个 → `list_erp_endpoints`(enabled 的真实端点名)
- 记哪个套账 → `list_workspaces`(真实套账)
- 只有一个可选时不问,直接带默认进确认卡(确认卡本身就是最后一道确认)
- 载体:LINE quick-reply 按钮 + postback(复用 line_postback 分发范式);用户手打文字回答
  同样能解析(不强迫点按钮)。四语文案进 agent_i18n(key parity 闸现成)。

### LI-4 · 遇阻引导目录

现状失败是诚实的但只"告知";升级为"告知 + 下一步":
- 复用 `push_log_friendly` / `mrerp_business_friendly` 失败码目录,**扩一个 guide 字段**
  (四语):无端点 → "去 网页-集成-连接 ERP 添加";没绑套账 → 绑法;余额不够 → 充值口;
  能力不存在 → "这个目前要在网页 xx 页做"。
- 大脑成文失败的兜底(fallbacks.py)同样带 guide。原则:**用户永远知道下一步去哪,
  绝不留死胡同**。

### LI-1 · 语料先行(施工第一块,零产品行为改动)

corpus.jsonl 扩意图场景(离线注入 OCR 结果 + scripted 大脑,跑真实分流代码进 CI):
话先图后(只推/只记/都要/都不要/指定端点/指定套账)· 图先话后(撤销改推/换套账)·
反问-回答闭环 · 反问后答非所问/反悔 · 意图过期 · 歧义单据(身份证→引导 DMS 是网页能力)·
大脑故障回默认路 · 闸关 byte-identical。**新增两条压测不变量:未确认不推(继承)+
闸关时图片路输出与现状逐字节一致。**

### LI-5 · 验收判据(达标才算完)

1. 全部在闸后:`agent_image_intent` 默认关;关 = 图片路逐字节现状(gate 契约测试);
2. 语料回归全绿进 CI;混沌压测(含图片事件注入)零违例;
3. 真机(绑定号):①图+"只推不记"→ 无新账 + 确认卡 → 点确认 → MR.ERP 真进单
   ②图+"记进 X 套账" ③裸图 → 默认记账与今天无差 ④反问流全程 ⑤"都不要"→ 零落账;
   双边截图证据夹;
4. 每块独立 commit 独立可 revert;每 push 盯 CI 到绿。

---

## 4. 风险与秒级回退

| 改动 | 风险 | 回退 |
|---|---|---|
| 图片分流问询点 | 误改默认路伤主流量 | 闸默认关;开后关闸 = byte-identical(契约测试锁);revert 单 commit |
| push 载体写 ocr_history | 与记账路双写造重复感 | 载体行仅意图含 push 时写;file_hash+dup 预检拦;可单独关 push 终端(agent_push_erp 现成闸) |
| pending intent 表 | RLS 孤儿 / 意图串人 | 建表当步定 RLS 终态;按 line_user_id+tenant 双键取;TTL 自灭 |
| 反问打扰用户 | 高置信也被问 | 默认路优先原则:没话+不歧义=永不问;反问频率进语料压测 |

## 5. 人类门(永不自动)

真机验收(需绑定号配合)· 放量 all(Zihao 拍板)· 涉 DMS 推送终端(本期不做,
只做"引导去网页",DMS 工具化是下一个能力单独报)。

## 6. 施工顺序

LI-1 语料 → LI-2 图片进大脑+四终端 → LI-3 反问+多轮 → LI-4 引导目录 → LI-5 压测+真机+报批。
每块一个或多个 commit,块间可交付可回退,不跨块夹带。
