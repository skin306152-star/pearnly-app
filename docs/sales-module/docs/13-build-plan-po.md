# 13 · 销项模块 · 建设执行计划(按 PO · 可执行清单)

> 这是开建后的逐 PO 清单 + 铁打执行规矩。接力窗口:先读 `STATE.md` → 本文件找下一个未完成 PO → 干。
> 设计依据 `docs/00–12`。迁移落点 `docs/08`。主项目约束/闸 `docs/10`。

---

## 一、铁打执行规矩(每个窗口、每个 PO 都守 · 违反即返工)

**R0 · 不成整顿对象**:新代码一律按整顿理想形态写 —— 单文件 <500 行、单一职责、无循环依赖、
每个新文件 ≥1 测试、schema 走 **Alembic**(禁 `ensure_*`)、SQL 参数化、多租户 `tenant_id`+RLS、
钱 `NUMERIC`、时间 `TIMESTAMPTZ`、去 AI 味、Conventional Commits + 署名 Opus 4.8。全套见 `docs/10`。

**R1 · 窗口换手 = 上下文到 50–70% 才换**:一个窗口**持续做、连做多个 PO**,直到上下文用到 **50–70%**
→ 自主更新 `STATE.md`(交接卡)+ 本文件勾掉已完成 PO → 换窗口。**没到 50% 别换、别为单个 PO 换窗口**;
**到了 70% 必须换**(留余量写交接,别撑爆)。

**R2 · UI 先出"可浏览器预览的草稿"放桌面**:任何新增 UI(页面/弹窗/组件)→ 先做一个**能在浏览器
直接打开、实时预览的 HTML 草稿**(放 `C:\Users\skin3\Desktop\`,文件名见各 UI PO)→ **Zihao 浏览器
预览 → 通过 → 才动手实现**。`docs/06` 的文字方案 ≠ 草稿 ≠ 开工许可。改完真浏览器复验(非 grep)。

**R3 · 全站禁 emoji 图标**:任何图标用**线性图标**(lucide/feather 风 · inline SVG · `currentColor` ·
stroke 1.8 · round caps),**不准用 emoji 当图标**。`check_ai_smell` 拦注释 emoji;UI 图标靠草稿评审 + 复验守。

**R4 · 迁移时机/方式**:**另一个窗口(主项目当前活)完成后** → 把本 sandbox **移入主项目** →
**在主项目内**按 PO 开发(不在桌面写代码)。落点逐文件见 `docs/08`。net-new 文件走 **RATCHET-EXEMPT**。
**开票=钱/合规高敏**:取连号/开出不可改/生成税票/发送 → 先报方案 + 真账号 E2E(铁律 #16/#26)· 不无人值守自动合并。

**R5 · 每个 PO 完成判定**:代码 <500 · 配测试 · `pre-push` + CI 全绿 · 含 UI 则真浏览器验 · 该删的旧件同 PR 删。

---

## 二、PO 清单 · Phase 1(合规开票闭环)· 按顺序

> 窗口吃量参考:**一个窗口约 2–3 个后端 PO,或 1 个 UI PO(含预览往返)**,以实际 50–70% 上下文为准,不硬绑。

| PO | 目标 | 落点 | 测试 | 高敏 |
|---|---|---|---|---|
| **PO-1** | DB schema:products / sales_documents / sales_document_lines / document_number_sequences / etax_submissions(留位)+ 每客户 `etax_channel` 配置 + RLS | `alembic/versions/NNNN_sales_core.py`(转写自 `migrations/0001`)| 迁移幂等 + RLS 租户隔离 | — |
| **PO-2** | 商品主数据 CRUD + 按 code/barcode/qr 查 | `routes/products_routes.py` + `services/sales/products.py` | 契约测试 `test_products_routes_contract.py` | — |
| **PO-3** | 商品 Excel 批量导入 | `services/sales/product_import.py` + 路由 | 导入解析 + 行校验测试 | — |
| **PO-4** | 销项单据核心:建草稿 / 正式开出(**事务取连号**)/ 作废 / 取详情 / 列表 · **不可变写保护** · 金额+7%VAT 计算 | `routes/sales_routes.py` + `services/sales/document.py` + `services/sales/numbering.py` | 连号不跳 / issued 拒改(409)/ VAT 算对 / 取号并发 | 🔴 |
| **PO-5** | 红冲 ใบลดหนี้ / 补开 ใบเพิ่มหนี้(引用原单 · 自身连号)| `services/sales/credit_note.py` + 路由 | 红冲引用 + 连号测试 | 🔴 |
| **PO-6** | 合规 PDF 生成(ใบกำกับภาษี/ใบเสร็จ · 连号+双方税号+VAT分列 · 复用 weasyprint)| `services/sales/pdf.py` | 字段齐全 + 快照测试 | 🔴 |
| **PO-7** | 发送:邮件 / LINE / 打印(三通道)| `services/sales/send.py`(复用 邮件/line_webhook)| 三通道分发测试 | 🔴 |
| **PO-8** | e-Tax 可插拔骨架:`ETaxChannel` 接口 + `NoopETax` + Provider/SelfHosted 桩 + issue hook | `services/sales/etax/*`(见 `docs/12`)| Noop 不报 / hook 调用 / 桩 throw 待接通 | — |
| **PO-9** | 销项汇入 ภ.พ.30(扩 `services/vat/` + `vat_excel_routes` 加销项数据源)| 改现有 vat 模块 | 进销汇总数字对 | 🔴 |
| **PO-10** | 前端 · 销售发票页:列表 + **开单弹窗(.modal 不用抽屉)** + 菜单图卡选品 + 手输码 + 实时算税 | `src/home/page-sales-invoices.ts` + `sales-*.ts`(替占位)| 真浏览器验 + 四态 | 🔴(UI · **先桌面草稿** `sales-invoice-draft.html`)|
| **PO-11** | i18n 4 语补全(zh/en/th/ja · `check_i18n --strict`)+ 整体验收(真账号 E2E 开一张票全链路)| `i18n-data` + 验收 | check_i18n 0 缺 + E2E | 🔴 |

## 三、PO 清单 · Phase 2(库存 + LINE 开单 + 应收)

| PO | 目标 |
|---|---|
| PO-12 | 库存 `inventory_*`(扣减/查询/缺货提醒)+ 后端 + 测试 |
| PO-13 | LINE 开单(在 line_webhook 加 intent:发文/图 → 提取 → 确认 → 开单)+ 测试 |
| PO-14 | 应收追踪页(账龄 30/60/90 + 催收 LINE/邮件 + 银行回款核销)· UI 先桌面草稿 `receivables-draft.html` |

## 四、PO 清单 · Phase 3(e-Tax 直报)

| PO | 目标 |
|---|---|
| PO-15 | 接通 e-Tax:先 `EmailETax`(ETDA 时间戳 · 免证书);Provider/SelfHosted 待合作者定 + 拿证书后填(见 `docs/12` 接通清单)|

> POS = **下一个独立项目**,不在本计划。

---

## 五、进度勾选(窗口完成 PO 后在此打勾 + 写日期/窗口)

- [ ] PO-1  - [ ] PO-2  - [ ] PO-3  - [ ] PO-4  - [ ] PO-5  - [ ] PO-6  - [ ] PO-7
- [ ] PO-8  - [ ] PO-9  - [ ] PO-10  - [ ] PO-11  - [ ] PO-12  - [ ] PO-13  - [ ] PO-14  - [ ] PO-15

> 启动前置:① 另一窗口(主项目当前活)完成 ② sandbox 已移入主项目 ③ 在 master。
> 现状:**前置未满足 → 尚未开建**(本计划就绪,等迁入主项目)。
