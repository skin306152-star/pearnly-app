# 自动做账 · 05 施工文案(封板 · 交施工窗口照此)

> 设计已封板(00-04 + 设计稿 01-05)。施工只填空、不发挥。**前置:进项 Phase 1 已上线(凭证的主要原料就位)·套账隔离已收官。**

## 0. 三条硬规矩
1. **照搬不重画 + 设计语言**:设计稿 `Pearnly_做账_UI预览/` 01-05 入库当快照真源,**一律照 `docs/ui/DESIGN_LANGUAGE.md`**(收拢分层/北极星+行动卡/动作收进面板/**禁原生 prompt·用 .modal**/去 AI 字样)。挂视觉照搬闸 `test_design_fidelity`。
2. **借贷恒平 + 状态诚实**:不平凭证绝不落库/过账;拿不准一律 `pending_review`,绝不静默乱过(铁律#3)。钱 Decimal·反解业务单不重算。
   **+ 错账安全带三件套(C3·2026-06-10 并入)**:method 标注(auto/suggested/manual·可筛)· unpost 一键撤销重做(void+重判·绝不"改不回来")· 粒度 opt-in(新租户默认建议模式·auto_post=false·按 rule_key 逐条开自动)。
   **+ 数据源分级(C1)**:first_party(POS/销项/采购系统内发生)=confidence 100 直通;ocr=置信分流;bank=只建议人确认。屏6 银行对账(C4)=六大行对账单文件解析·复用 services/recon+importer。
3. **套账隔离 fail-closed**:每句 SQL 带 workspace_client_id;凭证号按主体按期连号。

## 1. 文件落点
- 路由:`routes/accounting_routes.py`。
- 服务:`services/accounting/{accounts,mappings,vouchers,review,posting,rules,books,settings,closing}.py`(<500·单一职责)。**`rules.py`=02 模板目录(纯函数)·`posting.py`=取业务→套模板→断言平→落库**。复用 sales/totals、reportlab、workspace_context、document 连号。
- 前端:`src/home/acct-{list,review,accounts,settings,books}.ts`。
- 导航:app-shell-html(做账组 + 自动凭证占位换真子项)+ core-boot(路由)+ module-nav(accounting 门控)。
- 业务 hook:进项 `purchase/posting` 已留 → 接 enqueue;销项 issue / POS 日结 / 付款 settle 各加一行 enqueue(**只加调用·不改其业务逻辑**)。
- 迁移:`alembic/0034+`(chart_of_accounts/account_mappings/journal_vouchers/journal_lines/accounting_settings/review_learned + 预置科目&映射 seed)+ ensure_*(NEW-DEBT-EXEMPT)。
- i18n 4 语;测试每新文件 ≥1 + 隔离/权限闸。

## 2. 错误码(4 语 · 不露原始码)
`acct.unbalanced 借贷不平 · acct.mapping_missing 缺科目映射 · acct.period_closed 该月已结账 · acct.not_pending 非待审 · acct.forbidden 无权限 · workspace.required 先选公司 · acct.unexpected`

## 3. 施工顺序(一次建完整模块 · 内部安全次序)
```
S1 数据层  迁移 0034+ · 预置科目+映射 seed · ensure · 套账隔离闸
S2 引擎    rules.py(R1-R9 模板)+ posting.py(套模板/解析科目/断言平/confidence/防重复)+ 单测每模板
S3 接口    accounts/mappings/settings → vouchers(列/详/审/改/作废/手工)→ review → books/tax-reports/financials → close-period/export
S4 hook    进项/销项/POS/收付款 各挂 enqueue(幂等·不改业务逻辑)
S5 前端    导航(做账组)→ 主屏 → 逐笔审 → 科目表 → 设置 → 出账本(照设计语言+稿)
S6 收口    四态全 · i18n4语 · 视觉照搬闸 · 隔离/权限闸 · /simplify
```

## 4. 验收(DoD)
- [ ] 守门 6 道全绿 + 单测(每新文件≥1·R1-R9 各≥1)。
- [ ] 视觉照搬闸过(5 屏·桌面+手机·**符合 DESIGN_LANGUAGE**)。
- [ ] 真账号跨套账 E2E:进项 post → 自动生成进货凭证(借贷正确)；销项开票 → 销售凭证；POS 日结 → 凭证；服务费 → 进待审 → 逐笔审选服务 → 过账 + 记忆 → 下次同供应商自动过；月末 close → VAT 结转凭证 → 出账本/试算表借贷平；B 套账拿不到 A。
- [ ] 借贷不平拒绝 · 缺映射进待审 · 防重复(同 source 二次 enqueue 不增凭证) · 角色 403。
- [ ] 账本/报税材料 PDF 生成(泰文)。

## 5. 已知坑(沿用)
- 业务 hook **只加 enqueue 调用·绝不改进项/销项/POS 业务逻辑**(它们已上线·改坏=回归事故)。
- enqueue 幂等(UNIQUE source + 去重);重放/补算不重复生成。
- ANY(%s) uuid 列必 ::uuid[];新 ensure NEW-DEBT-EXEMPT;新文件 RATCHET-EXEMPT;共享树只 add 自己 pathspec;i18n 加键必 prettier;改 src 必 build+add dist+bump。
- 凭证号连号 FOR UPDATE 防跳号;月末结账锁期后该期不可再生成/改(走调整分录)。
