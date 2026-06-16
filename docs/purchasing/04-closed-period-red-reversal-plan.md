# 04 · 已结/已申报期的更正与作废:红冲(reversing entry)方案

> 承接 `03`(作废完整对冲 + posted 更正)。03 对**已结账/已申报期间**的作废/更正是 `409 acct.period_closed`
> 硬挡——这是"死路",与 Zihao「永不死路」冲突。本批用**红冲**替代硬挡:已报历史绝不篡改,在**当前
> 开放期间**做反向凭证冲销。Zihao 拍板 A/B 均按建议(见 §3)。

## 1. 原则(合规红线)

- **已申报的历史期间绝不改动**:原单做账凭证留在原期不动(否则破坏已提交税局的账)。
- 错了 → **当前开放期间**生成一张**反向凭证**(借贷对调、金额科目照原单)冲掉影响。
- 净效果跨期为零;调整落在当期 → **本期 ภ.พ.30 自动含此调整**(RD 正确做法:调整进当期申报,不去修订已报期)。

## 2. 怎么走(void / correct 共用)

作废/更正时,对每张相关做账凭证(进项主凭证 + 付款凭证):
1. 凭证期间 **开放** → `posting.void_voucher`(置 void · 现有路径,03 已上线)。
2. 凭证期间 **已结/已申报** → `posting.reverse_voucher`(新):当前开放期插入反向凭证(借贷对调),
   原凭证保持 posted 不动。
3. 库存照常逐笔回冲(库存不锁期);purchase_doc 标 `void`;更正再叠 `clone_as_draft` 出可改草稿。

判定:`acct_settings.is_period_closed(settings, voucher.period)`(`closed_through` 水位)。

## 3. 拍板项(已定)

- **A**:红冲落当前期 → 调整**本期 ภ.พ.30**(不动已报历史期)。✅ 按 RD 正确做法。
- **B**:极端边界——连当前月也已结(无开放期可红冲)→ `reverse_voucher` 抛 `acct.no_open_period`(409)
  诚实告知"无开放期间,请先重开本期再更正",不静默。

## 4. 落地(纯 accounting + purchase · 零 LINE 撞车)

- `services/accounting/posting.py::reverse_voucher(cur, *, tenant_id, ws, voucher_id, created_by)`:
  取原凭证+行 → 今日期间已结则抛 `acct.no_open_period` → 行借贷对调 → `jv.insert_voucher`
  (`source_type=f"{原}_reversal"` 避 `uq_jv_source` 撞已 posted 原单 · `voucher_date`=今日 ·
  `status=auto_posted` · 描述「红冲 原票号」)。无行(待审壳)→ no-op。
- `services/accounting/hooks.py::void_or_reverse(cur, *, ..., voucher_id, created_by)`(seam):
  按凭证期间选 `void_voucher` 或 `reverse_voucher`。`void_for_source` 改走它;`void_voucher`
  seam 包装由 `void_or_reverse` 取代。
- `services/purchase/posting.py::void_doc` + `_void_payment_vouchers(strict)`:改调 `void_or_reverse`
  (透传 created_by)。**已结期不再 409 挡死 → 改为红冲**(B 边界仍 409 诚实拦)。

## 5. 验收

- 单测:`reverse_voucher` 行借贷对调 + 今日已结抛 `no_open_period` + 无行 no-op;`void_or_reverse`
  开放→void/已结→reverse;`void_doc` 已结期走红冲不抛 409。
- 真账号 E2E(做账开通 + 结掉上期):上期入账单作废/更正 → 本期生成反向凭证 + 原凭证不动 +
  本期 ภ.พ.30 含红冲 + purchase_doc=void。
- 回归:开放期 void/更正行为不变(03 单测仍绿)。
