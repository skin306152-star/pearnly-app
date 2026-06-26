# 自动报税 · 05 施工文案(封板 · 交施工窗口)

> 设计封板(00-04 + 设计稿 01-04)。只填空不发挥。**前置:做账(Phase2)落地(产出账本/VAT结转/WHT明细)——报税吃它的数。**

## 0. 硬规矩
1. **照搬 + 设计语言**:稿 01-04 入库快照,一律照 `docs/ui/DESIGN_LANGUAGE.md`(收拢/北极星+行动卡/禁原生弹窗/去AI字样)+ 四-bis 交互完整性。挂视觉闸。
2. **数字诚实 + 报前体检**:税表数字全从做账账本来、不重算;**报前必体检**(未结账/不平/超期/缺税号),硬异常拦,绝不让报错表(铁律#3)。0 税额照常生成。
3. **提交不可逆**:e-Tax 提交二次确认;已报不可改(更正走更正申报)。套账隔离 fail-closed,税号按主体。

## 1. 文件落点
- 路由:`routes/tax_routes.py`。
- 服务:`services/tax/{filings,aggregate,anomalies,efiling,certs,settings}.py`(<500)。`aggregate.py`=02 汇总规则;`anomalies.py`=报前体检;`efiling.py`=RD e-filing 提交/导出。
- 复用:做账 `journal_*`(销项/进项税科目汇总)· 进项 wht 明细 + 扣缴凭证 · reportlab 泰文 · workspace_context。
- 前端:`src/home/tax-{center,review,settings}.ts`。
- 导航:app-shell-html(报税组)+ core-boot(路由)+ module-nav(tax 门控)。
- 做账 hook:close-period 完成 → `generate_filings`(只加调用)。
- 迁移:`alembic/00xx`(tax_filings/filing_lines + tax_settings·或并 accounting_settings)+ ensure(NEW-DEBT-EXEMPT)。
- i18n 4 语;测试每新文件 ≥1 + 隔离/权限闸。

## 2. 错误码(4 语·不露原始码)
`tax.has_anomaly 报前有异常先处理 · tax.period_not_closed 本月还没结账 · tax.missing_tax_id 缺收款人税号 · tax.already_filed 已报不可改 · tax.efiling_failed 提交失败 · tax.forbidden 无权限 · workspace.required 先选公司 · tax.unexpected`

## 3. 施工顺序
```
S1 数据层 迁移 + tax_settings seed + 隔离闸
S2 引擎  aggregate(PP30 销−进/超期剔除/缺税号 · PND53/3 按payee) + anomalies 报前体检 + 每表单测
S3 提交  efiling(e-Tax 直报回执 / 导出官方格式) + certs(扣缴凭证关联/发送)
S4 接口  filings 列/详/recompute/file/mark-filed/export/settings
S5 hook  做账 close-period → generate_filings(只加调用)
S6 前端  导航 → 报税中心 → PP30复核 → PND复核 → 报税设置(照设计语言+稿)
S7 收口  四态 · i18n4语 · 视觉闸 · 隔离/权限闸 · 交互完整性逐动作 · /simplify
```
> e-Tax 直报 = 接 RD e-filing(门户/API·现实可能先做"导出官方格式手报",e-Tax API 视 RD 开放度·先报方案确认对接方式)。

## 4. 验收(DoD)
- [ ] 守门6道 + 单测(每表≥1)。
- [ ] 视觉照搬闸过(4 屏·桌面+手机·符合 DESIGN_LANGUAGE)。
- [ ] 真账号跨套账 E2E:做账结账 → 生成 PP30/PND53/PND3 → 数字 = 账本(销−进=应交·WHT 按 payee 分)→ 报前体检(造超期进项/缺税号 → 拦/剔除)→ 提交(导出或 etax)→ filed+回执 → 已报不可改;B 套账拿不到 A。
- [ ] 0 税额照常生成 PP30 · 留抵显示对 · 扣缴凭证生成/发送 · 缺税号硬拦。
- [ ] 交互完整性逐动作(e-Tax 二次确认+回执/体检拦/重算/发凭证)+ 字段空态。

## 5. 已知坑
- 做账没落地前报税无米下锅——**等做账上线再施工**。
- e-Tax API 对接现实先确认(RD 开放度)·先做导出手报兜底·别假设能直连。
- ANY(%s) uuid 必 ::uuid[];新 ensure NEW-DEBT-EXEMPT;新文件 RATCHET-EXEMPT;共享树只 add 自己 pathspec;i18n 加键必 prettier;改 src 必 build+add dist+bump。
