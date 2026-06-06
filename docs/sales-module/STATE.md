# STATE · 销项模块沙盒 · 接力状态卡

> 新窗口/下一棒**先读这张卡**,再按需翻 `docs/`。保持 ≤40 行有效信息,历史往下沉到「变更日志」。

## 当前状态(2026-06-06 · 已开建上线)

- **🚀 已开建上线**(Zihao 拍板破例):sandbox 已迁主项目,**Phase 1 后端 PO-1~6 全做完 + 上线 master + 真账号 E2E**。代码在主仓库 `services/sales/` + `routes/sales*.py` + `alembic 0006~0008`。prod 库已 apply 到 0008。alembic 追踪本次首次在 prod 立起(之前没有)。
  - PO-1 schema / PO-2 商品 CRUD / PO-3 Excel 导入 / PO-4 开票核心(连号 FOR UPDATE/开出不可改 409/VAT+WHT)/ PO-5 红冲补开(独立连号)/ PO-6 合规 PDF(reportlab·桌面有实物样票)。
  - **账套主体=卖方**(Zihao 纠正:会计事务所多公司):账套主体加开票字段(地址/总分公司/电话/VAT)· 选择账套弹窗改「只选不建」(新增去客户管理)· 真浏览器验 + 0 console error。
- **⏭️ 下个窗口先做**:**买方信息动态模块** `docs/15-buyer-info-spec.md`(买方类型选择器 + 字段状态机·公司/个人/外国/匿名)——当前完全没有,是 PO-4 表单/PO-10 前端的买方块基础。之后续 PO-7(发送)/PO-10(开票页前端,先出 HTML 草稿)。
- **阶段**:需求已澄清 + 设计骨架已铺。~~等两道闸~~ 已破例开建。
- **范围已定**(Zihao 拍板):统一智能录入引擎 + 销项第一出口 + 比 Paypers 更智能。见 `docs/00-overview.md`。
- **产出**:全套设计文档 `docs/00–09` + 泰语客户问卷 + 核心 schema 草案 `migrations/0001_sales_core.sql`。
- **没碰主仓库**:本沙盒零文件进 repo,不触发整顿守门,不进整顿进度统计。
- **死规则(Zihao 2026-06-05 强化)**:① 所有 UI 先做**桌面可浏览器实时预览的 HTML 草稿**(放 `C:\Users\skin3\Desktop\`)→ Zihao 预览通过 → 才实现(`docs/06` 文字方案 ≠ 草稿)· ② **全站禁 emoji 图标,用线性图标**(lucide/feather inline SVG)· ③ 窗口换手 = 上下文**到 50–70% 才换**(自主更新本卡 + 计划勾进度;没到别换、别为单 PO 换)· ④ **另一窗口完成后 → sandbox 移入主项目 → 在主项目内开发**。全部见 `docs/13-build-plan-po.md` §一。
- **UI 决策(Zihao 2026-06-04)**:单据编辑/详情用**弹窗(modal)· 不用抽屉(drawer)**。主按钮色以 `home-38-buttons.css` `#2563EB` 为准(DESIGN_SYSTEM §2.1 `#1a365d` 是旧值)。

## 已完成(可做的都做了)

- [x] 15 张客户需求图调研 + 拆解(销项 vs 进项 vs Paypers 参照)→ `docs/01-requirements.md`
- [x] 架构定调:统一录入引擎 + 销项出口 → `docs/00-overview.md`
- [x] 泰国税务合规研究(ใบกำกับภาษี 连号/不可改/红冲/e-Tax/ภ.พ.30)→ `docs/03-thailand-tax-compliance.md`
- [x] 数据模型(决策无关的核心表)→ `docs/02-data-model.md` + `migrations/0001_sales_core.sql`
- [x] API 契约草案(对齐现有 `routes/` 约定)→ `docs/04-api-contracts.md`
- [x] 竞品对比 + "更智能"落点 → `docs/05-competitive-paypers.md`
- [x] 前端方案(POS 点单式 + 四态 + i18n + 缓存)→ `docs/06-frontend-plan.md`
- [x] i18n key 清单(th/zh/en)→ `docs/07-i18n-keys.md`
- [x] 迁回逐文件落点 + 守门处理 → `docs/08-migration-guide.md`
- [x] 客户问卷(泰语,纯文本可贴 LINE)→ `customer-questionnaire/`
- [x] **主项目约束 + 守门闸权威清单**(实扫 pre-push/CI/铁律得出)→ `docs/10-mainproject-constraints.md`
- [x] **与既有 PRD 对齐**(进项 Paypers 归 MODULE_EXPENSE_PRD_v2 · 销项税对账归 MODULE_SALE_VAT_RECON_PRD · 本沙盒=销项开票)→ `docs/00` §边界 / `docs/10` §6

## ✅ 已落地 · UI 硬规定(2026-06-05 · commit 07b6ded · 已上线 prod)

- 全站 **14 处**按钮/切换黑底 → 品牌蓝 `var(--btn-blue)` #2563EB(不止草案估的 4 处)· 加 `--btn-blue` token 于 home-38。
- `check_ui_consistency.py` 加硬规则 **D1**(禁新增抽屉 `.drawer` · 存量冻结 120 · 新 UI 用 `.modal`)+ **D2**(按钮/切换黑底基线 0 · 只导航栏可黑)· 挂进 **pre-push 硬拦**。
- DESIGN_SYSTEM §2.1/§10 + CLAUDE.md §30 同步定调。bump ?v=→11850101 + 4 语 release_notes。
- 验证:`/api/version`=11850101 · prod home.css 含 --btn-blue + 原黑按钮转蓝。
- 判断点:`.brv2-filter-btn.active`(筛选 active)按"只导航栏黑"也改了蓝;若要它保黑作指示,单行可回退。
- 草案见 `docs/11-ui-hard-gate-draft.md`(已执行)。

## ✅ 客户已答 · 决策锁定(2026-06-05 · 见 `docs/09`)

- [x] Q1 → **先做快速开票;POS 拆成下一个独立项目**(库存字段本模块预留)
- [x] Q2 → **从商品图库菜单式点选**(商品必带图)· 扫码归 POS 项目
- [x] Q3 → **要 e-Tax 直报税局(需电子证书)"可行才做"** → Phase 1 先打合规地基(连号锁+不可改+红冲),e-Tax 留 Phase 3
- [x] Q4 → **系统内建 + Excel 导入 + 要库存系统(คลังสินค้า)**
- [x] 用户 = **会计事务所 + 客户公司自己** 都有 · 发送 = **邮件/LINE/打印全做** · **要 LINE 开单**

锁定后分阶段:Phase1 合规开票闭环 / Phase2 库存+LINE开单+应收 / Phase3 e-Tax直报 / POS=下一个独立项目。

## 下一棒该干什么 → 看 `docs/13-build-plan-po.md`(逐 PO 执行清单)

- **现状**:设计全就绪 + 客户已答 + UI硬规上线。**开建前置**:① 另一窗口(主项目当前活)完成 ② sandbox 移入主项目 ③ 在 master。**前置未满足 → 尚未开建**。
- **开建后**:按 `docs/13` Phase 1 的 **PO-1 → PO-11** 顺序做(schema→商品→单据核心→红冲→PDF→发送→e-Tax骨架→ภ.พ.30→前端→i18n验收)。窗口连做多个 PO 到 50–70% 上下文再换手。
- **UI 类 PO(PO-10/14)**:先出桌面可预览 HTML 草稿(`sales-invoice-draft.html` 等)→ Zihao 过 → 再实现。
- **客户补充细节(连号/VAT/渠道/商品图)= 全做兼容+可配置,无需问客户**(Zihao 2026-06-05 · 见 `docs/09` 末 + `docs/02`)。连号默认"前缀-年份-连续号不跳",可配前缀/重置/起始号(接旧账本)。
- **无遗留待办**:设计全就绪,等"另一窗口完成 → 移入主项目"开建。

## 关键纠偏(实扫主项目后修正 · 别再踩)

- schema 走 **Alembic**(`alembic/versions/`)· 不是 scripts/sql · 禁 `ensure_*`。
- `tenant_id` = **UUID**(已确认)· 但 `client_id` 要匹配 `clients.id` 实际类型(INTEGER/BIGSERIAL · 非 UUID · 迁回核实)。
- i18n = **4 语 zh/en/th/ja**(早期误写 3 语已修)· `check_i18n --strict` 硬闸。
- 闸 = pre-push 本地硬闸 + CI 6 jobs + 9 脚本(非 3-4 道)· 见 `docs/10`。
- 开票=高敏 · 先报方案+Zihao在场+真账号 E2E · 不无人值守自动合并。

## e-Tax 架构(已设计 · 为未来铺垫)· 见 `docs/12`

- **可插拔通道** `ETaxChannel` 接口罩住 4 档:Noop(只出PDF·Phase1默认)/ Email(ETDA时间戳·平替①·小客户)/ Provider(接中介)/ SelfHosted(自建)。
- Phase 1 就铺:接口 + `etax_submissions` 表 + `etax_channel` 配置 + **发票模型一次性带全 e-Tax XML 字段** + Provider/SelfHosted 桩(throw 待接通)。
- 开票流程留唯一 hook(开出后 `if channel: channel.submit(doc)`)· 未来拿到证书/选定中介 = 只填一个适配器,**不动开票主流程**。
- 合作者"自建 vs 中介"回复只决定填哪个桩 · **不卡 Phase 1**。Paypers 不开销项票/无 e-Tax(已查证)→ 此为超越它的净新增。

## 变更日志

- 2026-06-04 · 建沙盒 · 调研 15 图 + 定调 + 铺全套设计文档与 schema 草案。
- 2026-06-04 · 实扫主项目守门/铁律/既有 PRD · 补 `docs/10` 权威约束清单 · 修 i18n→4语 / Alembic / FK 类型 / 闸真相 / PRD 边界。
- 2026-06-04 · 对照 `DESIGN_SYSTEM.md`(20 节)· `docs/06` 补设计系统对照 + 复用组件(pearnlyConfirm/.drawer/.erp-subtab/.stat-card)· 标出主按钮色值冲突(以 home-38-buttons.css `#2563EB` 为准)。
