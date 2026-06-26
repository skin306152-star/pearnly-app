# 00 · LINE 平台:方向 + 分层路由框架(做 LINE 活先读这一页)

> 这是 LINE 平台的方向入口。任何窗口动 LINE 相关代码,先读这页;做采购进项车道时,再读
> `docs/line-platform/02-procurement-canon.md` 作为产品正本。
> 设计来源:2026-06-16 Zihao 拍板「LINE = 统一对话前端」+ 逆向竞品 Paypers LINE 真机 + 「不可破产品边界」。
> 与本页对应的记忆:`line-platform-direction` / `line-accounting-honest-status-boundary` / `paypers-line-reverse-engineering`。

---

## 1. 定位

LINE = Pearnly 所有模块的**统一对话前端 / 遥控器 + 通知中心**,挂在已建好的后端工具层之上(OCR / DMS / ERP 推送 / 导出 / 做账 / 报税 / 对账)。**网页与 LINE 是同一套后端能力的两个前端**,不为 LINE 另起一套业务逻辑。

**目标边界**:覆盖约 80% 的日常动作(单发记账 / 查询 / 审批 / 触发 / 通知),不追求 100% 替代电脑。**密集核对、多步配置、报表钻取留在网页**——LINE 负责触发,用 LIFF / 深链跳过去。硬把密集表格塞进聊天是坑。

---

## 2. 不可破产品边界(每条 LINE 施工都受它约束)

详见记忆 `line-accounting-honest-status-boundary`,这里是必须刻进每次改动的三条:

**三态文案不许越级:**
- **已入账** = 复式分录真写入账簿(`status=posted`)。
- **已计入申报草稿** = 已进本期 ภ.พ.30(VAT)/ ภ.ง.ด.(代扣税)待复核。
- **已申报** = 必须真通过授权 e-Filing 提交、并取得税局回执才能这么说。**绝不在聊天里假装报税成功。**

**LLM 与确定性引擎分工(架构铁律):**
- LLM 只负责:听懂经营语言、字段抽取、多项拆分、上下文指代、把"本月花多少"转查询意图、解释为何要补料。
- LLM 绝不负责:借贷金额计算、税额勾稽、判税期是否开放、判可否抵扣、改锁定期间、宣称已提交、编造税票字段。**这些一律确定性代码算/校验。金额与过账永不信 LLM。**

**风险分层(别一刀切"识别后弹确认"):** 高置信低风险→自动入账可撤销;中置信→建草稿只问一个关键问题;低置信高税务风险→不进税表要求复核;无法识别→存证据不建分录;申报动作→先草稿+规则校验+授权确认,真提交并存回执才显"已提交"。

---

## 3. 分层路由框架(防一个大脑塞 50 工具)

| 层 | 职责 | 当前实现 |
|---|---|---|
| **L0** Rich Menu | 显式分流,用户主动选车道 | LINE OA 控制台配置 |
| **L1** 模态路由 | 按消息类型(图 / 文 / 文件)规则分发,零 LLM | `routes/line_webhook_routes.py::_handle_line_event` |
| **L2** 域内小模型 | 仅在本车道做 3–5 个意图分类 + 槽位抽取 | `services/expense/line_agent.py::understand`(一次 Gemini) |
| **L3** 会话状态 + postback | `conversation.pending` 多轮续接;卡内按钮动作不走路由 | `services/expense/conversation.py` / `services/line_binding/line_card_actions.py` |
| **L4** 兜底深链 | 密集操作跳 LIFF / 网页 | LIFF webview(`liff.state` 解包 + 套账门自动选,见记忆 `line-liff-edit-deeplink-complete`) |

**车道契约**:每条车道实现 `can_handle / classify / dispatch`。**加一条车道 = 路由表注册一行 + 新建一个 `services/line/lanes/<域>/` 文件夹,不动其它车道**(防把旧车道搬来搬去)。目标结构随车道逐步成形,不一次性空搭、不 big-bang 搬存量。

> 当前**只做透「记账车道」**一条,作为框架的参考实现。别同时铺多条车道。下一条车道首选「身份证 → DMS 客户」(后端 recognize / push 现成)。

---

## 4. 记账车道:当前实现地图(已对真代码 2026-06-16)

### 入口
- `routes/line_webhook_routes.py` — webhook 入口:签名校验 → 事件分发(follow / unfollow / postback / text / image|file)。6 位数字 = 绑定码消费。

### 文字路 — `services/line_binding/line_expense.py::handle_expense_text`
编排顺序(顺序本身是设计,别乱改):
1. 对话记忆(取历史 + 记本条,`line_chat_memory`,PO-15)
2. 闲聊(零成本 L1,`services/expense/replies.py`,治复读)
3. gate + 套账检查(`intake.line_expense_gate_open` / `default_workspace_id`)
4. **待确认更正**(`line_correct.try_confirm`,PO-13;优先于记账/大脑/兜底)
5. 收入识别(`detect_income`,明确收款/卖出不误记为支出)
6. 多项拆分(`parse_multi` → `line_expense_multi.do_record_multi`)
7. **L1 快路**:有金额 + 非问句 + 无其他 L1 意图 → 零 LLM 直接记
8. **大脑**(`line_agent.understand` 一次 Gemini)→ `_dispatch_agent` 按 intent 分发
9. 兜底(无 LLM):查账 / 求助 / 问答 / 礼貌带回

### 图片 / 文件路 — `services/ocr/line_image_ocr.py::process_line_image_serial`
per-user FIFO 串行(多图排队不乱序)→ OCR pipeline(L1 Google Vision → L2 Flash-Lite 从文本抽 → L3 Flash 视觉兜底)→ `services/purchase/line_ingest.py` 置信入账。

### 共用核心
- **写账闸** `line_agent.may_write`:仅 `record + statement/command` 才写;问句 / 否定 / 假设永不写。
- **置信分级** `services/expense/confidence.py::grade`(图文共用纯函数)。
- **入账编排归一** `services/purchase/confidence_post.book_by_confidence`(图文共用):建草稿 → 高置信且 `auto_book` 开则过账。`auto_book` 默认 = True(高置信直入,可撤销)。
- **数据卡** `services/line_binding/line_card.py::result_card`:Flex 四态(已入账绿 / 请确认琥珀 / 需补全灰 / 可能重复红)。
- **卡动作** `line_card_actions` + postback,防重放一次性令牌 `line_action_nonce`(PO-12)。
- **对话内改错** `services/expense/line_correct.py`(PO-13):冲销原单 + 建新草稿 + `corrected_from` 审计链。
- **编辑深链** = LIFF(`liff=purchase&doc=X&ws=Y`,套账门自动选,见记忆 `line-liff-edit-deeplink-complete`)。

### 已反超 Paypers
对话内改金额、四态透明数据卡、撤销(`void_doc`)。Paypers 只能「记 + 查 + 改一律甩网页」(逆向见记忆 `paypers-line-reverse-engineering`)。

---

## 5. 当前在做 / 未解决 backlog

采购进项车道的产品正本 = `docs/line-platform/02-procurement-canon.md`。当前最高价值三项:
- **P1E-2** 纠错 / 澄清 / 执行动作统一收口(“识别错了”进纠错闭环,不走拍照失败)。
- **回归测试** 固定真票样本(Amazon/CP ALL/Seafood/Little Betong),防金额、VAT、rounding、按钮策略回归。
- **诚实回复契约** 只陈述真发生的事,申报/过账文案严守三态。

`docs/smart-intake/19` 已折叠进产品正本,只作历史背景;完整 backlog 后续按 `02-procurement-canon` 拆。

---

## 6. 文档地图(按需取)

| 想干啥 | 读哪个 |
|---|---|
| LINE 方向 + 框架(本页) | `docs/line-platform/00`(本文件) |
| 采购进项产品正本 / 冲突裁决 | `docs/line-platform/02-procurement-canon.md` |
| 对话产业级设计正本 | `docs/smart-intake/15`(STP+HITL + 数据卡 + 引用/转圈) |
| LINE 大脑交接 | `docs/smart-intake/18` |
| 图片识别核心(L3 过度触发 / 触发器收紧) | `docs/smart-intake/09` |
| 文本路意图路由 / 字段映射 | `docs/smart-intake/10` |
| 竞品分类法 / 单据类型 / 字段对标 | `docs/smart-intake/16` |
| smart-intake 旧稿怎么读 | `docs/smart-intake/README.md` |

---

## 7. 施工纪律(LINE 是主路径)

- 改记账 / 改错主路径(P2/P3 类)**先报方案再动**;偏前后端 CRUD(P1 类)可直接做。
- 用 worktree 隔离(并行窗口常在改同片代码),开工先 `git pull --rebase`。
- 每个新文件 ≥1 测试;`compute_purchase_totals` 金标口径不动;金额/税额永不信 LLM。
- 守门 13 闸全绿 + 真账号 E2E;真机渲染 / 大脑表现留 Zihao 实测(代码窗口无真 LINE channel)。
- Conventional Commits;署名 `Co-Authored-By: Claude Opus 4.8 (1M context)`。收尾先跑 `/simplify` 再出报告。
