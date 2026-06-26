# 自动报税 · 02 税表汇总规则(★核心 · 从账本怎么算出每张税表 + 报前异常检查)

> 引擎:`services/tax/aggregate.py`(从做账/进项汇总出每张表)+ `anomalies.py`(报前体检)+ `efiling.py`(e-Tax 提交/导出)。**不重算业务**——取做账账本已记的数。钱 Decimal。

## PP30(增值税)
```
output_vat = 本期"销项税"科目贷方合计(做账·来自销项/POS 开票)
input_vat  = 本期"进项税"科目借方合计(做账·来自进项·仅【有效可抵】)
net = output_vat − input_vat
  net > 0 → 应交(填 PP30 应纳税额)
  net < 0 → 留抵(carry forward 下月,填留抵)
```
**有效可抵过滤(报前异常·关键)**:
- 进项票开票日**超 6 个月**(泰国进项税 6 月失效)→ 剔除,记 anomaly「超期·已不抵 ฿X」。
- 进项票**缺供应商税号** → 不计入可抵,记 anomaly「缺税号·未计」。
- **0 也要报**:net=0 也生成 PP30(file_zero·泰国月度强制)。

## PND53 / PND3(预扣税)
```
取本期进项里 item_type=service 且 wht_amount>0 的付款,按收款人:
  payee = 公司(juristic) → 进 PND53
  payee = 个人(individual) → 进 PND3
每笔:payee/税号/income_type/base/rate/wht;汇总 SUM(wht) = 该表应缴。
扣缴凭证:复用进项已生成的 wht_cert;缺收款人税号 → cert_status=missing_tax_id + anomaly。
```
**报前异常**:缺收款人税号(开不了凭证、报不了)→ 拦 + 「去补税号」落点。

## 报前体检(anomalies · 提交前必跑 · 状态诚实)
| 检查 | 处理 |
|---|---|
| 本期**未结账**(做账没 close)| 提示「先去做账结账」· 数据可能不全 |
| 有**借贷不平/待审凭证** | 提示先处理(数据不准不让报) |
| 进项超 6 月 / 缺税号 | 列出 + 剔除/不计 + 落点去补 |
| 银行对账未完成 | 软提示(可报·建议先对完) |
> 体检过 → 可提交;硬异常(缺税号要报的)→ 拦。

## 提交(efiling.py)
- **e-Tax 直报**:settings.efiling_connected → 连 RD e-filing 提交对应表 → 拿 receipt_no 回填 · status=filed。**不可逆 → 提交前二次确认。**
- **未连**:导出 RD 官方格式(PP30/PND xlsx/txt)→ 用户手工上传 RD 门户 → 回来「标记已报」。
- 提交后:status=filed + receipt_no + filed_at;做账对应期可锁。

## 触发 / 幂等
- 做账 `close-period` 完成 → 自动生成本期 tax_filings(prepared)。也可手动"重算本月"。
- UNIQUE(period,kind) 防重复;重算覆盖 prepared,filed 的不动(已报不可改·错了走更正申报)。

## 测试(每表 ≥1)
PP30 销−进=应交(含超期剔除/缺税号不计/0也生成)· PND53/PND3 按 payee 类型分 + 汇总 + 缺税号拦 · 报前体检(未结账/不平/超期)· e-Tax 提交回执 / 导出格式 · 已报不可改 · 套账隔离。
