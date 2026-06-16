# 03 · 进项单作废:下游完整对冲 + 锁定期护栏(方案)

> 背景:已入账(posted)单在网页/LINE 可作废,但 `void_doc` 当前只反库存,**做账凭证、ภ.พ.30 进项税、付款凭证都没反**(对开了「做账」模块的租户 → 作废后账本与税表残留 = 账花了)。这是「posted 可更正/作废」与「想撤就撤、永不死路」的**前提地基**:更正 = 作废 + 重建草稿,作废不干净则更正出来的账就是错的。

## 1. 现状(已对真代码)

`post_doc` 入账时写 4 类下游;`void_doc` 只反 1 类:

| 下游 | 入账写入 | 现状作废反冲 |
|---|---|---|
| 库存 | `_apply_stock` 进货入库 | ✅ `_reverse_stock` 取负回冲 |
| 申报 PND(代扣) | — | ✅ 直接读 `purchase_docs.status='posted'`,作废即排除 |
| 做账凭证 | `acct_hooks.enqueue_posting`(source_type=purchase) | ❌ **未反** |
| 申报 ภ.พ.30(VAT) | — | ❌ 读 `journal_vouchers.status`,凭证没作废 → 仍计进项税 |
| 付款凭证 | 建单即付时 `pay_doc`(source_type=payment) | ❌ **未反**(void 不先撤付款) |

报税/账本全是**实时聚合**(`tax/aggregate.py`:PP30 取 `journal_vouchers status IN (posted,auto_posted)`,PND 取 `purchase_docs status='posted'`),无死快照 → **只要把状态翻干净,下游自动同步**。问题纯在 void 没翻干净。

## 2. 方案

让 `void_doc` 成为**完整反冲**,且在锁定期/已申报期**拒绝静默作废**(状态诚实)。

### 2.1 新增 `acct_hooks.void_for_source`(seam 层)
镜像 `enqueue_posting` 结构,但有一处**关键反差**:
- 模块未开通 `accounting` → no-op(与 enqueue 一致)。
- 找到源单的活跃凭证 → 走 `posting.void_voucher`(其内置 `_assert_period_open`)。
- **不吞错**(enqueue 为护业务路径用 SAVEPOINT 吞错;void 反过来:凭证作废失败必须让整事务回滚,否则账不一致)。`acct.period_closed`(409)即透传 → 作废被拒。

### 2.2 改 `void_doc`(`services/purchase/posting.py`)
顺序(同一事务,任一步抛错 → 全回滚 = 原子):
1. 守卫:非 posted 拒(draft 走 delete · 已 void 幂等返回)。
2. 已付(`paid_amount>0`)→ `_void_payment_vouchers(..., strict=True)` 撤付款凭证。
3. `acct_hooks.void_for_source(source_type='purchase', source_id=doc_id)` 作废做账主凭证。
4. `_reverse_stock` 库存回冲。
5. `status='void'`。

凭证若落在已结账/已申报期间 → 步骤 2/3 的 `void_voucher` 抛 `acct.period_closed` → 整作废回滚,前端/LINE 得诚实 409(「该期已结账/申报,请走当期红冲」),**不静默破账**。

### 2.3 `_void_payment_vouchers` 加 `strict` 参数
- `strict=False`(默认,`unpay_doc` 用):保持现有 best-effort(SAVEPOINT 吞错,不阻断付款 toggle)。
- `strict=True`(`void_doc` 用):不吞错,让 `period_closed` 等透传以触发整事务回滚。

## 3. 已接(P1 · 同批后续提交)
- **网页 posted「更正」入口**:`POST /api/purchase/docs/{id}/correct` → `posting.correct_doc` = `void_doc`(完整对冲)+ `docs.clone_as_draft`(逐列精确复制整单/全明细/bill 票图为新草稿 · 不重算金标口径 · `corrected_from` 审计链 · dedupe_key 置空避唯一约束)→ 前端详情「更正」按钮打开新草稿编辑(三步:作废→改→重新入账)。已结账/已申报期 → `acct.period_closed`(409)诚实拦。

## 4. 不做(留下一步)
- 已结账期间的**红冲**(reverse entry · 当期生成反向凭证替代直接作废):本步只做「拒绝 + 诚实提示」,红冲单独立项。
- 对话内(LINE)改错扩面到任意字段/第 N 笔:`line_correct` 现仅金额,后续接。

## 4. 验收
- 单测:`void_doc` 已付单 → 调 strict 撤付款 + `void_for_source` + 反库存 + status;模块关 → `void_for_source` no-op;`period_closed` 透传不被吞。
- 真账号 E2E(做账开通):LINE/网页记一笔高置信入账 → 生成 purchase 凭证 → 作废 → 凭证 void + PP30 进项税归零 + 库存回冲 + status=void。
- 回归:`_void_payment_vouchers` 默认行为不变(`unpay_doc` 链式撤付款测试仍绿)。
