# 商户采购 · 05 施工文案(封板 · 交施工窗口照此执行)

> 这页是给施工窗口的"填空说明书"。设计已封板(00-04 + 设计稿 01-10)。**施工只填空,不发挥**——边界/错误码/文案都在这,临场发挥 = bug 来源。
> 前置:套账隔离已 100% 收官(STATE 确认)· 工作树清干净后从稳定基线起。

## 0. 三条硬规矩(施工第一天读)

1. **照搬,不重画**:设计稿 `Pearnly_采购_UI预览/` 01-10 **入库**(`tests/visual/snapshots/purchase/`)当唯一真源,令牌(色/间距/圆角/字号)逐字搬。挂**视觉照搬闸** `tests/visual/test_design_fidelity.spec.js`(POS 桌台那套):稿截图 vs 生产页 getComputedStyle 逐项比对,不像=红=推不上去。**禁止"我重新画一个差不多的"**(昨天的坑)。
2. **四态/边界全做**:见 04 §八表,每屏空/加载/错 + 边界**不得省**。`rows=0/失败` 绝不显示"成功"(铁律#3)。
3. **OCR/LINE 已授权放开**(Zihao 2026-06-08):直接做最优方案,**不用先报方案**。唯一底线 —— **现有事务所「LINE 拍图→识别中心」路径一字不破坏**,只在其上加分流。改前端必 `npm run build` + `git add static/dist` + bump `?v=`。

## 1. 文件落点(巨石封锁 · 铁律#17/21/23)
- 后端路由:`routes/purchase_routes.py`(`APIRouter` · app.include_router)。
- 服务:`services/purchase/{docs,suppliers,categories,intake,totals,documents}.py`(单文件<500·单一职责)。复用 `services/sales/totals.py`(VAT/WHT)、销项 reportlab(替代收据/扣缴凭证)、`services/sales/approval.py`、`services/inventory/*`、`services/ocr/*`。
- 前端:`src/home/purchase-*.ts`(主屏/录入/详情/供应商/设置 各文件·不进 home.js)。
- 导航:`src/home/app-shell-html.ts`(进项管理组重排)+ `core-boot.ts`(路由)+ `module-nav.ts`(expense 门控)。
- i18n:`static/dist/i18n-data.js`(4 语·加键必 prettier·bump)。
- 迁移:`alembic/versions/0031_*`…(见 01)+ 启动 `ensure_*`(标 NEW-DEBT-EXEMPT)。
- 测试:每新文件 ≥1;机械闸 `test_purchase_sql_isolation` / `test_purchase_permission_gate`。

## 2. 错误码字典(4 语 · 前端不露原始码 · 同销项 sales.* 风格)

| code | zh | th | en | ja |
|---|---|---|---|---|
| purchase.dup_invoice | 这张票像录过了,确认是新的再入账 | บิลนี้เหมือนเคยบันทึกแล้ว | This bill looks already recorded | この伝票は登録済みのようです |
| purchase.line_invalid | 有明细行填得不全 | มีรายการกรอกไม่ครบ | A line item is incomplete | 明細に未入力があります |
| purchase.amount_mismatch | 合计对不上,请检查 | ยอดรวมไม่ตรง โปรดตรวจสอบ | Totals don't add up | 合計が一致しません |
| purchase.supplier_inactive | 该供应商已停用 | ผู้ขายถูกปิดใช้งาน | Supplier is inactive | 取引先は無効です |
| purchase.tax_id_invalid | 税号不是 13 位 | เลขภาษีไม่ใช่ 13 หลัก | Tax ID must be 13 digits | 税番号は13桁です |
| purchase.not_draft | 已入账单据不可改 | เอกสารที่บันทึกแล้วแก้ไขไม่ได้ | Posted document can't be edited | 記帳済みは編集不可 |
| purchase.forbidden | 你没有此操作权限 | คุณไม่มีสิทธิ์ | You don't have permission | 権限がありません |
| workspace.required | 请先选择公司(套账) | โปรดเลือกบริษัทก่อน | Select a company first | 会社を選択してください |
| purchase.unexpected | 出了点问题,请重试 | เกิดข้อผิดพลาด ลองใหม่ | Something went wrong | エラーが発生しました |

## 3. 逐屏施工要点(配 04 互通地图 + 设计稿)

- **屏1 主屏**(`purchase-list.ts`):桌面表格/手机卡片(媒体查询断点已在稿)· KPI 4 张(进货/费用/可抵进项税/未付)· chip 筛 + 搜 · 行点击按 status 分流(draft→屏10 / posted→屏6)· 四态。
- **屏10 录入**(`purchase-form.ts` · ★最重):两栏(桌面)/堆叠(手机)· 票图+凭据(左)/信息+明细+合计(右)· 明细行 商品|服务 切换联动 WHT · 即时重算(税前→VAT→含税→WHT→实付,Decimal,逐步取整)· AI 预填字段绿标、未抽到黄底 · 重复票红条 · 存草稿/确认入账。
- **屏6 详情**(`purchase-detail.ts`):头+行+附件+票图+金额+付款卡 · 记付款/作废/(草稿)编辑 · 费用单隐藏进项税/SKU 段 · 作废灰态。
- **屏7/8/9 弹窗**:桌面居中/手机底抽屉 · 见 04 各自接口。
- **屏4 供应商**(`purchase-suppliers.ts`)/ **屏5 设置**(`purchase-settings.ts`):平铺页 · 页内动作弹窗 · 两级科目编辑(树)。
- **屏3 LINE**:说明页 + 接 `/expense`;LINE bot 改动见 PO-5。

## 4. 施工顺序(一次建完整模块 · 内部安全次序 · 非"分批上线")

> Zihao 定调:**设计已一次封板,施工一口气建到整模块完工再交付**,不"上线一半再设计后半"。下面是窗口内部"先骨架后管线"的写码次序,全在同一套封板设计下。

```
前置修(开工即做):
  P0a OCR 判方向+抽全卖方(扩 services/ocr · 先报方案)
  P0b expense 模块注册业态预设 + 后端 assert_module_enabled + 导航数据驱动门控
  P0c 迁移号 0031+ · 进项管理组重排 + 凭证中心改名归位

主建(OCR/LINE 放开做最优·不报方案):
  S1 数据层  迁移 0031-0033 + ensure_* + 套账隔离闸
  S2 后端    suppliers/categories/settings → docs/lines(建/列/详/post/pay/void/delete) → intake 分流 → 凭据生成 → summary
  S3 前端    导航 → 主屏 → 录入(屏10) → 详情 → 三弹窗 → 供应商/设置 → LINE 入口
  S4 联动    进货入库 / 进项税+WHT 汇总 / 应付聚合 / 做账 hook(留)
  S5 收口    四态全 · i18n 4 语 · 视觉照搬闸 · 机械闸(隔离/权限) · /simplify
```
> 每段做完跑守门 6 道。OCR(P0a)/LINE 放开做最优方案,只守"不破坏现有事务所识别中心路径"。

## 5. 验收(Definition of Done · 一次拎包入住)

- [ ] 守门 6 道全绿 + 单测(每新文件 ≥1)。
- [ ] **视觉照搬闸通过**(10 屏稿 vs 生产页·桌面+手机两视口)。
- [ ] 真账号**跨套账 E2E**:A 套账拍进项票→AI分流→录入(含服务行 WHT)→确认入账→进库存→进项税+WHT 进汇总→记付款;B 套账拿不到 A 的任何数据(9/9 式)。
- [ ] dedupe 防重复票 · intake 三路分流(文字/进项票/低置信→inbox)· 角色 403。
- [ ] 替代收据/扣缴凭证 PDF 生成(泰文合规·复用销项模板)。
- [ ] 四态全屏覆盖 · 错误码 4 语不露原始码。
- [ ] 桌面端 + 手机端真机/视口都验(铁律:两端都做)。
- [ ] OCR/LINE:现有事务所「拍图→识别中心」路径回归验证不破坏。
- [ ] 老租户零破坏(expense opt-in·关了不报错)。

## 6. 已知坑(前窗口/邻模块血泪 · 别重踩)
- `ANY(%s)` uuid 列必 `::uuid[]`(POS catalog 空网格真因)。
- 新 `ensure_*` 标 `NEW-DEBT-EXEMPT`;新文件 ratchet 标 `RATCHET-EXEMPT`。
- 共享工作树多窗口:只 `git add <自己 pathspec>`,禁 `add -A`/`amend --pathspec`。
- i18n 加键必 prettier;改 src/* 必 build + add dist + bump。
- 钱用 Decimal;WHT/VAT/凑整逐步取整(餐厅服务费 ±1 分教训)。
- 套账隔离每句 SQL 带 `workspace_client_id`,运营接口缺套账 = fail closed。
