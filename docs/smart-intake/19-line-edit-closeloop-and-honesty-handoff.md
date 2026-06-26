# 19 · LINE 记账车道:改错闭环扩面 + 草稿可见可编辑 + 诚实四态(施工交接)

> 给下一个施工窗口。承接 `15`(对话产业级)/`18`(大脑交接)/`docs/line-platform/00`(车道总纲)。
> 本批的来源:2026-06-16 逆向竞品 Paypers LINE 真机 + Zihao 拍板「不可破产品边界」。
> 别重画设计,别 big-bang 搬存量;按下面优先级逐条做,每条带验收标准。

---

## 0. 先读现状(已建的别重做 · 都对过真代码)

| 能力 | 状态 | 锚点 |
|---|---|---|
| LLM 大脑(意图/槽位/护栏) | ✅ 已上线 | `services/expense/line_agent.py`(record/query_summary/query_detail/undo/edit/chat/out_of_scope·`may_write` 闸·问句/否定/假设永不写·LLM 绝不产金额) |
| 置信驱动入账 STP+HITL + 四态数据卡 | ✅ | `services/expense/confidence.py` + `services/line_binding/line_card.py` |
| 查账(汇总+明细)+ 撤销 | ✅ | `line_expense.py:147-154`(undo→`posting.void_doc`) |
| **对话内改金额(PO-13)** | ✅ 已上线 | `services/expense/line_correct.py`(「上一笔改成550」→冲销原单+建新草稿+确认+`corrected_from` 审计链) |

**Paypers 对比结论(真机)**:它只能"记 + 查 + 改一律甩网页",我们已有的对话内改金额它结构上做不到。本批是把这个已反超的优势做厚,不是补课。

---

## 1. 不可破边界(每条施工都受它约束)

入账/申报三态,文案不许越级:
- **已入账** = 复式分录真写入账簿(`status=posted`)。
- **已计入申报草稿** = 已进本期 ภ.พ.30 / ภ.ง.ด. 待复核。
- **已申报** = 必须真通过授权 e-Filing 提交、取得税局回执才能说。**绝不在聊天里假装报税成功。**

架构铁律:**LLM 只听懂/抽取/拆分/意图/解释;借贷金额、税额勾稽、税期、可否抵扣、锁期、提交状态一律确定性代码算。** 详见记忆 `line-accounting-honest-status-boundary`。

---

## 2. 别动 · 并行窗口正在做(2026-06-16 在跑,避免撞车)

`#4 多图排队(per-user 串行)` / `#7 收入vs支出(保守不误记)` / `#8 数量解析(split_qty_price)` / `#9 单笔路 date·vendor 平价` / `#10 /simplify 抽共享 booker·卡片发射器`。
→ 这些主要动 `services/expense/line_quick_entry.py`、`line_expense.py` 的记账/解析段。**本批开工前先 `git pull --rebase`**,确认它已合入再动 `line_correct.py` / 前端草稿列表。

---

## 3. 本批要做(优先级 + 验收 + 文件)

### P1 · 草稿可见可编辑 / 入账锁定(backlog #1 · 逻辑反了 · 最高价值 · 不依赖外部)
**现状病灶**:识别完的草稿在网页列表不显示;点入账后才显示却又不能改。**应改成**:
- 草稿 / 需补全 在采购列表**可见 + 可编辑 + 可补全**;
- 入账 = `posted` 定稿**只读**(只能撤销/冲销,不能原地改)。

验收:① 网页采购列表能看到 LINE 来的 `draft`(含 `field_confidence` 标黄项)并可改保存;② `posted` 单在列表只读,改动入口变"撤销/更正";③ 真账号 E2E:LINE 记一笔草稿 → 网页列表可见可改 → 入账 → 变只读。
涉及:前端采购列表 + 详情(`src/home/purchase-*.ts`)、`routes/purchase_routes.py` 的 list/get 过滤(别只返 posted)。

### P2 · 改错闭环扩面(line_correct 从"窄版"做厚)
现 `line_correct.py` 只能:**改金额 / 只认"上一笔" / 改完压平成单行**。三处缺口逐个补:

1. **改任意字段**(现非金额→`exp_edit_web` 甩网页,`line_expense.py:165`):支持改 科目 / 供应商 / 日期。
   - 大脑 `line_agent` 已抽 `vendor_name`/`date`/`expense_type` 等槽位,扩 `request_correct` 接收"改什么字段→什么值",`_corrected_data` 按字段落。
   - 验收:「上一笔改成水电费」「卖家改成 7-11」「日期改成昨天」都能对话内完成,出确认卡,过 auto_book。
2. **按"第 N 笔"引用**(现 `_find_last_posted` 是 `LIMIT 1`):query_detail 列了表后,「第 1 张改成 100」要能定位到列表第 1 项。
   - 把 query_detail 列出的 doc_id 顺序存进 `conversation.pending`(或会话态),改错时按序号取 id。
   - 验收:复现 Paypers 那段——查明细 → 「第一张金额改为100」→ 改中第 1 笔(不是最近一笔)。
3. **保多行明细**(现 `_corrected_data` 重建单行 goods → 多品项票一改塌成 1 行):只改被指定字段,其余行/明细原样复制。
   - 验收:4 品项票改总额/某字段后,新草稿仍是 4 行,`compute_purchase_totals` 后 `grand_total` 不漂(与 #8 同口径,别让 LLM 算金额)。

### P3 · 诚实回复契约(PO-14 · 配合 P1/P2)
- 工具执行结果 → 回复**只陈述真发生的事**:写了就说"已入账/已存草稿",没写绝不说成功;改错说清"原单已冲销、新草稿/已入账"。
- 申报相关文案严格按三态;`exp_*` i18n 文案四语齐(`line_i18n`)。
- 验收:单测覆盖"工具返回 None / 部分成功 / 冲销失败"时文案不谎报。

### P4(次批 · 可选)
backlog #2 单据类型显人话、#3 逐条明细 OCR 增强、#6 替代收据 PDF、#11 doc_type 枚举扩。本批不做,留指针。

---

## 4. 施工纪律(LINE 是主路径)

- **先报方案再动** P2/P3(改记账/改错主路径);P1 偏前后端 CRUD 可直接做。
- 用 **worktree** 隔离(并行窗口在改同片代码);开工 `git pull --rebase`。
- 每个新文件 ≥1 测试;`compute_purchase_totals` 金标口径不动;金额/税额永不信 LLM。
- 守门 13 闸全绿 + 真账号 E2E;真机渲染/大脑表现留 Zihao 实测(本窗无真 LINE channel)。
- Conventional Commits;署名 `Co-Authored-By: Claude Opus 4.8 (1M context)`。
- 收尾先跑 `/simplify` 再出报告。

---

## 5. 验收后能讲的一句话

Paypers 只能"记+查+甩网页改";做完本批,Pearnly 能**在对话里改任意字段、按第 N 笔精确定位、改完仍是真复式账、四态诚实不谎报申报**——这是"票据收集器"和"能对话改账的自动记账"的分界线。
