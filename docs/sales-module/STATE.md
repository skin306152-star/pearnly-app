# STATE · 销项模块沙盒 · 接力状态卡

> 新窗口/下一棒**先读这张卡**,再按需翻 `docs/`。保持 ≤40 行有效信息,历史往下沉到「变更日志」。

## 当前状态(2026-06-06 · 已开建上线)

- **🚀 已开建上线**(Zihao 拍板破例):sandbox 已迁主项目,**Phase 1 后端 PO-1~6 全做完 + 上线 master + 真账号 E2E**。代码在主仓库 `services/sales/` + `routes/sales*.py` + `alembic 0006~0008`。prod 库已 apply 到 0008。alembic 追踪本次首次在 prod 立起(之前没有)。
  - PO-1 schema / PO-2 商品 CRUD / PO-3 Excel 导入 / PO-4 开票核心(连号 FOR UPDATE/开出不可改 409/VAT+WHT)/ PO-5 红冲补开(独立连号)/ PO-6 合规 PDF(reportlab·桌面有实物样票)。
  - **账套主体=卖方**(Zihao 纠正:会计事务所多公司):账套主体加开票字段(地址/总分公司/电话/VAT)· 选择账套弹窗改「只选不建」(新增去客户管理)· 真浏览器验 + 0 console error。
- **⏭️ 下个窗口先做**:**买方信息动态模块** `docs/15-buyer-info-spec.md`(买方类型选择器 + 字段状态机·公司/个人/外国/匿名)——当前完全没有,是 PO-4 表单/PO-10 前端的买方块基础。之后续 PO-7(发送)/PO-10(开票页前端,先出 HTML 草稿)。
- **📋 后端合规 + 开票全兼容规格** `docs/16-backend-compliance-and-output-spec.md`(与 15 并列·调研窗口审代码产出):A 双方信息冻结快照(已开票不可改·**合规硬伤**)· B §86/4 开票完整性闸 · C VAT 价内/价外 · D 折扣/优惠/内部价(现状只算不显示·要加百分比/整单/PDF显示)· E 纸张(A4/A5/热敏)+正副本(ต้นฉบับ/สำเนา)+留底≥5年+打印 · F 开具审批(多模式可开关)· G 日期历法(曼谷本地日/倒填护栏/佛历/账期)· H 模板(多公司品牌)· **J 税票+收据合并单 + 收款状态(Zihao 2026-06-06 拍板·本期做)** · I 完整性清单 P1~P2(报价转换/发送/WHT多档/PromptPay…)。**P0 硬伤=双方冻结+折扣显示+留底+合并单,建议优先**。
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

## 2026-06-06 · 买方模块 + 合规四块后端【已上线 prod + E2E 全过】(commit 87c21b7)

**做了什么**(spec 15 + spec 16 A/B/D/E1/E2/G/J · 迁移 0009~0011):
- 买方动态模块 `services/sales/buyer.py`(配置表/归一化/§B 完整性闸)+ 买方块随单据存。
- §A 双方冻结 `parties_snapshot`(开出冻结 · PDF 从快照渲染 · 改档案不动已开票)。
- §J 合并单 `tax_invoice_receipt` + 收款四列(无款不开)。
- D 折扣(行百分比 + 整单按比例摊 · PDF 折扣列)。E1/E2 纸张 A4/A5 + 正/副本角标。
- G 历法 `services/sales/dates.py`(曼谷本地开票日 + 倒填/未来护栏 + 佛历 + 账期)。
- 买方块前端**草稿** `桌面/sales-buyer-block-draft.html`(Zihao 已认可**逻辑**;**样式不按此草稿**,等 Zihao 最终设计稿再做 PO-10)。

**验证状态(全部真实做过)**:
- ✅ 本地全量 unittest **2399 OK** + ruff/black/check_ai_smell/check_file_size/import app 全绿。所有文件 <500。
- ✅ **prod 迁移已应用**(ssh `pearnly`→`psql $DATABASE_URL`·一个事务原子加 15+1 列·`ADD COLUMN IF NOT EXISTS`·`alembic_version` 推到 `0011_sales_terms`·已验列全在)。prod 不自动迁移(Dockerfile/store.py/db_migrations 无钩子)→ 走既定 ssh+psql 通道(Zihao 授权)。
- ✅ **已 push 上线**(`87c21b7`·pre-push 守门全绿〔补 6 个 RATCHET-EXEMPT〕·webhook 部署完成·两 worker `Application startup complete`·无 ImportError/Traceback)。
- ✅ **prod 真链路 E2E = 13/13 PASS**(在 prod 库跑真代码·全程事务 ROLLBACK·零残留)。过的:A 公司买方块入库+行折扣算税(180/12.60/192.60)· B 取号+`parties_snapshot` jsonb+买卖双方冻结 · **E 冻结证明:改卖方档案后已开票快照仍旧名 + PDF 从快照渲染** · F 红冲继承冻结快照 · C §B 匿名开完整税票被拦 · D §J 收据无款不开+补款后可开。

**产品决策(Zihao 2026-06-06 · 留后续)**:C 价内外=默认价外·单据级开关·不做行级;F 审批=本期不做(有客户再加·默认关·老板=审批人);H 模板/热敏=随 UI 一起设计;E3 pdf_sha256=可选有空再加。

**下一棒 = 按 `docs/16` §M「执行顺序到闭环」逐一做,每块做完即验**(Zihao 2026-06-06 拍板:把后端全做完→再前端→上线闭环):
1. C 价内外(§C·默认价外·单据级) 2. 省纸两联(§E2 `copies_layout=two_up`) 3. F 审批(§F·默认关·owner审批) 4. E3 `pdf_sha256`+热敏窄版(§E1/E3) 5. PromptPay/WHT多档/报价转换(§L1-3) 6. H 模板**后端管道**(§L4·视觉留设计稿) 7. PO-7 邮件发送(**LINE=高敏·留 Zihao 在场**) 8. PO-10 开票页前端〔按桌面样稿 **`Pearnly开票UI预览/index.html`** 向导式整流程 + buyer 草稿逻辑〕→ i18n 4 语 → 真账号 E2E → **上线闭环**。
> 卡口:**LINE 发送**不无人值守(等 Zihao 在场);prod 迁移走 ssh+psql 经授权。**H 模板视觉已定稿**(app.html 3 套预设)不再 gated。
> **整套前端"图纸"已出齐**(Zihao 2026-06-06「先出全套设计再施工」):`Pearnly开票UI预览/app.html`(模块工作台:列表/详情含作废红冲补开转换/商品/客户含买方类型/账套含品牌+模板/开票设置)+ `index.html`(开票向导:5步+输出设置+省纸+成功面板)+ `sales-buyer-block-draft.html`(买方逻辑)。**前后端契约 + 设置存储缺口见 `docs/16` §N。** PO-10 照这三份施工,视觉别另起。
> **按图施工保障 = `docs/17-frontend-handoff-and-acceptance.md`**(Zihao 担心漏功能/死按钮):全量「按钮→动作→接口」矩阵(精确 path · ✅有/🔧待建)+ 设计令牌锁死 + **验收 = 真浏览器自动点每个按钮断言路由真通 + 截图比对草稿** + 每屏完成判定。**🔧 待建接口(settings/send/promptpay-qr/convert + clients/seller 补字段)先于对应前端按钮做,否则必出死按钮。** 施工窗口照 §17 验收,不过不算完成。

## 2026-06-06(续)· §M 后端块 1-3 做完(本地验·**未 push·待 Zihao 授权 prod 迁移+上线**)

**做了什么**(§M 1-3 · 迁移 0012/0013 · 本地提交未 push):
- **§M1 C 价内/价外**(`price_includes_vat`·单据级开关·默认价外):`compute_totals` 价内反算
  `vat=base*rate/(100+rate)`,PDF 合计区按模式分支并单列 VAT;红冲/补开继承原单价内外。迁移 0012。
  顺带把金额算法从 `document.py` 抽到新 **`services/sales/totals.py`**(document 506→<500·`compute_totals` re-export)。
- **§M2 省纸两联**(`copies_layout=two_up`):`render_invoice_pdf` 正本+副本印同张 A4/A5(上下半幅
  Frame+虚线裁切线·`KeepInFrame` shrink·7 行明细实测仍单页)·热敏自动回落 separate。无 schema。
- **§M3 F 审批**(`approval_mode`·默认 none):状态机 draft→submit→pending_approval→(owner 批准取号)
  issued / 驳回→rejected→改→draft。新 **`services/sales/approval.py`**(状态迁移叶子)+ 抽出
  `document.finalize_issue`/`lock_for_issue`(直开与审批同一套取号/冻结/闸)。审批端点 owner-gated
  (复用 `_require_owner_or_super`)。迁移 0013(approved_by/at + rejected_reason)。
  ⚠️ `approval_mode` 策略源 = `sales_settings`(§M7·**尚未建**)→ 当前路由默认 none(行为不变),
  端点已就绪;**§M7 落地时把 issue 路由接 settings.approval_mode 即激活**(已留 seam)。

**验证(本地全做)**:全量 unittest **2431 OK** · ruff/black/check_ai_smell/check_file_size 全绿(全文件 <500)·
check_line_ratchet 全绿(已加 5 个 RATCHET-EXEMPT·新功能合理增长)·import app OK。`/simplify` 已收口
(pdf 复用 totals._d·删未用 subtotal_after)。HEAD=本地 6 commit(d613143..exempt)·**origin 仍在 a1169bf**。

**待 Zihao(高敏闭环卡口)**:① 授权 prod 迁移 0012+0013(ssh `pearnly`→`psql` 一事务 ADD COLUMN IF NOT EXISTS)
② 授权 push(=部署)③ push 后真账号 E2E 验价内外/省纸PDF/审批三态。**真账号 E2E + LINE 仍按铁律 #26。**

**下一棒(§M 续)**:4. E3 `pdf_sha256`+热敏窄版 5. L1 PromptPay / L2 WHT多档 / L3 报价转换
6. L4 模板后端管道 7. `sales_settings`(并激活 approval_mode)+ clients/workspace_clients 补字段
8. PO-7 邮件发送 9. PO-10 前端。

## 变更日志

- 2026-06-04 · 建沙盒 · 调研 15 图 + 定调 + 铺全套设计文档与 schema 草案。
- 2026-06-04 · 实扫主项目守门/铁律/既有 PRD · 补 `docs/10` 权威约束清单 · 修 i18n→4语 / Alembic / FK 类型 / 闸真相 / PRD 边界。
- 2026-06-04 · 对照 `DESIGN_SYSTEM.md`(20 节)· `docs/06` 补设计系统对照 + 复用组件(pearnlyConfirm/.drawer/.erp-subtab/.stat-card)· 标出主按钮色值冲突(以 home-38-buttons.css `#2563EB` 为准)。
