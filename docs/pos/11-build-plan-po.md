# POS 项目 · 11 逐 PO 施工计划

> ⚠️ 状态更正(2026-06-08):本计划内 PO-A1~B7 + 餐厅 PO-R1~R4 均【已施工并上线 prod】。
> 本文档是开工前的计划稿,正文各 PO 未逐项标"已完成"≠未做——以代码为准(别被"无完成标记"误导)。
> 明确仍延后(按设计,非遗漏):刷卡真实在线网关(Omise/2C2P)、B7 称重/会员积分/批发账期。

> 施工顺序总表。库存先、POS 后(Zihao 定调)。每个 PO:目标 / 新建文件 / 接口(04)/ 屏(UI)/ 验收(10)/ 完成判定。
> 每 PO 自含可上线一小块;做完即按 10 验收,过才进下一个。窗口连做多个 PO 到 50–70% 上下文再换手。

## 阶段 A · 模块底座 + 库存(先做)

### PO-A1 · 模块开关底座
- 目标:`tenant_modules` 表 + 开关读写 + 主程序导航按模块显隐(库存/POS/切收银台 按开关出现)。
- 新建:`alembic 0021` + `services/modules/store.py` + `routes/modules_routes.py`(`GET /api/me/modules`)+ `src/home/module-nav.ts`(导航显隐)+ 测试。
- 验收:开/关模块→导航项显隐;关模块调接口→`pos.module_disabled`。

### PO-A2 · 商品多单位 + 批次标志
- 目标:products 加列(base_unit/track_batch/track_expiry/is_weighed/min_stock/default_cost)+ `product_units` CRUD。
- 新建:`alembic 0022` + `services/products/units.py` + 扩 `routes/products_routes.py` + 测试。
- 验收:商品配多单位换算;能力块关时只用 base_unit。

### PO-A3 · 库存核心 + 出入库接口
- 目标:warehouses + inventory_stock + inventory_batches + inventory_transactions;入库/盘点/调整/近效期/查询接口(04 §4)。
- 新建:`alembic 0023` + `services/inventory/{store,ledger,fefo}.py` + `routes/inventory_routes.py` + 测试(FEFO/幂等/RLS)。
- 验收:入库带批效;扣减 FEFO;盘点生成调整;库存=流水物化。

### PO-A4 · 库存后台前端(/home)
- 目标:屏7 库存后台(列表/汇总/入库弹窗/盘点/低库存/近效期)接真接口 + 四态。
- 新建:`src/home/inventory-*.ts` + `static/home-NN-inventory.css` + i18n。
- 验收:屏7 按钮全通(05)+ 四态(07)+ 低库存红/近效期黄。

## 阶段 B · POS 收银

### PO-B1 · 收银员角色 + PIN 鉴权 + /pos 入口 + 开通
- 目标:role=cashier;pos_cashiers + PIN 登录(04 §1);登录分流加 cashier→/pos;开通收银 onboarding(屏8)。
- 新建:`alembic 0024`(terminals/cashiers/shifts)+ `services/pos/{auth,cashier}.py` + `routes/pos_auth_routes.py` + 登录分流改动(共用现有登录·自验不破)+ /pos 入口页 + 屏8 前端 + 测试。
- 验收:PIN 登录;cashier 落 /pos 偷不进 /home;开通选业态→批量开模块+建仓+建收银员。
- ⚠️ 高敏:按图施工(已授权免在场)+ 真账号 E2E(含老板/会计/超管登录不破)。

### PO-B2 · 班次 + 小票后端(核心)
- 目标:开班/交班(04 §5);建小票/退货/作废/promptpay/热敏/取单(04 §6,在线版,先不离线);连号(终端分段)+ FEFO 扣库存 + totals 价内外 + 幂等。
- 新建:`alembic 0025`(pos_sales/lines/payments)+ `services/pos/{shift,sale,refund,numbering}.py`(复用 totals/promptpay/pdf_thermal)+ `routes/pos_sales_routes.py` + 测试(信封/幂等/FEFO/退货回补/RLS)。
- 验收:核心流程 E2E §3(除离线)。

### PO-B3 · 收银前台(在线版)
- 目标:屏6 开班登录 + 屏1 收银主屏 + 屏3 挂单 + 屏4 退货 + 屏5 交班,接真接口 + 四态。
- 新建:/pos SPA 前端(选品/购物车/收款现金+扫码+卡/挂单本地/退货/交班)+ i18n。
- 验收:屏1/3/4/5/6 按钮全通(05)+ 四态(07)+ 流程 E2E。

### PO-B4 · 升级正式税票
- 目标:屏2;小票→全式 ใบกำกับภาษี(落 sales_documents·复用销项合规)+ full_invoice_id 回填 + 不重复计 VAT。
- 新建:`services/pos/upgrade.py` + 接 sales_documents + 屏2 前端 + 测试。
- 验收:E2E §3.6。

### PO-B5 · 离线层(PWA + 同步)★最高风险
- 目标:按 08 ADR 做 PWA(SW+manifest)+ IndexedDB outbox + 同步引擎 + 本地 totals(对齐服务端)+ `POST /sales/sync`。
- 新建:/pos service worker + IndexedDB 层 + 同步引擎 + `routes/pos_sales_routes.py` 加 sync + 本地 totals 等价测试。
- 验收:离线剧本 §4(断网开单/重开 outbox 在/恢复同步/超卖告警/重复补传 deduped)。

### PO-B6 · 销售报表
- 目标:屏9(04 §7)。
- 新建:`services/pos/report.py` + `routes/pos_report_routes.py` + `src/home/sales-report-*.ts` + 测试。
- 验收:数据与流水对账;E2E §7。

### PO-B7 · 业态能力块完善 + 收口
- 目标:餐厅(桌台/厨房单)、称重、会员积分等能力块按需补;i18n 4 语齐;全量验收闭环 + /simplify 收口。
- 验收:开各业态预设功能块按开关显隐正常;10 全量过。

## 顺序与依赖
```
A1 → A2 → A3 → A4   (库存可独立上线一小块)
        ↓
B1 → B2 → B3 → B4 → B5 → B6 → B7   (B2 依赖 A2/A3 的商品单位+库存扣减)
```

## 里程碑
- M1(A1–A4):库存模块上线,老板能管库存(POS 之前先有货底)。
- M2(B1–B4):POS 在线版上线,能卖货收钱出小票升税票自动扣库存。
- M3(B5):离线能力上线,断网可卖。
- M4(B6–B7):报表 + 全业态能力块 + 收官。

> 每 PO 完成判定见 10 §9。施工前必读 09 施工规约。

## 暂不做 · 留后续(Zihao 2026-06-08 拍板搁置 · 在此可找回)

- **刷卡真集成(Omise / 2C2P 在线支付网关)**:现"仅记录"模式够用(顾客在银行 EDC 刷,系统记一笔)。真在线刷卡 = 单独大项目(商户申请+对接网关+对账),回头再起。
- **POS 业态能力块 B7**:称重 · 会员积分 · 批发账期/应收。现只做了零售/药房/餐厅核心,这些能力块按需再补。
- 桌台硬删除 / 餐厅服务费智能默认 10% / 收银端消费收款设置 = 已并入收银收尾窗口做(2026-06-08),不在此搁置。
