# 📊 STATE · Pearnly 项目状态

> **最近更新**:2026-05-19 · **按量付费系统全面落地** · cache bust **v=11835200** · 任务 1-6 完成

---

## 🚀 按量付费系统(铁律 · 任何窗口先读)

> 旧订阅系统(trial/monthly/yearly/lifetime)已下线,系统改为按量付费。
> 任何接力窗口必须遵守以下约定,不得擅自改回旧模型。

### 计费模型

| 项 | 规则 |
|---|---|
| 单位 | 按 OCR 页数(`pages`)计费 |
| 第一档 | 前 200 张/月 → **฿1.50/张** |
| 第二档 | 超过 200 张 → **฿0.75/张** |
| 重置 | **Asia/Bangkok**(UTC+7)每月 1 日 00:00 自动重置(年月由 `_bkk_year_month()` 锚定) |
| 存储 | 钱包余额 = `tenant_credits.balance_thb`(NUMERIC(12,2)) |
| 月用量 | `monthly_page_usage(tenant_id, year_month)`(YYYY-MM, Asia/Bangkok) |
| 流水 | `credit_transactions`(type ∈ topup/usage/adjustment) |

### 角色判定

- `users.invited_by IS NULL` → **owner**(可见余额 / 充值入口 / 报表导出 / 余额预警)
- `users.invited_by IS NOT NULL` → **employee**(屏蔽以上,只能扫单)
- `users.is_billing_exempt = TRUE` → **豁免账号**(不扣费 · 不预警 · 不入流水)
  - 内部白名单:`skin306152@gmail.com`、`mrerp@outlook.co.th`

### 并发与一致性

- `deduct_company_credits` **必须** `SELECT ... FOR UPDATE` 锁 `tenant_credits` 行(已实现)
- 在事务内完成:① 锁行 ② 读 monthly_usage ③ 计算分档 ④ 扣款 ⑤ 写流水 ⑥ 更新月用量
- 一律走 Asia/Bangkok 时区算月度,不要用 `_datetime.now()` 裸取(会被服务器 TZ 漂移)

### 多公司(Task 3)

- `users.active_tenant_id`(可空 UUID · `ON DELETE SET NULL`)优先于 `users.tenant_id`
- `auth.get_current_user_from_request` 已自动覆盖 `user["tenant_id"]`(若 active 存在)
- JWT **不**变(`tenant_id` 字段保留,但运行时被 active 覆盖)
- API:`GET /api/my-companies` / `POST /api/switch-company`

### 邮件通知(Task 5 · 仅泰语 · 必须 try/except)

| 函数 | 触发点 | 防骚扰 |
|---|---|---|
| `send_topup_approved_email` | `/api/admin/credits/topup/approve` 成功后 | 无 |
| `send_low_balance_email` | `deduct_company_credits` 后 balance<50 | `tenant_credits.low_balance_notified_at` · 24h 去重 |
| `send_employee_invitation_email` | `/api/team/employees` 成功后 | 无 |

任何邮件发送 **必须** 包裹 try/except,失败仅记 warning,不阻塞主流程。

### admin 后台

- 仅 zh / th 双语(en/ja 用户登录自动降级 th)
- 原生 alert/confirm/prompt 全部替换为 `_adminDialog` + `_toast`(textarea 支持驳回原因)

### 前端铁律(切语言)

- 任何用 `t()` 动态生成 innerHTML 的 IIFE 必须 `subscribeI18n('模块名', _rerenderAll)`
- 已注册模块:topup-v2、usage-history、company-selector、balance-alerts、dashboard 等

---

## ✅ 2026-05-19 完成清单(Task 1-6 · 按量付费系统加固)

> **接力规则**:本段为最新窗口产出,旧段保留作历史

### Task 1 · 语言切换(home.js + admin.js)
- topup IIFE 接入 `subscribeI18n`(切语言 · modal 开着时同步重渲文字)
- usage-history 接入 `subscribeI18n`
- admin `labelMap` 移除 en/ja 项 · 默认与回落统一 `th`

### Task 2 · admin 弹窗(static/admin/admin.js)
- `_adminDialog` 支持 `type:'textarea'`(rows / Ctrl+Enter 提交)+ `danger` 红色按钮
- 驳回充值改用 textarea + 必填 + 红色按钮 + 详尽 placeholder
- 验证:`alert/confirm/prompt` 调用数 = 0

### Task 3 · 多公司(db.py + app.py + auth.py + home.js)
- DB:`users.active_tenant_id UUID`(ON DELETE SET NULL)
- API:`GET /api/my-companies` · `POST /api/switch-company`
- auth.py:`get_current_user_from_request` 内自动用 active 覆盖 tenant_id
- 前端:`_initCompanySwitcher` IIFE · 单公司静默 · 多公司全屏卡片选择 · 顶栏 brand 下拉切换

### Task 4 · 余额预警(home.js)
- `_initBalanceAlerts` IIFE · 顶栏正下方插预警条:
  - 余额=0 → 红色 · `zero-balance-msg`
  - 余额<50 → 黄色 · `low-balance-msg`
  - 本月 ≥190 张 → 蓝色 · `near-tier-msg` 带页数
- 新用户引导:owner + 余额=0 + 无历史 + 首次登录 → 卡片 · `localStorage.pearnly_onboarding_seen_<uid>`
- 豁免账号 / 员工 / 已有历史 → 跳过

### Task 5 · 邮件(app.py)
- `send_topup_approved_email(tenant_id, amount, new_balance)` → owner
- `send_low_balance_email(tenant_id, balance)` → 24h 防骚扰
- `send_employee_invitation_email(email, password)` → 新员工
- `tenant_credits.low_balance_notified_at TIMESTAMPTZ`(已 ADD COLUMN IF NOT EXISTS)
- 全部 try/except 包裹 · 失败仅日志 · 主流程不阻塞

### Task 6 · 加固
- **时区**:`_bkk_year_month()` 助手 + `_BKK_TZ` 全局,替换两处 `_datetime.now().strftime("%Y-%m")` + app.py `/api/me/credits` 的 `_dt.date.today()`
- **并发**:`deduct_company_credits` 第 8900 行 `SELECT … FOR UPDATE` 验证存在
- **移动端**:`<meta viewport>` 已在 home.html L5;`home.css` 内 `@media` 数 = 84 处
- **STATE_PEARNLY.md** 本段更新(下面老段保留)

---

## 🆕 2026-05-16(深夜) 本窗口完成清单(v118.32.5.5.30 · UI精修)

> 历史段 · 保留作 changelog

### 对账 UI 视觉精修(home.html / home.css / home.js · cache bust 11841123)

| 项 | 修法 |
|---|---|
| GL 折叠头背景 | `#f4f4f0` → `#ffffff` · hover `#ebebea`→`#F9FAFB` |
| VAT 折叠头背景 | `#fafaf8` → `#ffffff` · hover `#f4f4f0`→`#F9FAFB` |
| 搜索框背景 | `var(--bg)` → `#ffffff` |
| GL "导出 Excel" | 差异明细头部 → **对账汇总头部** |
| VAT 下载按钮 | 独立蓝色 bar → **对账汇总头部** ghost 风 · 文案同步 |
| VAT 折叠防误触 | click代理加 button/a 判断 · 按钮不触发折叠 |
| 去除 vex-dl-bar | 已删除 · 无 DOM 残留 |

### 待下窗口
- 🔴 **Excel 差异明细 Sheet 表头美化**(ws1 · `gl_vat_reconciler.py`) ← 下窗口第一优先
- 🟡 验证 Excel 对账汇总格式(ws2 · WHITE_FILL/SECT_FONT 已部署 · 待用户重跑验证)

---

## 🆕 2026-05-16(深深夜) 本窗口完成清单(接 v5.5.28 · 多项修复)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### 🔴 P0 Bug 修复 · 客户 Korn 对账数据错误(已验证数字正确)

| 文件 | Bug | 修法 |
|---|---|---|
| `vat_report_parser.py` | `_to_float()` 遇到 `(500.00)` 括号负数抛异常 → 整行 VAT 记录被跳过 | 加括号负数解析:`(500.00)` → `-500.0` |
| `gl_vat_reconciler.py` | GL 2列格式 + 无期初余额时 · ลดหนี้/รับคืน(退货)行被默认归 Credit · 导致 GL 合计多算 2000 | 加 `_DEBIT_LINE_KW` frozenset + `_is_debit_line()` · 关键词优先判断 → 退货 = Debit |

**Korn 验证结果**:`ตัวเลขแสดงถูกหมดแล้ว` ✅ (数字全部正确)

### UI 修复(home.js + home.html + home.css)

| 项 | 修法 |
|---|---|
| GL `#1A3C5E` 深蓝色残留 5 处 | 全替换为 `var(--ink)` / `var(--bg)` / `var(--line)` |
| GL 对账结果区在卡片外 | `glv-result` 移入 `vex-main-action` 内(同 VAT 面板结构) |
| GL 对账跑完后汇总/明细不自动展开 | 加 `_expandResults()` helper · 在 `_run()` 和 `_loadTask()` 结束时调用 |
| VAT 对账汇总行显示 UUID hash | 删 `subEl.textContent = '#' + last.task_id` |
| 差异明细行数徽章右对齐跑偏 | `.recon-collapse-sub` 改为 pill badge 样式(同 `glv-section-count`) |
| 历史表下载按钮 tooltip 显示"操作" | 改为 `t('hist_export')` → 显示"导出" |
| GL 折叠头 hover 显示蓝色 `#F1F5F9` | 改为 `#ebebea` |

### CSS 视觉层次(参考上传识别页面)

| 元素 | 之前 | 之后 |
|---|---|---|
| `vex-main-action`（主操作卡片）| `#f4f4f0`（同页面）| `#ffffff`（白卡片）|
| `vex-drop`（上传格子）| `#f4f4f0` | `#f8f8f6`（凹陷感）|
| `vex-kpi-card`（KPI 卡片）| `#F9FAFB` | `#ffffff` |
| `vex-task-section`（VAT 历史区）| 无背景 | 白卡片 + 圆角边框 |
| `.glv-history`（GL 历史区）| 无背景 | 白卡片 + 圆角边框 |

### Excel 汇总 Sheet 格式(gl_vat_reconciler.py · ws2)

| 项 | 修法 |
|---|---|
| 分区标题行有黄色底色 | 加 `WHITE_FILL = PatternFill("solid", fgColor="FFFFFF")` 显式覆盖 |
| 分区标题行显示小计金额(与明细行重复) | `b_val = "" if not emphasize else amount` · 标题行 B 列留空 |
| 分区标题行字体与明细行相同 | 加 `SECT_FONT = Font(bold=True, size=10)` 粗体 |

⚠️ **注意**:Excel格式修复刚刚部署 · 用户在本窗口测试时用的是旧版(有问题)。下窗口需先验证。

---

## 🆕 2026-05-16(深夜) 本窗口完成清单(v118.32.5.5.26 → v118.32.5.5.28 · 共 3 个微版本)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### VAT 预览面板数据接通 + UI 清理

| 版本 | 内容 |
|---|---|
| **v118.32.5.5.26** | **P0 完成**:销项税对账跑完后自动拉 `/api/vat_excel/tasks/{id}` JSON · 填充 `vex-summary-collapse`(5 KPI:总量/匹配/差异/现金/差异金额) + `vex-detail-collapse`(全量差异行 · 可滚动 · 无截断); `_fetchAndFillVexPreview` 异步函数 · 跨 IIFE 靠 `window._fillVexSummary/Detail` 全局桥; `app.py` release_notes 4 语更新 |
| **v118.32.5.5.27** | **屎山清理**:砍掉"对账完成"绿色完成横幅(`vex-result` div + MutationObserver `_watchVexResult` + 4 语 i18n key + CSS `.vex-result`); 下载按钮移至极简 `vex-dl-bar`(仅一个下载按钮 · display flex); cache bust 11841111→11841112 |
| **v118.32.5.5.28** | **UI 蓝色/颜色/顺序三项修正**:`.vex-pp-guide` `#DBEAFE`→`var(--line-soft)` 蓝底清除; 预览面板边框 `#E5E7EB`→`var(--line)` 统一暖灰; `.vex-action-info.ok` 颜色→`var(--success)` 绿; GL 对账面板"对账汇总"与"差异明细"互换顺序(汇总在前); cache bust 11841112→11841113 |

### 待下窗口继续
- 🟡 GL 收入对账预览面板数据填充(同 VAT 套路 · 接 `/api/recon/gl-vat/tasks/{id}` JSON · 当前骨架空)
- 🟡 GL 对账 i18n 完整性 lint(`scripts/check_i18n.py`)

---

## 🆕 2026-05-16(晚) 本窗口完成清单(v118.32.5.5.16 → v118.32.5.5.25 · 共 10 个微版本)

> **接力规则**:换窗口先看本段 · 老段保留在下面

### NAV-IA Gap 补全 + 新铁律 + 基础设施加固

| 版本 | 内容 |
|---|---|
| **v118.32.5.5.16** | **视觉大清扫**:7 处硬编码蓝色(`.rh-stat-dot` / `.client-card` / `.billing-card` / spinner / `.ob-deco` / `.sv-batch-count strong` / `.glv-history-actions`)→ `var(--accent)` / 纯黑 / 暖灰; **首页 dashboard**:4 KPI 卡 + 快速操作 + 最近动态(复用 `/api/me/plan` + `/api/ocr/history`) |
| **v118.32.5.5.17** | **版本更新弹窗**:新文件 `static/version-banner.js`(独立 IIFE · 30s 轮询 `/api/version` · 顶部条 + modal + 4 语 + 30min snooze); `/api/version` 加 `release_notes` 4 语字段; CLAUDE.md 铁律 #6:每次部署写 4 语 release_notes |
| **v118.32.5.5.18** | **部署 graceful 三层**:systemd `TimeoutStopSec=35` + `KillSignal=SIGTERM`; uvicorn `--timeout-graceful-shutdown 30`; lifespan 加 `_recover_interrupted_tasks()`(扫 `status=running` 老任务 → 标 `interrupted`) |
| **v118.32.5.5.19** | **对账对称化**:销项税核查加 `vex-summary-collapse`(4 KPI 卡) + `vex-detail-collapse`(逐条差异表); 收入对账加 `glv-preview-panel`(vex-pp-grid 两栏 · 文件名/大小/路径) |
| **v118.32.5.5.20** | **批量删**:后端 `recon_routes.py` 加 `/api/recon/gl-vat/tasks/batch_delete` · `db.py` 加 `delete_gl_vat_tasks_batch()`; 前端两个对账历史表加 checkbox 列 + 顶部批量删按钮 |
| **v118.32.5.5.21** | **弹窗文案 + reload bug 修**:点"立即更新"前先写 `LS_LAST_SEEN = 最新版本`，防 reload 后弹窗复现; banner 文案 4 语标准化 |
| **v118.32.5.5.22** | **Gmail thead 切换栏**:选中行后 thead 切换成 batch 模式行(内联 · 不另建 div);修表头列宽错位(nth-child → nth-last-child · 操作列固定 110px) |
| **v118.32.5.5.23** | 收入对账查看清单 UI 骨架:改为 `vex-pp-grid` 两栏 + 上方两上传区域对齐 |
| **v118.32.5.5.24** | **屎山清理**:删老 `pn-version-banner` IIFE(116 行 JS + 86 行 CSS); `vex-pp-grid` 从 `1.5fr 1fr` → `1fr 1fr; gap:60px` 对齐上方上传区 |
| **v118.32.5.5.25** | **查看清单 1:1 复刻**:`_renderGlvPreviewPanel()` 完整实现(搜索框 / 清除全部 / 文件行 × X 删除按钮 / 分页); `_removeFile()` 直接写 `STATE.vatFile/glFile=null` 绕过 `setFile(null)` 早返回; `_reset()` 同步调 panel 刷新 |

### 本窗口新铁律
6. **每次部署写 4 语 release_notes**(v5.5.17 拍板):大白话 · 不含 OCR/Gemini/API/batch 等技术词 · 会计师能看懂"我能用上啥"

### 待下窗口继续(本段已由 v5.5.26-28 解决)
- ✅ ~~销项税核查预览数据填充~~ — v5.5.26 已完成
- ✅ ~~UI 蓝色残留~~ — v5.5.28 已清理

---

## 🆕 2026-05-16 本窗口完成清单(v118.44.1.0 → v118.32.5.5.15 · 共 17 个微版本)

> **接力规则**:换窗口先看本段 · 老 GL 主线段保留在下面

### Admin SPA 用户管理补全(NAV-IA Phase 8 收尾)
| 版本 | 内容 |
|---|---|
| **v118.44.1.0** | 用户详情抽屉(7 section)+ 3 tab(客户/员工/日志)切换 + 升级 modal · 移植自 home.js L20600-L22400(1800 行) |
| **v118.44.1.1** | 封停 / 解封 / 级联删除(双重确认)+ 风控完整版(展开 / 分页 / 详情 modal / 批量封禁) |

**改动**:`static/admin/admin.html` + `admin.js`(+1200 行) + `admin-i18n.js`(zh+th 49→130 key)· admin SPA 0 home.js 依赖 · 后端 13+ API 全在不动。

### GL 收入对账 + 销项税核查多 ERP 兼容
| 版本 | 内容 |
|---|---|
| **v118.32.5.5** | WNF/Express/Mr.ERP 风格 GL PDF 解析(`gl_vat_reconciler._parse_gl_text_lines`):兼容 2/3 列数字 + 无日期延续行 + 余额变化判借贷 |
| **v118.32.5.5.1** | 科目 regex `_ACCT_RE` 放宽 4-5 位→4-7 位(支持 WNF 6 位科目 411000) |
| **v118.32.5.5.2** | filename 500 修(泰文文件名走 RFC 5987 utf-8) + VAT 页眉过滤(`_filter_garbage_rows`) + 4 处 alert→showToast |
| **v118.32.5.5.3** | VAT 过滤加严:doc_no 单 token + ≤30 字符 + 不含表头关键词 |
| **v118.32.5.5.4** | VAT pdf_text 过滤后 < 3 行先试 `_parse_vat_pdf_text_lines` 文字行 regex · 不立即回退 Gemini(省 40 秒) |
| **v118.32.5.5.5** | invoice_no 切粘连尾(`_GLUED_TAIL_RE`):DXOHC25-006**OHANAHAN** → DXOHC25-006 + ref_no 严格化(必须含数字) |
| **v118.32.5.5.6** | z-index 单点修(`.cpw-forgot-overlay` 1000→10000) |
| **v118.32.5.5.7** | **z-index 批量修 13 处**(用户反馈"修一类不修一处")· `.add-emp-overlay/.modal-mask/.modal-overlay/.admin-modal-backdrop/.cmdk-mask` 等全升 10000 |
| **v118.32.5.5.8** | BAKELAB pypdf 抽泰文字符顺序乱 · 税号检测改任意 13 位 fallback(`_extract_seller` + `_extract_buyer`) |
| **v118.32.5.5.9** | `extract_invoice_fields` 加 text_path 快路径(销项税核查 BAKELAB 5 张 24s→11s) · `try_text_extraction(strict=False)` |
| **v118.32.5.5.10** | **Session 1 账号 1 设备**:JWT 加 jti · users 加 `active_jti` · 登录写入 · 校验不等就 401 `auth.session_revoked` |
| **v118.32.5.5.11** | `gl_vat_reconciler` summary 加 4 类调整项明细 list + Sheet 2 缩进展开单据明细(Korn 反馈) |
| **v118.32.5.5.12** | 修 migrate bug · `_ensure_user_profile_columns` 加 `commit=True`(ALTER TABLE 之前未提交导致 active_jti 列没建上) |
| **v118.32.5.5.13** | Session 心跳:15 秒轮询 `/api/me/plan` + window focus / visibilitychange 立即 check · 实时踢人 |
| **v118.32.5.5.14** | Trial 缩水:100 张/月 7 天 → **30 张/月 3 天**(Korn 反薅闸 🅱) |
| **v118.32.5.5.15** | login.html 着陆页 4 真公司名换假名:SINCERE/GreenLeaf/PT Solutions/Café Mae → 咖啡店/面包房/IT 公司/餐厅(4 语 i18n + DOM) |

### 本窗口产生的新铁律(已记 memory · 见 CLAUDE.md)
1. **修一类不修一处** · 修 bug 前 grep 同类 pattern 一次性全修(2026-05-16 v118.32.5.5.7 拍板)
2. **ALTER TABLE 必须 `commit=True`** · `db.get_cursor()` 默认不 commit · DDL 会在 with 块退出时回滚(v118.32.5.5.12 踩坑)
3. **Session 控制走 active_jti 模式** · JWT 加 `jti` claim · 每次登录写 users.active_jti · token.jti != active_jti → 401 `auth.session_revoked`
4. **PLG 反薅闸 5 道**(2026-05-16):trial 30/3 + 1 设备 + 24h 同 IP 3 邮箱 + 24h 同 /24 网段 10 邮箱 + 员工共享老板额度
5. **着陆页禁止真公司名** · 用行业类目假名(咖啡店 / 面包房 / IT 公司 / 餐厅)避免商号冒用风险

### 待用户(Zihao)测试确认
- session 实时踢人(v5.5.13 加心跳后)— 3 设备登录测 · 看 15 秒内被踢
- admin SPA 抽屉 / 3 tab / 4 modal / 风控批量封禁
- z-index 13 处批量修(除"添加员工"已确认)

### 待 Korn 回复
- 「5 人轮流用 1 账号」想堵法:🅰 设备指纹累计 / 🅱 IP 段限流 / 🅲 价格策略 / 不堵(SaaS 通病)
- 多 ERP 真实样本(Express / Mr.ERP / FlowAccount)收集中
- 着陆页假名风格确认

### STATE 老遗留(本窗口未碰 · 下窗口可选)
- 🔴 P0-VAT 6 张文件 10 分钟卡 · `parse_vat_report` 同步阻塞 async · `run_in_executor` 修(0.5 天)
- 🟡 真实国税局 PDF 504 timeout(BAKELAB 33 行)· timeout 60 + 重试 + pdfplumber 优先(0.5 天)
- 🟢 进项管理 UI 壳子 v118.45.0 / Phase 6 v118.40 MVP(3 周)

---

## 🆕 GL 对账主线(2026-05-15 晚 上线 · 客户拍板)

> **核心**:新功能"收入对账"(总账 GL vs 销项税报告) · 与现有"销项税报告核查"(发票 vs VAT 报告)互补
> **触发**:客户桌面"新需求"文件夹 · 新需求.md + Thai/中双语规则 · 2026-05-15 PM 立项 → 同日晚上线

| 子模块 | 状态 |
|---|---|
| `gl_vat_reconciler.py` 核心引擎(pdfplumber + 文字行 regex + 对账 + 4 语 Excel 导出) | ✅ v118.32.5.0 |
| `recon_routes.py` 4 个 API 路由(run/tasks/{id}/{id}/export) | ✅ |
| `db.py` `gl_vat_task` 表 + 5 个 CRUD | ✅ |
| 前端:对账中心新加"收入对账" Tab + 折叠区 + 历史表 + i18n × 4 语 | ✅ |
| **销项税性能修复** · `classify_file(fast_mode_invoice=True)` 跳冗余 Gemini classify(节省 25-30s/10 张) | ✅ v118.32.5.3 |
| Excel 导出升级:5 KPI 顶行 + 状态列 + 4 语使用说明 Sheet(借鉴 vat_recon 模板) | ✅ v118.32.5.4 |
| 客户拍板重命名:`销项税对账→销项税报告核查`(zh) / `GL对账→收入对账`(zh) / Thai 4 语同步 | ✅ |

**性能基线**:GL 对账(2 文字 PDF · 252 行)~2 秒;销项税核查(5 张发票 + 1 VAT)~40 秒(原 3 分钟)。

**已知细节**:
- 匹配键 VAT.`เลขที่เอกสารอ้างอิง` ↔ GL.`ใบสำคัญ`(不是 invoice_no)
- 正数 → GL Credit · 负数 → GL Debit 转负
- 收入科目默认 4xxx 开头(UI 可改前缀)
- 生产服 venv 新装 `pdfplumber 0.11.9`

详见 `HANDOVER_TO_NEXT_WINDOW.md`(2026-05-15 晚版本)。

---

## 🧭 NAV-IA 平行主线(2026-05-15 收官 · 8 Phase 全部完成)

> **PRD 主文件**:`NAV_IA_PRD.md`(IA 重构唯一 spec)
> **Phase 6 子 PRD**:`MODULE_EXPENSE_PRD_v2.md`(进项管理模块 · 对标 Paypers · 3 周)
> **基准实物**:`D:\Users\Skin\Desktop\pearnly_project\pearnly_nav_prototype_final.html`(切视角看效果)
> **CLAUDE.md 铁律段**:已加「🧭 导航 IA 铁律」节
> **触发**:2026-05-13 Zihao 提"产品凌乱不堪 · 找不到头" → 2026-05-15 拍板

### 当前状态: **NAV-IA 主线收官 · Phase 1-8 全部 ✅ · 等 Zihao 拍板下一主线**

| Phase | 内容 | 工时 | 状态 |
|---|---|---|---|
| 0 | 文档体系建立 | 0.5 d | ✅ **2026-05-15** |
| 1 | **顶栏三件套**:头像菜单 + 搜索框 + Cmd+K 命令面板 | 1.5 d | ✅ **2026-05-15** · v118.33.1.0 |
| 2 | sidebar 重复入口清扫 | 0.5 d | ✅ **2026-05-15** · v118.33.2.0 |
| 3 | sidebar 集成一级入口 + 后撤销 CTA(prototype 没有) | 0.5 d | ✅ **2026-05-15** · v118.33.3.0 |
| 4 | "即将" badge 大清扫(5 个) | 0.5 d | ✅ **2026-05-15** · v118.33.4.0 |
| 5 | sidebar 业务流分组(销项▾/进项▾) | 1 d | ✅ **2026-05-15** · v118.33.5.0 |
| 6 | 进项管理完整模块(新功能) | 3-5 d | 🚫 **永久跳过** · 等独立开 v118.40 MVP · 子 PRD:`MODULE_EXPENSE_PRD_v2.md` |
| 7 | **集成模块独立化** | 1 d | ✅ **2026-05-15** · v118.33.7.0 |
| **视觉皮肤对齐** | 11 轮微迭代 · 蓝→黑 / 浅蓝→暖灰 / 顶栏 48 / 字号 13 / 一刀切替换 50+ 处浅蓝硬编码 | ~1 d 累计 | ✅ **2026-05-15** · v118.33.7.1 → v7.11 |
| 8 | **Admin Layout 独立**(Earn 专属 · 仅 2 项 sub-nav · admin SPA 不引 home.js) | 1 d + 6 hotfix | ✅ **2026-05-15** · v118.44.0 → v118.44.0.7(8 个微版本) |

### 🆕 Phase 8 实施详情(本窗口 2026-05-15 · 8 个微版本)

| 版本 | 干啥 |
|---|---|
| v118.44.0 | 首部署 · 新建 admin.html/css/js 三件套 + app.py 加 `/admin/{rest:path}` 路由 + login.html 超管跳 /admin/cost |
| v118.44.0.1 | 老 `/admin` 改 301 重定向到 `/admin/cost`(解决浏览器 cache 卡老 home.html) |
| v118.44.0.2 | 修文字隐形(home.js applyLang 抛错残留 `.lang-switching` class)+ admin.js 持续轮询业务函数 |
| v118.44.0.3 | login.html 超管直跳 `/admin/cost` 跳过 `/home` 中转 · `/` `/login` no-cache · 卡顿 3s → 1s |
| v118.44.0.4 | 删「返回普通视图」按钮(死循环) + 修语言下拉关闭 bug |
| v118.44.0.5 | home.js L13585 顶层 try-catch + admin.js 自己 fetch admin 业务 API |
| v118.44.0.6 | 诊断面板改累积日志 |
| **v118.44.0.7** | **彻底独立救援版** · admin.html 拔掉 home.js + 新建 `admin-i18n.js`(zh+th 49 key)+ 5 个按钮 listener + 修 Google 余额 endpoint(`/api/admin/billing/balance`)+ 删诊断 chip |

### 🎯 Phase 8 文件清单(给下窗口接力用)

**新建 4 个文件 · admin SPA 完全独立**:
- `static/admin/admin.html` (~20 KB · sidebar 2 项 + topbar + page-admin-cost + page-admin-users DOM)
- `static/admin/admin.css` (~9 KB · 复用 home.css token + admin 专属变体)
- `static/admin/admin.js` (~23 KB · 鉴权 + 路由 + UI + 业务 fetch 全自包含)
- `static/admin/admin-i18n.js` (~7 KB · zh + th 49 key · 不写 en/ja 按铁律)

**改 home.js 关键位置**:
- L9851 admin-layout 早退分支(已废 · 因为 admin.html 不再引 home.js)
- L9890 `_isAdminPath` 加 `startsWith('/admin/')`
- L11598 `renderFileList` 加 `if (!list) return` 防御
- L13585 + L13590 顶层 `applyLang/routeTo` 包 try-catch
- L29911 / L30029 跳 `/admin/cost`
- 4 个语言块加 6 个 `adm-*` key(zh/en/th/ja 全)

**改 app.py 2 个 route**:
- 老 `/admin` 改 301 重定向到 `/admin/cost`
- 新加 `/admin/{rest:path}` 服务 admin.html
- `/` `/login` 加 no-cache headers

**改 login.html**:超管登录跳 `/admin/cost`(已登录用户重访同上)

### 🚨 Phase 8 关键经验教训(给下窗口看)

1. **home.js 30k 行屎山 + 248 处 `.classList.`**:在缺 DOM 上下文下任何一个 null 就抛错 · setInterval/subscribeI18n 持续触发让浏览器交互失效。**任何新独立模块不要再 `<script src="/static/home.js">`** · 重做的 admin SPA 拔掉它后立刻清净。
2. **i18n 区域分级铁律生效**:admin-i18n.js 只内嵌 zh + th 49 key(adm-* 内部页豁免 en/ja)
3. **app.py 后端 API 零改动**(只加静态 route)· 严格遵守"不改后端 API"铁律 ✓
4. **优化选项 2(拆 home.js)立项 TECH_DEBT.md P1** · 渐进翻新 4 阶段路线 · 不闭眼开干 · 等专门窗口

### 4 类账号矩阵(铁律 · 详见 NAV_IA_PRD §2)
- **员工** = 看不到付费 / 测试 / 管理员
- **老板** = 看付费 · 看不到测试 / 管理员
- **skin** = 老板 + 测试中心
- **Earn** = **走独立 /admin/cost layout** · 不进 home.html · sub-nav 仅 2 项

### Earn 铁律精确化(2026-05-15 Zihao 拍板)
**Earn 不工作 · 只管账户 + 看成本** · admin layout 只 2 个 sub-nav:成本追踪 + 用户管理
**已砍**:平台概览 / 操作日志 / API 健康度

### 与 P0-VAT 主线协调
- NAV-IA 已收官 · 后续接力直接做 P0-VAT 剩余尾巴 或 Phase 6 进项管理 v118.40
- 接力机制:窗口开"继续"先看 P0-VAT 是否有阻塞 · 或挑 Phase 6/P0-VAT 推

### 4 类账号矩阵(铁律 · 详见 NAV_IA_PRD §2)
- **员工** = 看不到付费 / 测试 / 管理员
- **老板** = 看付费 · 看不到测试 / 管理员
- **skin** = 老板 + 测试中心
- **Earn** = **走独立 /admin layout** · 不进 home.html · **sub-nav 仅 2 项**(成本追踪 + 用户管理)

### Earn 铁律精确化(2026-05-15 Zihao 拍板)
**Earn 不工作 · 只管账户 + 看成本** · admin layout 只 2 个 sub-nav:
1. 成本追踪(`admin-cost` · 不动)
2. 用户管理(`admin-users` · 不动)

砍掉的(原 PRD 写了但 Earn 不需要):
- ❌ 平台概览
- ❌ 操作日志
- ❌ API 健康度

### 与 P0-VAT 主线协调
- NAV-IA 改前端 · P0-VAT 改后端 + 对账核心 · **同窗口可并行**
- 优先级:P0-VAT > NAV-IA · 但 NAV-IA 可挤 P0-VAT 等待时间(用户测试期/真实数据等)
- 接力机制:任何窗口开"继续"先看 P0-VAT 是否有阻塞 · 无阻塞 + 有空 → 挑 NAV-IA Phase 接力

---
> **当前线上(已 ssh 核实)**:**v118.44.0.7**(NAV-IA Phase 1-8 全部完成 · Earn admin SPA 独立)· `/api/version`=`11841085` · `systemctl is-active mrpilot` = active
>
> **🔥 本窗口决策(2026-05-14)**:**MR.ERP 项目搁置 → 全删源码(~5600 行)** · 等客户部署 `pearnly_bridge.php` API 后再接回
>
> **本窗口完成清单**:
>   - ✅ **v27.8.1.17.2** · P0-1 / P1-3 / P1-4 / P1-6 / P1-7 / P1-8 / P2-10 / P2-11 共 8 项前端修缮
>   - ✅ **v27.8.1.17.3** · P0-2 已推送标记 + 重复推送二次确认
>   - ✅ **v27.8.1.18** · P1-5 商品映射 tab + P2-9 全部跳过按钮
>   - ❌ ~~v18 智能归属(buyer_name → client 学习)~~ · 半完成已撤销
>   - ❌ ~~v27.8.1.19-debug(Bug #4 排查接口)~~ · 已撤销
>   - ✅ **v27.8.1.19-no-mrerp** · MR.ERP 代码全删(~5600 行)
>   - ✅ **v27.8.1.19-fix** · 修智能引号 JS 语法错误
>
> **下一步候选**:
>   - 🔥 **P0** · 等客户 bridge API · 收到 URL + KEY + schema 后接入 `pushHistoryToErp()` 空壳(0.5-1 天)
>   - P1 OCR速度优化(parse_vat_report 同步函数阻塞 async 根因 · 用run_in_executor修 · 约0.5天)
>   - P2 银行对账(等客户需求)
>   - 🚫 浏览器扩展(Zihao 拍板:不开展)
>
> **主线**:LINE 登录 ✅ → 用户管理 ✅ → 客户分配 ✅ → ERP 适配器 ✅ → **MR.ERP 整链路推完** ✅ → **MR.ERP 改善 11 项** ✅ → ⏸️ **MR.ERP 全删搁置(等 bridge API)** → P0-VAT 已完成 → P1 OCR 速度 / P2 银行对账 / Bridge API 接入
> **重要文档**:`HANDOVER_TO_NEXT_WINDOW.md`(本窗口完整交接 · 必读)· `MODULE_SALE_VAT_RECON_PRD.md`(P0-VAT 需求权威 · 已完结)

---

## ⚠️ 战略铁律 · 头号(2026-05-09)

**自动化 ERP 适配器主线升 P0** · 所有后续窗口必须以 ERP 工作优先 · 其他全部排后:
- ⏸️ 银行对账 v118.26.3/.4 暂停
- ⏸️ 用户管理深化 v118.29.x 推后
- ⏸️ 老板看板 v118.30.x 等 ERP 闭环后做
- ✅ Git 私库 + 公测可与 v118.27 并行

理由:OCR 推 ERP 才是 Pearnly 核心商业闭环 · 没这条线 · 银行对账 / 用户管理只是辅助。

---

## 一句话定位

Pearnly = **4 语言 SaaS（中 / 英 / 泰 / 日）** · 会计事务所 + SME 老板的 AP 自动化 SaaS · 4 语都是真产品语言 · **当前 GTM 首发 = 泰国市场** · 强项是多语言 OCR(泰中日)+ 全管道自动化(LINE / 邮件 / 文件夹)+ **ERP 中立中间件(任何 ERP 都能推 · API 直推 / xlsx 兜底 / 浏览器扩展全自动)** + 一页多发票拆分。

**「不让用户换 ERP · 让 Pearnly 适配所有 ERP」** = Pearnly 区别于 FlowAccount / PEAK 单兵作战的核心定位。

> 🌐 4 语铁律：每个功能必须 th / en / zh / ja 4 语完整 · 不许"先做泰文剩下再说" · i18n 字典顺序 th → en → zh → ja（开发优先级·非重要性）· 详见 CLAUDE.md 顶部铁律

---

## 线上版本

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com(Cloudflare DNS only · 自建 SSL · 已稳)|
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · Ubuntu 24.04 · `/opt/mrpilot/` |
| 数据库 | Supabase PostgreSQL `aydjsgmirjpkjaqknmlg` · AWS ap-southeast-1 · service_role |
| 部署 | `bash /opt/mrpilot/deploy.sh /tmp/<tar.gz>` |
| 邮件 | Gmail SMTP · 发件人 `Pearnly <hello@pearnly.com>` |
| LINE Bot | Greeting message **ON** · 加好友自动推 4 语欢迎 + 6 位代码绑定引导 |
| LINE Login | Channel ID `2010022630` · Email scope **Applied** ✅ |
| env(关键)| `PEARNLY_PUBLIC_URL=https://pearnly.com` `LINE_LOGIN_CHANNEL_ID=2010022630` |
| 联系 | hello@pearnly.com / +66 86-889-2228 / LINE @059oupmg |

**当前 cache bust**:`home.css?v=11841085` · `home.js?v=11841085`(v118.44.0.7 · NAV-IA Phase 1-8 全部完成 · 2026-05-15 线上)
**下版本 cache bust**:`11841086`
**下版本 cache bust**:`11841079`

---

## 🔑 账号分工(铁律)

| 账号 | 用途 | 备注 |
|---|---|---|
| **skin306152@gmail.com (Google OAuth)** | 🧪 功能测试账号 + 测试中心白名单 + ERP dev seed 白名单 | `user_id=468b50c1-5593-4fd6-990d-515ce8085563` `tenant_id=040f012b-a456-49b3-a8f4-f83901bec9ea` |
| **Earn** | 👑 超管账号 | 永远只看 /admin · 不跑系统业务 · 仅平台管理 |
| mrerp@outlook.co.th | yearly · 1500 配额 · **绝对不许碰** | 真实付费用户 |

**铁律**:测产品功能 → skin OAuth · 测平台管理 → Earn /admin · 绝对不许碰 mrerp

---

## 🔌 MR.ERP 项目状态(2026-05-14 全删 · 等 bridge API)

**Zihao 拍板**：暂停 HTML 爬取方案 → 等客户部署 `pearnly_bridge.php` 提供 JSON API。

**项目内 MR.ERP 代码**：✅ 全删（app.py / db.py / home.js / home.html 共约 5600 行）

**给客户的 Bridge 文件**：`D:\Users\Skin\Desktop\pearnly_project\mrerp_bridge\`
- `pearnly_bridge.php`(单文件 · 191 行 · 提供 ping/products/customers/schema 接口)
- `INSTALL.txt`(3 步安装说明)

**客户装好后 Zihao 提供**：① ERP 网址 ② API 密钥 ③ schema 接口截图

**接入位置**：home.js `pushHistoryToErp()` 空壳 + 后端新建 bridge_client 模块

**保留的 MR.ERP 测试信息（备用）**：

| 项 | 值 |
|---|---|
| 域名 | `mrerp4sme.com`(已知) |
| 测试账号 | Username: `test01` |
| 测试公司 | `1010-01-000006` |
| 测试数据库 | `TEST2019`(`?comidyear=6&seldb=1`) |

---

## 🔥🔥 P0-VAT v118.32.3.x → v118.32.4.x 真实进展(2026-05-12 外部窗口核实)

> **背景**:上窗口意外关闭 + 文档没来得及更新 · 本窗口 ssh 服务器核实真实状态 · 文档曾误标 v3.9 待部署 · 实际已推到 v4.7 在线
> **核实方式**:服务器 `/opt/mrpilot/static/home.html` 的 cache bust + `/api/version` + 服务器代码版本注释 grep

**v3.0 → v3.9(全部已上线)** —— 上上窗口 BCDEF 优化 · 详情见旧 HANDOVER

**v3.10 → v4.7(已上线 · 上窗口意外关闭前推完 8 版 · 中间细节缺失)**:

| 版本 | 推断内容(代码注释 grep)| 状态 |
|---|---|---|
| v4.0 | C 进度反馈业务化 5 阶段步骤 | ✅ 在线 |
| v4.1 | 失败明细 + 业务错误码 4 语 + 失败 task 关联客户名 | ✅ 在线 |
| v4.2 | 微调(无注释痕迹) | ✅ 在线 |
| v4.3 | 金额格式化含币种 + 概览卡可见性控制 | ✅ 在线 |
| v4.4 | 无注释痕迹 | ✅ 在线 |
| v4.5 | 无注释痕迹 | ✅ 在线 |
| v4.6 | 无注释痕迹 | ✅ 在线 |
| v4.7 | done 状态防被轮询响应覆盖 | ✅ 在线 |

**v4.8(本窗口推上线 · 2026-05-12)**:

| 文件 | 改动 | 业务影响 |
|---|---|---|
| `vat_report_parser.py` | Gemini prompt 加 5 条严格规则 + self-check | OCR 不许自作主张改人名/税号/金额 · self-check 验证 pre_vat + vat ≈ total |
| `recon_routes.py` | RowActionBody 加 `source` 字段(invoice/report) | 行级操作记录用户采纳哪边为准 · 拼进 notes 不改 db schema |
| `home.js` "B 方案" | accepted_diff 视觉等同 matched(绿勾 + 已核对徽章)+ 2 个大按钮 + 新 action 映射(accept-invoice / accept-report / undo) | 金额对不上的行用户校对兜底 · 选完即视为对得上 |
| `home.html` / `home.css` | cache bust 11832470 → 11832480 + 配套样式 | - |

**部署核实**:`/api/version` = `{"version":"11832480"}` ✅ · `systemctl is-active mrpilot` = active

**⚠️ deploy.sh 坑**:`sleep 3` 不够(uvicorn 启动实际 7 秒)· 部署完瞬间 nginx 502 · 等几秒自动恢复 · 下次顺手把 sleep 改 10s

**🔴 P0 遗留(v4.8 没碰)**:6 张文件批量识别仍卡 10 分钟 · 嫌疑根因 `parse_vat_report` 同步函数阻塞 async 事件循环 · 推荐 hotfix 包 `run_in_executor`

**剩余 BCDEF 阶段**:D 后台异步 + LINE/邮件通知(v118.32.5)→ E OCR prompt 升级深化(v118.32.6 · v4.8 已偷跑 prompt 严格规则部分)

---

## 🔥🔥 v118.32.4.9 核对表重构 · 主线推翻(2026-05-12 Zihao 拍板)

> **触发**:Zihao 用 19 张 BAKELAB 发票 + 1 张销项税报告测试 v4.8 · 结果 1✓ 16⚠ 严重对不上 · 截图 + PDF 核对要求(`异常\ขั้นตอนการตรวจรายงานภาษีขาย.pdf`)发回
> **核心认知改变**:Pearnly = **核对表生成器**(不是匹配判定器)· 准确率 100% 定义 = **OCR 抽出来的字段跟原文 100% 一致**(不是匹配率 100%)

### 核对要求(来源 · Zihao 给的会计师标准 PDF)

**必识别 7 项 = PDF 编号 3-9**:
| # | 字段 | 备注 |
|---|---|---|
| 3 | 日期 | 必 |
| 4 | 发票号 | 必 |
| 5 | 客户名 | 必 |
| 6 | 买方税号 | 必 |
| 7 | 买方分公司 | 必(个人买家除外 · PDF 明文) |
| 8 | 净额(VAT 前) | 必 |
| 9 | VAT 金额 | 必 |

**辅助检查**:PDF 第 1 项"是否有 ใบกำกับภาษี 字样" + 第 2 项卖方 4 子项一致性(同一份报告应同一个卖方)

### 三个微版本拆分

**v118.32.4.9 核对表重构**(1.5 天):
- 后端 reconciliation_matcher.py 改"逐字段对照"模式 · 不归一化 · 如实展示两边
- 数据结构每行 7 字段 × 报告/发票两侧 + 一致 bool + 差异类型枚举
- 前端对账中心改对照表 UI(参考 PDF 底部表格布局)
- 每行差异提供 3 个动作:"改报告"/"改发票"/"两边都对是同一笔"
- **UI 顶部加"此次汇总"区**(Zihao 强调):
  - 总行数:N
  - 完全一致:X 行
  - 数据差异:Y 行(细分 · 发票号差/客户名差/金额差/...)
  - 🔴 OCR 没识别完整:Z 行
  - 散客无发票(正常):M 行
- 4 语 i18n × 全部新词条

**v118.32.4.10 7 项 OCR 准确率底线**(1 天):
- vat_report_parser.py + 发票 OCR 都加:7 项任一缺失 → 那一行红字"OCR 没识别完整"+ 重传按钮
- 后端业务规则校验(独立于对照):
  - 净额 + VAT ≠ 总额 → "金额自相矛盾"
  - VAT ≠ 净额 × 7%(非 0% / 免税)→ "税率异常"
  - 税号不是 13 位 → "税号格式异常"(散客除外)
- 系统标完用户自己决定要不要修

**v118.32.4.11 Excel 导出 + 列表时间戳**(0.5 天):
- 按 PDF 底部表格格式导出 Excel(左右双栏 + 备注 + 三签名位 ผู้จัดทำ/ผู้ตรวจสอบ/ผู้อนุมัติ)
- **Excel 表头 4 语 i18n**(F2 已做基础 · 这次扩到对照表全字段)
- **Excel 顶部加"此次汇总"区**(对应 UI 汇总)
- 近期对账列表加时间戳 + 默认时间倒序 + "清 7 天前任务"按钮

---

## 🧪 v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划(2026-05-13 评估完)

> **背景**:v4.9.5 推上线后 Zihao 用 13 个场景实测 Excel 公式对账新方案 · 仅 skin306152 内测可见
> **结果**:4 全对 + 3 部分对 + 6 个 bug → 公式对账思路成立但实现要重做
> **现状**:已评估完工作量 · 等 Zihao 拍 504 + 拍"开干"

### 13 场景测试结果分布

| 类型 | 数量 | 含义 |
|---|---|---|
| ✅ 全对 | 4 | 发票号匹配 + 7 字段全等 + 金额对得上 |
| 🟡 部分对 | 3 | 发票号匹配但金额或字段有差异(Sheet 3 SUMIF 聚合后信息丢失看不出来) |
| 🔴 错 | 6 | 5 类 bug · 见下 |

### 5 个 bug 拆解(v4.9.6 一锅烩 · 评估 2.5 天)

| # | bug 现象 | 根因 | 修法 | 工时 |
|---|---|---|---|---|
| 1 | Sheet 1/Sheet 2「期间」列空白 | invoice.period AI 没抽 + Sheet 2 拿 period_year/month 没拼出 | build_excel 写入时 period 空 → 从 invoice_date / report_date 降级算 MM/YYYY(BE 转公历) | 0.2 天 |
| 2 | 散客发票(无税号)+ 散客在报告里 → 现在标"发票有报告无"孤儿 | 散客硬走"无税号即孤儿"分支 · 没去报告里查 | 散客改三重匹配 客户名+发票号+金额 · 加 `_match_cash_customer` 辅助 | 0.4 天 |
| 3 | Sheet 3 只对总金额 · 漏发票号差/日期差/期间差/分公司差/客户名差 5 维度 | Sheet 3 按 buyer_tax_id SUMIF 聚合 · 同客户多张发票合一行 · 维度信息丢失 | **Sheet 3 整段重写** · 砍 SUMIF · 改 INDEX/MATCH 按发票号一对一 · 5 维度各占独立列 · 报告侧落单行贴在表底 | 0.8 天 |
| 4 | 税号差 1-2 位直接判孤儿 | 等号严格比 · 无 fuzzy | 加 Levenshtein 编辑距离 ≤ 2 → 标"疑似匹配 · 请确认" · 不替用户判定(符合「我们只核实」铁律) | 0.3 天 |
| 5 | 发票缺税号(OCR 漏抽)→ 现在标孤儿 | 当前只看发票自己的 buyer_tax_id 空 = 散客 | 反向匹配 VAT 报告 · 找到了 → "OCR 漏抽税号 · 实际应为 XXX" · 跟 Bug 2 共享代码 | 0.2 天 |

### UI 美化清单(0.6 天 · 基准模板 `异常/vat_recon_BEAUTIFIED_demo.xlsx`)

| 项 | 实现 |
|---|---|
| Sarabun 字体(泰文优先) | openpyxl Font(name="Sarabun") + Tahoma fallback |
| 金额列千分位 #,##0.00 + 右对齐 | 已有部分基础 · 全字段对齐 |
| 斑马条纹(偶数行 #F9FAFB) | 数据循环里设 PatternFill |
| 表头蓝底白字 + 行高 32 | 蓝底白字已有 · 行高从 24 → 32 |
| 冻结第一行 | 已有 freeze_panes="A2"(保持) |
| Sheet 标签彩色 | ws.sheet_properties.tabColor(发票蓝/报告绿/对账橙/说明灰) |
| Sheet 3 KPI 4 大数字卡片 | 顶部 4 个大单元格 · 字号 18 加粗 + 背景色 + 大行高 |

### 核心改造点 · Sheet 3 推翻重做

- **当前**:按 `buyer_tax_id` 聚合 · 每税号 1 行 · `SUMIF(Sheet1!I)` 算金额合计
- **改后**:按 `invoice_no` 一对一 · 每张发票 1 行 · INDEX/MATCH 按发票号查报告
- **报告侧没匹配上的**:贴表底 ("发票无 · 报告有" · 不让信息丢失)
- **散客特殊处理**:三重匹配 客户名+发票号+金额 · 匹配失败再走 OCR 漏抽提示
- **结果**:用户能在一张表上同时看到 5 维度差异 · 不需要回到 Sheet 1/2 翻原数据

### v4.9.6 决策点(等 Zihao 拍)

🟡 **真实国税局 PDF 504 超时**(33 行 BAKELAB · pdfplumber 抽不到 → Gemini 25s timeout)
- 带:+0.5 天 · timeout 60s + 重试 + pdfplumber 优先 · 总 3.0 天
- 不带:推 v4.9.7 · 用户继续用合成数据测 · 总 2.5 天

### 部署后必测(≤2 项 · Zihao 已确认)

1. 重跑 13 个测试 PDF · 看每个 bug 都标对
2. 下载 Excel · 看格式美化是否到位

### 测试数据资产

- `异常/测试/v4_9_多场景/`(1 报告 + 12 发票)
- `异常/测试/รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行真实国税局 · 504 那张)
- `异常/vat_recon_BEAUTIFIED_demo.xlsx`(美化基准模板)

---

## 🎯 v118.32.4.10 UX 大改造 · 等 v4.9.6 测过开干(3.1 天)

> **触发**:2026-05-13 Zihao 拍板 · 公式对账 v4.9.6 修完后 · UX 从"导出 Excel"升级为"UI 主流程 + Excel 变导出"
> **核心认知**:对账完成 → 进 UI 看大盘 + 详情 · Excel 不再是主出口 · 看齐 DataSnipper 同级 UX

### 改动清单

**改动 1 · 撤销旧模式(0.3 天)**
- 删「标准对账 / Excel 公式对账」toggle 切换器
- 销项税对账模块全平台默认走新流程 · 撤 skin306152 email 白名单
- BETA 标签保留(产品未完全成熟)
- 旧 vat_report_parser.py 等模块代码不动 · 保留向后兼容 · 但 UI 入口隐藏
- 试用账号限额 3 次 · 第 4 次弹"升级解锁无限次"(不是直接拒绝)
- 「近期对账任务」= **当前 tenant 内所有用户**的历史任务(不跨租户)

**改动 2 · UI 汇总页核心(2.3 天)**
- 后端:`/build` 不返 xlsx 改返 JSON + 新建 `vat_recon_results` 表 + 单独 export endpoint(0.8 天)
- 前端主体(1.8 天):
  - 顶部 KPI 4 大卡(行高 100)· 蓝总笔数 / 绿匹配 / 红异常 / 橙异常金额
  - 第二行筛选 + 操作:[全部][匹配][缺一边][金额不一致][待确认] tab + 排序 + 批量 + 📥Excel + 📄PDF
  - 对账明细表 · 列:☐ 状态 税号 客户 发票号 期间 发票金额 报告金额 差异 操作
  - 行颜色:匹配绿底 / 异常红底 / 待确认黄底 / hover 高亮
  - 4 语 i18n × 50+ 词条 + 移动端适配 + 防呆撤销

**改动 3 · Excel 导出按钮(0.2 天)**
- 复用现有 build_excel · 单独 GET endpoint
- 点按钮重新生成(用户改了数据也能拿最新)

### 关键决策(已拍)
- 撤白名单 → 所有 plan 都能用(trial 限 3 次 / monthly+yearly+lifetime+admin 无限)
- 详情抽屉 + PDF 预览推到 v4.11 · v4.10 只做列表 · 点行先不展开详情
- 审计 PDF 导出推到 v4.12 · v4.10 只做 Excel 导出

---

## ❌ v118.32.4.11 详情抽屉 + PDF 溯源 · **永久砍(2026-05-13 Zihao 拍板)**

> v4.11 详情抽屉 / PDF 溯源 · 永久砍(2026-05-13 Zihao 拍板)
> 理由:v4.10.10 已删整套 modal 预览代码 · 改走「Pearnly = 数据提取器 · 用户拿 Excel 自己看」路线
> v4.10.11 加了上传清单预览面板 · 用户感知充分 · 不需要再造任务详情预览
>
> 原计划(留痕 · 勿重启):点行 → 抽屉滑出 · 左半可编辑 · 右半 PDF.js + bbox 高亮 · OCR bbox 三层降级 · 3.0 天
> **下一个版本直接跳 v4.10.12(Excel 质量验收 + 任务列表时间戳 + 清7天)**

---

## ⏸️ v118.32.4.12 暂缓 · 待真实会计师反馈(P3 候选)

> **拍板**:2026-05-13 Zihao 决定 · v4.11 上线后让真实会计师试用 2-3 周再决定要不要做
> **理由**:避免凭空猜需求做错方向

候选内容:
- 审计 PDF 导出(KPI + 异常表 + 异常发票缩略图 + 签字栏 + 4 语)
- 历史对比卡片(同客户跨期"上月 X 张 · 这次 Y 张 · 异常增加 Z")
- 批量操作(选行 · 标已审/驳回 · 全部接受匹配项)

**触发条件**:
- 真实会计师试用 2-3 周
- 反馈表明这些功能确实是高频需求(不是"想要"而是"必需")
- 之后再开 v4.12 · 工时 2.7 天

---

### 推翻的旧方案(留痕 · 别再走回头路)

❌ **v4.9 旧方案 · INV ↔ IV 模糊匹配归一化** —— 替用户做决定 · 违反"我们只核实"哲学
❌ **v4.9 旧方案 · 客户名去 ์ 符号自动算同一人** —— 同上
❌ **匹配率 100% 当成功标准** —— 错位的 KPI · 真正 KPI 是 OCR 字段抽取准确率 100%

---

## 核心模块状态

### ✅ 已上线(线上稳定)

**v118.28 系列(2026-05-08 ~ 05-09 · 17 版)**
- v28.0 客户切换器 + v28.1.0 测试中心
- v28.3 LINE Bot URL · v28.4.x LINE 社交登录
- v28.5.x 顶栏布局 + 移动端 6 BUG
- v29.0 用户管理 UI + 操作日志
- v28.6 超管员工 tab 只读化
- v28.7 + v28.7.1 密码重置链接化
- v28.8 客户老板查 Pearnly 访问日志
- v28.9 改密后旧 JWT 失效
- v28.2 + v28.2.1 超管 /admin URL 独立
- v28.1 客户分配面板

**v118.26 银行对账系列(2026-05-09)**
- v26.0 顶级菜单 + 当月概览
- v26.1.x 批量上传 + 列表筛选
- v26.2.0/.1 右半屏 + 候选 pane + 客户徽章 ✅(测试通过)
- **v26.2.2** OCR P0 紧急修补(quota gate 早返回 · 修 v27.7 fix_orphan tenant=0 死结)✅
- **v26.2.3** admin_upgrade_user 字段修正 + forgot_password 改 SMTP ✅
- **v26.2.4** banned/inactive 安全闸 + 员工 plan 继承 + _require_owner_or_super 懒建 ✅
- **v26.2.5** signup 3 路径同事务建 tenant(根因修复)✅

**前期累计**
- 多语言 OCR(泰中日)· AP 自动化管道 · 4 语 i18n subscribeI18n 总线
- admin 后台 80% 完成度

### 🔥 进行中(主线 · 战略调整后)

**头号 P0 · 自动化 ERP 适配器**(13-17 天):
- ⏳ v118.27.0 客户/科目/税码映射底座(2-3 天)· **下一件**
- ⏳ v118.27.1 MR.ERP 适配器(方案 A · 5-7 天)· 等 4 件物料
- ⏳ v118.27.2 FlowAccount API 直推(2 天)
- ⏳ v118.27.3 PEAK API 直推(2-3 天)· 等 partnership
- ⏳ v118.27.4 Xero + QB API 直推(各 1.5 天)
- ⏳ v118.28.0 Express 适配器(3 天)
- ⏳ v118.28.1 「我的 ERP 是 ___」反馈框(0.5 天)

**P0 公测启动并行**:
- ⏳ A.1 Git 远程私库 push(0.5 天)

**P1 浏览器扩展平台**(公测后):
- ⏳ v118.31 系列 浏览器扩展框架 + MR.ERP web 自动点击(15-18 天)

### ⏸️ 暂停 / 推后

- v118.26.3 银行对账拖拽匹配(1.5 天 · ERP 闭环后)
- v118.26.4 银行 Excel/CSV 解析(0.75 天 · 同上)
- v118.29.x 用户管理深化(3.6 天 · 公测后)
- v118.30.x 老板看板 + 风控告警(L4-L6 · 7-10 天 · ERP 闭环后)

### ❌ 已取消 / 永久砍

- v27.8 全表 RLS(service_role 自动 BYPASS)
- ~~Mr ERP 直推对接(已复活)~~ → v118.27.1 立项
- Facebook 社交登录
- 超管直接重置客户密码(v28.7)
- 老板看到员工临时密码(v28.7)
- **桌面 RPA(D)** + **UI Automation API(E)**(2026-05-09 · v26.2 调研后定砍)
- 用友 T+ 适配(泰国基本无用户)
- Tally 适配(on-premise + API 弱)

### 🚫 阻塞(等外部条件)

- MR.ERP 4 件物料(现金销售真实数据 / 采购 / 会计凭证 / 错误信息)· 等 Zihao 补
- PEAK API 文档 + sandbox · 等 partnership 邮件回
- Express API 文档 · 等商务联络回

---

## 🆕 铁律清单(累计 33 条)

1-22:见 v118.28.1 HANDOVER · 不变

23. **战略调整 · 自动化 ERP 主线升 P0**(2026-05-09)· 银行对账让路 · 所有窗口 ERP 工作优先
24. **ERP 二分法**(2026-05-09)· 有 API → API 直推 / 无 API → A+C · v118.27.0 映射底座是依赖
25. **桌面 RPA(D)+ UI Automation(E)永久砍**(2026-05-09)· 桌面 ERP 走 A 兜底
26. **浏览器扩展平台(C)= Pearnly 平台能力**(2026-05-09)· 不只 MR.ERP · 复用所有 web ERP
27. **MR.ERP `mrerp4sme.com` PHP web 应用 · 厂商 Mr.ERP for SME**(2026-05-09)
28. **MR.ERP 文件格式铁律**(2026-05-09):.xlsx · 3 sheet 命名严格 `Worksheet/Worksheet 1/Worksheet 2`
29. **MR.ERP 字段格式铁律**(2026-05-09):日期字符串 YYYY-MM-DD · 客户代码三段式含泰文 · 税率字符串枚举
30. **MR.ERP 数据库 / 多公司 = 服务器分配**(2026-05-09):URL 参数 · Pearnly 推不需带
31. **MR.ERP 无 API / 无文件夹监听 / 无定时导入**(2026-05-09):全自动只能走方案 C 浏览器扩展
32. **L1-L6 产品价值定位**(2026-05-09):入账 → 学习 → 对账 → 看板 → 合规 → 风控 · 客单价 599 → 3000-5000
33. **公测策略**(2026-05-09):Git 私库后即启动 · ERP 适配器并行 · 公测反馈反推优先级

### 🆘 v118.26.2.2-2.5 紧急修补铁律(34-43)

34. **OCR quota gate 早返回模式**(v118.26.2.2):有效 plan 用户(trial/free/pro/firm/enterprise/monthly/yearly)在 `_check_user_quota` 顶部直接放行 · lifetime 单独看自带 key
35. **tenants 表无 plan / max_seats 字段**(v118.12.1 → v118.26.2.3):任何 `UPDATE tenants` SQL 严禁包含这 2 字段 · 否则整条抛错被 try 吞
36. **forgot_password 邮件用 SMTP 主用**(v118.26.2.3):`_smtp_send_email` from app.py · Resend 作 fallback · 不依赖 RESEND_API_KEY
37. **被禁用 / 未激活账号 OCR 拦截**(v118.26.2.4):`_check_user_quota` 顶部 `is_banned` / `is_active=False` 早返回
38. **员工 plan 继承在 OCR 路径**(v118.26.2.4):`_check_user_quota` 检测 `role=member` 时查 owner.plan
39. **`_require_owner_or_super` 懒建 tenant 兜底**(v118.26.2.4):`tenant_id=NULL` 时自动建
40. **signup 3 路径同事务建 tenant**(v118.26.2.5 根因解):`_ensure_tenant_for_new_user(cur, user_id, plan, ...)` · 用 PLAN_CONFIG 真实 quota
41. **新注册 token 带 tenant_id**(v118.26.2.5):signup 主路径返回的 access_token 立刻带新 tenant_id
42. **大改造后 5 步回归测试铁律**(SOP §7.5 新增):动 users/tenants/plan/role/quota/auth 后 · 部署后跑 5 步验证 · 一步红立刻 hotfix
43. **LINE push API ack 不可靠**(2026-05-09):已有 LINE→Email fallback 是产品权衡 · 不修

---

## 数据资产

| 资产 | 数量 | 用途 |
|---|---|---|
| 银行对账单 PDF | 9 张 | 对账测试 |
| 发票 OCR 异常规则 PDF | 9 张 | OCR 边界测试 |
| skin OAuth 测试数据 | 8 个 TEST_ 客户 / 37 张发票 / 5 条异常 | 功能测试 |
| **MR.ERP 销售-赊销真实样本** | 1 份 .xlsx(2 行数据 · 文件名 mrerp_sample_SC_credit_real.xlsx) | **v27.8.1.0 推送测试 + 适配器开发** |
| **MR.ERP 销售-现金空模板** | 1 份 .xlsx | 同上(待补真实数据 · 当前 sheet 命名错 Sheet1-4 · 应是 Worksheet/Worksheet 1-3 · 不能直接用) |
| **PEARNLY_ERP_RESEARCH_2026_05.md** | 11 家 ERP API 状态调研 | 战略决策档 |
| **PEARNLY_ERP_DEEP_2026_05.md** | 自动化模块深度优化 + L1-L6 | 战略决策档 |

---

## ⭐ 极简模式(新窗口必读)

省 70% Claude 额度 · 4 语红线不破。

### 启动步骤

1. 新窗口第一句话发简化版 `NEW_WINDOW_OPENER.txt`(3 行)
2. 把当前最新 `pearnly_v118_27_8_1_14d.tar.gz` 拖进对话框
3. 模板「我要做的事」一栏写一句话需求
4. **推荐第一个版本:v118.27.8.1.15 批量上传 500 + plan +300 + auto_push 默认开**(P0-A 第一站 · 1 天)
5. **完整路线**:v15→v22(9.5 天)按 BACKLOG.md 顺序推 · 中途不许扩大范围

### 新窗口 Claude 必须遵守

红线 / 业务闭环 / 省钱 / UI ≤ 5 项 / 部署后命令验证 / 测试中心隔离 → 全在 `PEARNLY_WORKFLOW_SOP.md`。

---

## 当前已知小问题

- 🔴 **P0 · v4.9.2 分组 bug 暂停未解**(2026-05-13):用户拖 13 个 v4_9_多场景测试文件 · stats 显示 12 文件 12 发票 0 VAT 报告 → **VAT 报告被识别成 invoice 而非 vat_report** · v4.9.2 加的 "filename 含 รายงาน → 强制 vat_report" 没起作用 · Zihao 拍板暂停修转去做 v4.9.5 内测 · 留给 v4.9.3 / v4.9.6 一起 fix
- 🔴 **v4.9.5 内测 · 真实国税局 PDF 504 超时**(2026-05-13):合成 PDF(12 行 · reportlab)能跑通 · 但真实 BAKELAB 测试文件夹的 `รายงานภาษีขาย 03.69 - 001 033.pdf`(33 行 · 真实国税局格式)Gemini 25 秒超时 · 嫌疑:PDF 是图片化文字层 → pdfplumber 抽不到 → fallback Gemini 但 timeout 太短 · v4.9.6 已规划修(timeout 60 + 重试 + pdfplumber 优先)
- 🟡 **v4.9.5 测试反馈待修(5 bug + UI 美化 · 2.5 天 已评估)**:详见上方"v118.32.4.9.5 内测结果 + v118.32.4.9.6 规划"段 · 等 Zihao 拍 504 + 拍"开干"
- 🔴 **P0 · 6 张文件批量识别卡 10 分钟未根本解决**(v118.32.3.0-3.9 多版未解决 · 下窗口必修)· 嫌疑根因:`parse_vat_report` 同步函数阻塞 async 事件循环 · 详见 `HANDOVER_v118_32_3_9.md`
- 🟡 P1 · F1 金额对齐(`amount_pre_vat`)用户未实测 5/5 BAKELAB 匹配
- 🟡 P1 · F2 Excel 4 语 i18n 表头(中/英/日/泰)用户未实测
- 🟡 P1 · 系统设置改 modal(v3.6-3.9)用户没逐个 tab 测过 · 可能某些 pane 内容布局错乱
- 🟡 P1 · 单据记录列贴右(v3.9 才找到根因 `.card { padding: 20px }`)用户未确认
- 🟢 P2 · `gemini_engine.py` 不在 project knowledge · E 阶段(OCR prompt 升级)前必须 scp 拉到本地
- 🟢 P2 · 测试中心 sidebar badge 当前显示 "24" 异常 · 下窗口让用户截图看具体错误
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码(admin-modal-reset-pw 词条 / showResetPwdResult / `_admin_*_LEGACY`)· 0.2 天 · P3

---

## 公测启动检查清单(只剩 1 项)

| 项 | 状态 |
|---|---|
| LINE 登录 + 补邮箱 modal | ✅ v28.4.x |
| 操作日志 + 分页 + CSV | ✅ v29.0 |
| 超管员工 tab 只读化 | ✅ v28.6 |
| 密码重置链接化 | ✅ v28.7 |
| /reset 落地页 | ✅ v28.7.1 |
| 客户老板查 Pearnly 访问日志 | ✅ v28.8 |
| 改密后旧 token 失效 | ✅ v28.9 |
| 超管 /admin URL 独立 | ✅ v28.2 (+ .1) |
| 客户分配面板 | ✅ v28.1 |
| 银行对账右半屏 | ✅ v118.26.2.1(测试通过) |
| 用户管理/租户连环 BUG 修补 | ✅ v118.26.2.2-2.5(测试通过) |
| **Git 远程私库 push** | ⏳ 0.5 天 |

**做完 Git 私库即启动公测** · ERP 适配器(v118.27.x)并行 · 公测反馈反推 ERP 排序优先级。

---

# 📌 v118.27 系列进度补丁(2026-05-10)

> 本文档主体写于 v118.26.2.5 时代 · v27.x ERP 适配器系列推进至 v27.7.1 · 此章节同步实际进度

## v118.27 系列 ERP 适配器 · 已上线版本(v27.0 → v27.7.1)

| 版本 | 主题 | cache bust | 状态 |
|---|---|---|---|
| v27.0 | 客户/科目/税码映射底座(3 张表 + 6 接口) | - | ✅ |
| v27.0.1 | pearnlyConfirm 全局弹窗 + ERP 映射搬「自动化」+ seed 提速 | - | ✅ |
| v27.1 | MR.ERP xlsx 适配器(stub-first · sales_credit 单张) | - | ✅ |
| v27.4 | Xero OAuth 2.0 适配器 + 推 ACCREC + 错误码 4 语 | - | ✅ |
| v27.4.1 | Xero scope broad → granular | - | ✅ |
| **v27.4.2** | MR.ERP sheet 数动态(customer/product=1 / journal=2 / sales=3 / payment=4) | 11828944 | ✅ |
| **v27.5** | 抽屉 1 推按钮统一 split + 下拉 + `/api/erp/connectors/status` | 11828945 | ✅ |
| **v27.5.1** | hotfix 多发票文件导出只 1 行 BUG · invoices 数组 + 拆 N 行 | 11828946 | ✅ |
| **v27.5.2** | hotfix race condition + SKIN 双闸白名单 | 11828947 | ✅ |
| **v27.5.3** | 「泰国销售明细」导出模板(`excel_template_th.py`) | 11828948 | ✅ |
| **v27.5.4** | 新版本检测横幅 · `/api/version` + 5min 轮询 + no-cache | 11828949 | ✅ |
| **v27.5.5** | hotfix unified IIFE race · placeholder-first | 11828950 | ✅ |
| **v27.6** | 4 模板对齐 · 砍 ERP 录入格式 · 路由分发 | 11828951 | ✅ |
| **v27.6.1** | hotfix 抽屉推送下拉改向上弹出(dropup) | 11828952 | ✅ |
| **v27.7** | 识别中心下拉向上弹 + `/api/ocr/export-by-history-ids` | 11828953 | ✅ |
| **v27.7.1** | hotfix 客户导出 BUG · `db.list_ocr_history` retention_days Optional | 11828954 | ✅ |
| **v27.8.0.4** | MR.ERP 反向工程 + 后端引擎(mrerp_pusher.py + kms_helper.py · 5 步实测全通) | - | ✅ 临时部署 /tmp/v27_8_test |
| **v27.8.1.0** | MR.ERP MVP · mrerp_credentials 表 + 5 db 函数 + 3 endpoints + 凭据 modal | 11828960 | ✅ |
| **v27.8.1.1** | hotfix · setTimeout 600/700ms 自检定时(防 IIFE race) | 11828961 | ✅ |
| **v27.8.1.2** | excel_template_th.py 公式修复(=E*F · 防循环引用) + `_userInfo` 轮询 | 11828962 | ✅ |
| **v27.8.1.3** | 「识别完自动推送」toggle 端到端 · auto_push 字段 + OCR 钩子(2 处) | 11828963 | ✅ |
| **v27.8.1.4** | mrerp_xlsx_generator schema 大改对齐 Korn 真样本(header 18/detail 8/tail 3) | 11828964 | ✅ |
| **v27.8.1.5** | invoice_no `INV-2026-0501` → `690415-001`(BE+MM+DD+seq) + 下载 xlsx debug | 11828965 | ✅ |
| **v27.8.1.6** | 抢救式抓 MR.ERP 错误 hint(red text + JS alert + ไม่พบ/ผิดพลาด)+ raw HTML 存 | 11828966 | ✅ |
| **v27.8.1.7** | 强制 cell 物理保留(`' '` 占位) + sheet1 col 19 spacer · dim=A1:S2 | 11828967 | ✅ |
| **v27.8.1.8** | 🧪 Korn 真样本对照测试 endpoint + UI 按钮 · 决定性诊断(mrerp_pusher OK + xlsx 字节差异) | 11828968 | ✅ |
| **v27.8.1.9** | 后处理 inlineStr → sharedStrings · 处理 `&#NNNN;` 双重 escape 坑 | 11828969 | ✅ |
| **v27.8.1.10** | 🔬 自诊断对比 endpoint(zip 文件级 diff) + UI modal + 两 xlsx 下载 | 11828970 | ✅ |
| **v27.8.1.11** | XML 后处理 · row spans + 完全空 cell + sheet3 只 header + 去 t="n" | 11828971 | ✅ |
| **v27.8.1.12** | ⭐ Korn 模板克隆方案 · 6 metadata 文件不动 · MR.ERP 推送 100% 打通 ✅ | 11828972 | ✅ **真写库验证** |
| **v27.8.1.13a-14d** | 10 个子版本 · MR.ERP 整链路用户旅程完美闭环(凭据 modal 重构 / 字段映射 UX / armas 真客户主表 / mini modal 内联引导 / 智能推荐排前 / Korn 0006 真实推送) | 11828973-11828122 | ✅ |
| **v27.8.1.14e** | 修「上传图片多选强制合并」痛点 · 默认行为反转(gallery 默认分别 · camera 默认合并) | 11828123 | ✅ |
| **v27.8.1.15** | 批量 500 张 + plan 上限+300 + admin 999→9999 + auto_push 默认开 + 大批量进度条 + 新用户引导 modal | 11828124 | ✅ **用户测试通过** |
| **v27.8.1.16** | score=1.0 零点击 + 0.7-0.97 中分 undo toast(3 秒倒计时 + [改一下]/[没问题])+ 列表 recommend/maybe 徽章 | 11828125 | ✅ **用户测试通过** |
| **v27.8.1.17** | 商品对照表 stkmas + detail 行真 product_code + product mini modal(逐个解决)+ 子串闸 fix(占比 ≥ 0.5 才认 0.85)| 11828126 | ✅ **已部署 · 等用户测** |
| **v27.8.1.17.1** | 租户管理 6 bug hotfix(plan_expires_at 字段同步 / monthly/yearly/lifetime 分支 / 员工字段全继承 / tenant.subscription_expires_at 同步 / 幽灵字段移除 / SSoT 对齐) | 11828127 | ⏳ **待部署测试** |

**线上版本号**:**v118.27.8.1.14b.3**(2026-05-14 · 3 项 bug 修复全上线)
**前期里程碑**:v27.8.1.12 MR.ERP 推送通道打通 · 数据真进 TEST2019 库
**核心成果**:`SI690415-001` 净额 4,635.24 写入 mrerp4sme.com TEST2019 库验证通过 · 整条 OCR → MR.ERP 自动推送链路闭环

---

## 🔥 P0-ERP 改善清单（2026-05-14 · **排在 v18-v22 和其他所有模块之前**）

> **来源**：2026-05-14 全流程产品审查（OCR 识别 → 归属客户 → MR.ERP 推送）完整 UX/逻辑/Bug 审计
> **优先级**：全部排在 v18-v22、OCR 速度优化、银行对账之前

### P0 · 立刻修（下窗口第一优先）

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 1 | **归属客户保存后必须关闭重开抽屉才能推送**：前端 `_openHistoryDrawer` 拿的是旧 task 对象 snapshot，保存后没刷新 state，导致 `client_id` 仍为空，推送报「请先归属客户」| `home.js` | 0.5h |
| 2 | **推送成功后无标记，可重复推同一张发票**：无 `is_pushed` flag，无二次确认，用户无法判断是否已推 | `home.js` + 后端 | 1h |

### P1 · 本周

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 3 | **错误文案误导**：报「请先在自动化配置 ERP 端点」，实际原因是「请先为此发票选择归属客户」，并高亮选择框 | `home.js` i18n | 0.3h |
| 4 | **识别成功率显示超 100%**（333% 等）：应改为「共识别出 N 张发票」，去掉百分比 | `home.js` | 0.3h |
| 5 | **字段映射缺「商品映射」tab**：现有客户/科目/税码三 tab，无法管理 `item_name → erp_code` 映射，删除操作全靠 SQL | `home.js` | 2h |
| 6 | **商品 modal 搜索框未预填充 OCR 商品名**：每次手动输入，效率低 | `home.js` | 0.5h |
| 7 | **推送成功弹窗无 MR.ERP 跳转链接**：用户无法一键跳去 MR.ERP 赊销列表核实 | `home.js` | 0.5h |
| 8 | **客户映射备注含内部版本号「v16」**：应改为「系统自动识别 · {日期}」 | `home.js` | 0.2h |

### P2 · 下周

| # | 问题 | 文件 | 工时估算 |
|---|---|---|---|
| 9 | **商品 modal 缺「全部跳过」按钮**：多件商品时每次只能逐个跳 | `home.js` | 0.5h |
| 10 | **推送日志「ERP 返回结果: 2」无意义**：需翻译为友好文案「成功推入 N 行明细」| `home.js` | 0.3h |
| 11 | **商品 modal 加载无进度提示**：连接 MR.ERP 商品库期间界面空白，用户不知道在加载 | `home.js` | 0.5h |

### 逻辑设计（需 Zihao 拍板）

| # | 问题 | 影响 |
|---|---|---|
| 12 | **`erp_client_mappings` 按 `client_id` 存储**：同一 Pearnly 客户下不同买方（如不同分公司）全推同一个 MR.ERP 客户 · 会计事务所管多家公司时可能错推 | 设计决策：保持现状（适合一对一绑定）vs 改为按 `buyer_name` 存储（适合多买方场景）|

### Bug #4（后续调查）

| # | 问题 | 调查方向 |
|---|---|---|
| 13 | **`/api/erp/mrerp/products` 不返回 P001/Pepsi 500ml**（已 Approved）：`_mrerp_fetch_products_raw` 通过 stkmas showdata.php 抓页面 HTML，疑似 P001 所在行解析失败 | 服务器手动运行 `_mrerp_fetch_products_raw(tid)` 打印原始 HTML，确认 P001 是否在里面，定位 `_parse_mrerp_products_html` 解析问题 |

### 绕过方案（Bug #4 修复前）

商品 modal 下方有「手动输入编号」折叠区，用户可直接键入 P001 → 保存 → 映射写入 → 下次同商品名自动复用

---

## 🔥 v118.27.8 系列细化(本窗口拍板 · 不推翻三层架构)

### 三层架构红线(继承 · 全部生效)

| 层 | 名称 | 客户类型 | 状态 |
|---|---|---|---|
| **C** | xlsx 兜底 | 入门 / 谨慎 | ✅ v27.5.3+v27.6 已上 |
| **D** | 浏览器扩展(用浏览器现成 PHPSESSID 推) | 不存密码但要一键 | ⏳ v118.30+ |
| **A** | 后端模拟登录(凭据 KMS 加密存) | 信任 Pearnly · 后台批量 | ✅ 引擎 v27.8.0.4 完成 · 🔥 接 UI 在 v27.8.1.0 |

A 永远不是默认 · UI 必须显眼让用户知道也支持 C。任何一层失败 → 自动降级。

### v27.8 拆分进度(2026-05-11 v14d 收尾更新)

```
v27.8.0   反向工程 + 后端骨架            ✅ 100%
v27.8.1.0 MVP(凭据 + 一键直推)         ✅ 完成
v27.8.1.1 IIFE race + setTimeout 修复   ✅ 完成
v27.8.1.2 公式修复 + _userInfo 轮询      ✅ 完成
v27.8.1.3 自动推送 toggle 端到端         ✅ 完成
v27.8.1.4 schema 大改对齐 Korn 真样本    ✅ 完成
v27.8.1.5 invoice_no 格式 + 下载 xlsx    ✅ 完成
v27.8.1.6 抢救式抓 MR.ERP 错误 hint      ✅ 完成
v27.8.1.7 强制 cell 物理保留 + spacer    ✅ 完成
v27.8.1.8 Korn 真样本对照测试(神器)     ✅ 完成
v27.8.1.9 inlineStr → sharedStrings      ✅ 完成
v27.8.1.10 服务器端字节级自诊断          ✅ 完成
v27.8.1.11 XML 后处理对齐 row spans      ✅ 完成
v27.8.1.12 ⭐ Korn 模板克隆方案 · 推送 ✅ 完成 · 真写库验证
v27.8.1.13a 凭据 modal 重构 + 字段映射 UX + 上传自动归属 bug 修复  ✅ 完成
v27.8.1.13b 测试连接 → 自动探测账套(selectdb.php 解析)            ✅ 完成
v27.8.1.14a/14a.1 dev 抓 MR.ERP 页面 / 客户列表(反向工程)         ✅ 完成
v27.8.1.14b/14b.1 OCR 抽屉 mini modal + 错误码归一 · Korn 0006 验证 ✅ 完成
v27.8.1.14b.2/14b.3 banner + UX 减重(顶栏 SSoT)                  ✅ 完成
v27.8.1.14c 数据源切到 armas 真客户主表 + 深度栈精确解析             ✅ 完成
v27.8.1.14d ⭐ OCR 买方名模糊匹配 + 推荐排前 · MR.ERP 整链路闭环   ✅ 完成
v27.8.1.14e 上传图片多选默认改成分别 · camera vs gallery 分支       ✅ 完成

🔥 P0-A · MR.ERP 全链路完美化(9.5 天):
v27.8.1.15 批量 500 + plan +300 + auto_push 默认开 + 新用户引导     ✅ 完成 · 用户测试通过
v27.8.1.16 score=1.0 零点击 + 0.7-0.97 中分 undo toast              ✅ 完成 · 用户测试通过
v27.8.1.17 商品对照表 stkmas + detail 行真商品码 + 子串闸 fix       ✅ 完成 · 已部署 · 等测试
v27.8.1.17.1 租户管理 6 bug hotfix(套餐升级数据一致性)             ⏳ 待 Zihao 部署测试
v27.8.1.18 OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab(v17 遗留) 🔥 下个窗口主任务(1.4 天)
v27.8.2   ERP 主页 UI 三件套(完整映射 UI 已删 · 被 mini modal 替代) 🔥 (2 天)
v27.8.3   推送预览 + 凭据失效检测 + 失败自动降级 xlsx              🔥 (1.7 天)
v27.8.4   真实可达性测试                                          🔥 (0.5 天)
v27.8.5   重复防护 + 批量推送 + ERP 链接 + LINE 推老板             🔥 (1.9 天)

P1 · 公测前 / 战略:
v27.8.6   webhook 卡片化 + 砍蓝按钮(原 v27.8.1.16 降级)           (0.5-1 天)
A.1       Git 远程私库 push · 公测前必做                          (0.5 天)
```

### 🔥 P0-A · MR.ERP 全链路完美化 v15-v22(9.5 天 · v14d 窗口拍板 · 用户全采纳)

> **来源**:`Pearnly_票据到ERP归档_用户旅程分析_v118_27_8_1_14d.md` · 用户拍板"MR.ERP 相关全部排前 · 其他依次排序"
> **详细任务**:见 BACKLOG.md 的 P0-A 章节

**优化目标**(操作数对比):
- 现状:新客户 score=1.0 → 2 次操作 / 批量 50 张 → 50 次推送
- v22 完成后:**新客户 score=1.0 → 0 次操作**(零点击)/ **批量 50 张 → 1 次推送**(批量推)
- 80% 用户场景"想 0 次"· 20% 用户场景"想 1 次"· 0% 用户场景"想 2+ 次"

| 版本 | 内容 | 估时 | 状态 |
|---|---|---|---|
| **v15** | 批量上传 500 + plan 上限+300 + auto_push 默认开 + 新用户引导 | 1 天 | ✅ |
| **v16** | score=1.0 零点击 + 中高分快速确认 toast | 0.6 天 | ✅ |
| **v17** | 商品对照表 stkmas + detail 行真商品码 | 1.5 天 | ✅ 等用户测 |
| **v17.1** | 租户管理 6 bug hotfix | 0.3 天 | ⏳ 待部署 |
| **v18** | OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab | 1.4 天 |  |
| **v19** | ERP 主页三件套(4 KPI + 连接器 + 推送日志) | 2 天 |
| **v20** | 推送预览页 + 凭据失效检测 + 失败自动降级 xlsx | 1.7 天 |
| **v21** | 真实可达性测试 | 0.5 天 |
| **v22** | 重复防护 + 批量推送 + ERP 链接 + LINE 推老板 | 1.9 天 |

### 红线 2 · ERP 对接主页 UI 三件套(继承 · v19 实施)

```
① 统计区 · 顶部 · 4 张 KPI 卡(今日已推/待推/失败/自动化率)
② 连接器卡片 · 中部 · Xero/MR.ERP/Webhook + 虚位卡(FlowAccount/PEAK/QB 灰)
③ 推送日志 · 底部 · 表格 + 时间筛选 + 失败行「解决」跳 OCR
```

**注**:原计划在 v19 加的「完整映射 UI / 默认值设置 modal」**已删** —— 14b 已决定 mini modal 替代 + 默认值后端写死(铁律 62)。

### 红线 3 · 真正难点是映射 UI(已被 v14d 解决)

OCR 拿名字 · MR.ERP 要 code:
- 客户名 · v14b/c/d 已用 mini modal + armas + 模糊匹配解决 ✅
- 商品名 · v17 商品对照表用同样方案解决
- 默认仓库 / 部门 / 销售员 · 后端写死(铁律 60 业务化)· 不再要求用户配

---

## 🔌 MR.ERP 反向工程结果(本窗口完成 · 100%)

### 测试环境

```
URL:        https://www.mrerp4sme.com
Username:   test01 / Password: test01
公司:       1010-01-000006 บริษัท ทดสอบการใช้ จำกัด
数据库:     TEST2019(URL ?comidyear=6&seldb=1)
内部 idus:  15(test01 用户 · 从 formupload.php hidden input scrape)
```

### 全 5 步 endpoint 字典(实测通过 ✅)

| 步 | URL | Method | Body | Response |
|---|---|---|---|---|
| 0a 预热 | `/` | GET | - | (set PHPSESSID) |
| 0b 登录 | `/login/checklogin.php` | POST | `txtusers=X&txtpasswords=X&btnsubmit=Submit` | 200 + HTML(同 URL · 不 redirect) |
| 0c 选公司页 | `/login/selectdb.php` | GET | - | 200 |
| 0d 选公司 | `/login/mainmenu.php?comidyear=6&seldb=1` | GET | - | 200 + 主菜单 HTML(被踢回 login = 鉴权失败判定) |
| 0e scrape idus | `/impartran/formupload.php?idmenu=370` | GET | - | 200 + HTML(含 `<input hidden name="idus" value="15">`) |
| **1 上传** | `/impartran/component/uploadexcel.php` | POST | **multipart**: `uploadfile=<file>` + `idus=15` + `selmenu=118` | 200 + 0 字节(文件存 server session) |
| **2 预览** | `/impartran/formrdpc.php` | POST | `idus=15&selmenu=118`(form-urlencoded) | 200 + HTML(form 含 `cbimport[N]` checkbox) |
| **3 确认** | `/impartran/component/importpc.php` | POST | **multipart**: `idus + selmenu + cballfrmimport1=on + cbimport[N]=N` | 200 + 短字符串(数字="2"=新 row id 成功 · 非数字=错误) |

### 路径分类(铁律 51)

```
impartran/  = 交易类业务单据(销售/采购/收付款 import · idmenu=370 是赊销)
imparse/    = 主数据类 / 现金销售 import 走这里(idmenu=371)
expartran/  = 交易类导出(idmenu=404 商品销售导出)
```

### idmenu / selmenu 字典(部分 · v27.8.2 补全)

| 业务 | idmenu | selmenu | 路径 | sheet 数 | 状态 |
|---|---|---|---|---|---|
| SC 赊销 import | 370 | 118 | impartran | 3 | ✅ 实测 |
| SC 销售导出 | 404 | 118(下拉切) | expartran | - | ⚠️ URL 知 · cURL 待抓 |
| SE 现金销售 import | 371 | ❓ 未抓 | imparse | 4 | ⏳ |
| 采购 / 收款 / 付款 / 凭证 | ❓ | ❓ | ❓ | ❓ | ⏳ v27.8.2 |

详细 endpoint 字典 + 8 个踩坑细节 + scrape idus bug 修复 · 见 `HANDOVER_v118_27_8_1_0.md`。

---

## 🆕 铁律清单(累计 62 条 · v14d 窗口新增 61-62)

旧 1-58 见 v118.27.8.0 HANDOVER · 不变。

### 本窗口新增(2026-05-11)

59. **MR.ERP sales_credit xlsx 必须用 Korn 模板克隆生成**(2026-05-11):`mrerp_xlsx_generator.py` 的 sales_credit 路径走 `_generate_xlsx_sales_credit_korn_clone()` · 6 个 metadata 文件不动(workbook.xml / [Content_Types].xml / styles.xml / theme.xml / 2 个 rels) · 只重写 sharedStrings + sheetData · 模板必须存在 `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` · 不许直接 openpyxl save(它会重写 workbook.xml 丢失 PhpSpreadsheet 兼容性)

60. **UI 文案业务化** · 不能用程序员术语(2026-05-11):「映射」→「对照」/「对照表」(会计师懂)· 「凭据」→「账号」 · 「ERP 端编号」→「客户在 ERP 里的编号 / 商品码」 · `comidyear` / `seldb` 折到「高级设置」隐藏 99% 用户不动 · 文案要假设「会计师不懂技术」 · 所有出现技术名词的地方都要业务化

61. **MR.ERP 主数据用 `showdata.php` 通用 pattern 抓**(2026-05-11 · v14c/v14d 实测):所有 `/X/allview.php?idmenu=N` 列表页 = 空壳 + AJAX 后填(`<div id="showdata">` 由 `showdata()` 异步填充)· 客户端反向工程要点:① warm-up GET 列表页(种 Referer / PHPSESSID)· ② POST `/X/component/showdata.php`(form data: `showdata_numrows=30 / showdata_pages=N / searchdataval=""`)翻页拼接 · ③ 用顶层 `<span>` 深度栈解析(避开 URA hover 嵌套 span 干扰)· ④ 停止条件:返回空 / `id="nodata"` / `len(chunk) < 10` · 任何 MR.ERP 主数据(客户 armas / 商品 stkmas / 供应商 apmas / 仓库 store 等)都走这套

62. **字段对照表 = 后台页 · 不是主入口**(2026-05-11 · v14b 大反思):99% 用户**不**主动进「字段对照表 / 自动化 → ERP 对接 → 字段映射」 · 那是给老司机审计 / 批改用的后台页 · 用户的客户/商品/税码映射应在 **OCR 抽屉推送时按需配**(失败那一刻就地解决) · 任何"先去配置 → 再使用"的 UX 都是失败设计 · mini modal 内联引导 + 智能推荐 + 手动输入备份才是正解

### 本窗口 v15-v17.1 新增(2026-05-11)

63. **模糊匹配子串规则必须有占比闸**(2026-05-11 · v17 边界 fix):`_match_buyer_score` 的 0.85 子串包含规则需加约束:短串占长串 ≥ 50% 才认 0.85 强子串匹配 · 否则降级 SequenceMatcher 兜底。否则会出现「Random XYZ Co」误推荐「XYZ Limited」(3 字符占 9 字符 0.33 触发 0.85)。这条铁律适用任何主数据模糊匹配 ·  客户 / 商品 / 供应商通用。

64. **用户字段必须 SSoT · 顶栏 vs 设置页**(2026-05-11 · v17.1):`/api/me/plan` 是套餐相关字段的权威源 · `_build_user_info` 同样字段必须对齐。两个 endpoint 都要返 `plan_expires_at` / `plan_days_left` / `trial_expires_at` / `trial_days_left` 这一套 · 顶栏走前者 · 设置页走后者 · 双方显示必须完全一致 · 否则会出现「顶栏年付364天 / 设置页月度订阅—」自相矛盾 BUG。

65. **员工继承老板套餐字段必须全套继承**(2026-05-11 · v17.1):`_build_user_info` 检测 `role=member` 查 owner 时 · 不能只继承 `plan` 一个字段 · 还要同时继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota`。否则员工的设置页 / 顶栏跟老板对不齐(员工看到自己注册时的旧数据)。已在 SELECT 多列 + return dict 同步赋值实现。

66. **`admin_upgrade_user` 必须同步 `tenants.subscription_expires_at`**(2026-05-11 · v17.1):铁律 35 写「tenants 表无 plan / max_seats」 · 但 subscription_expires_at 是真存在的列(在 db.py 5659 建 tenant 时写入)· 之前 admin_upgrade_user 漏更新这个列 · 导致 tenant 表过期值永远停在注册时初始值。任何套餐升级 / 降级路径必须同时维护 `users.plan_expires_at` + `tenants.subscription_expires_at`。

67. **tenants 表无 `trial_expires_at` / `plan_expires_at` 列**(2026-05-11 · v17.1):这两个字段只在 users 表 · `get_tenant()` 返回的 dict **不要**引用 `tenant_info["trial_expires_at"]` 这种幽灵字段 · 否则代码误导(实际 always None 走 fallback 到 user 表)。tenants 表能用的过期字段只有 `subscription_expires_at`。

68. **服务器单独覆盖文件清单**(2026-05-11 · v17):有些文件不进 deploy.sh 主流程 · 必须 Zihao 手动 scp 覆盖。当前清单:`mrerp_xlsx_generator.py`(detail 行 product_code 真码注入需要)。新增此类文件时必须在 HANDOVER 显式标出 · 否则部署后功能缺失没人知道。

---

## 🆕 旧铁律清单(累计 58 条 · 见 v27.8.0 收尾时新增 51-58)

旧 1-43 见 v118.26.2.5 HANDOVER · 不变
44-50 不变(本窗口部分修正见下面)

44. **三层 ERP 对接架构永久并存**(2026-05-10):A 后端模拟 + C xlsx 兜底 + D 浏览器扩展 · 任何一层失败自动降级 · A 不是默认
45. **ERP 对接主页 UI 三件套**(2026-05-10):统计 + 连接器卡片 + 推送日志 · 缺一不可(留 v27.8.2 做 · MVP v27.8.1.0 不做)
46. **MR.ERP 反向工程 ✅ 100% 完成**(2026-05-10 本窗口):认证 = 单一 PHPSESSID cookie · 无 CSRF · 无签名 · 全 5 步 endpoint 实测通过
47. **v27.8 真正难点是映射 UI**(2026-05-10):OCR 名字 → MR.ERP code · 必做主数据缓存 + fuzzy match + 用户确认 + 推送预览(留 v27.8.2 做)
48. **真实可达性 60%/90% 不是 100%**(2026-05-10):首次 60% · 重复 90% · 失败必兜底 .xlsx
49. **后端到后端跳过浏览器 JS 校验**(2026-05-10):v27.8 直接 HTTP POST · 不走前端 · 浏览器抓的弹窗错误跟我们无关
50. **MR.ERP idmenu 决定子模块**(2026-05-10):371=现金销售(imparse 路径 · 4 sheet) · 370=赊销(impartran 路径 · 3 sheet) · 各模块 sheet 数 + 路径不同 · v27.8 客户端按 module dispatch

### 本窗口新增 51-58(2026-05-10)

51. **MR.ERP 路径分两套**:`impartran/`(交易类业务单据 · 销售/采购/收付款 import) ≠ `imparse/`(SE 现金销售 + 推测主数据类) ≠ `expartran/`(交易类导出) · 不是单一 endpoint · 同模块名可能跨路径
52. **idus 是 MR.ERP 内部用户 ID**(test01=15 · 不是 username):scrape 来源 = 任意业务页的 `<input type="hidden" name="idus" id="idus" value="N">` · 必须用 BeautifulSoup 解析(name 和 value 之间隔了 id 属性 · 严格正则会漏)
53. **idmenu ≠ selmenu**:idmenu = URL 路由 ID · selmenu = 业务子类型字典(118=ขายเชื่อ-รายได้ขายในประเทศ赊销国内销售)· 同 idmenu 可通过 ชื่อเมนู 下拉切 selmenu(import 和 export 共用同一字典)
54. **MR.ERP 完整 5 步流程铁律**(不可乱序):
    1. GET / 预热(必须 · PHP session 初始化)
    2. POST /login/checklogin.php(`txtusers/txtpasswords/btnsubmit=Submit` 字段名都是复数 · 带 Referer)
    3. GET /login/selectdb.php(选公司页 · 模拟用户流程)
    4. GET /login/mainmenu.php?comidyear=N&seldb=N(激活公司 + 真实判登录成功 · 被踢回 login = 失败)
    5. GET /impartran/formupload.php?idmenu=N(scrape idus)
    6. POST upload → POST formrdpc → POST importpc(实际推送 3 步 · 同 PHPSESSID)
55. **MR.ERP importpc.php 必须 multipart**(虽然字段全是文本)· 服务端不接 form-urlencoded · requests 用 `files=[(name, (None, value))]` 触发
56. **MR.ERP 上传不是 AJAX 是浏览器整页跳转**(uploadexcel.php POST → 浏览器跳到 formrdpc.php)· 但**后端代码不需要模拟跳转** · 直接顺序 POST 即可
57. **MR.ERP checklogin.php 不靠 r.url 判成功**(POST 后永远停在 checklogin.php 自己 · 即使成功也不 redirect)· 真实判定 = 看下一步 GET mainmenu 是否被踢回 login + 看 body 是否含 txtusers
58. **MR.ERP confirm 返回值约定**:数字字符串(如 "2") = 成功 · 表示新 row id · 非数字 = 错误信息(具体格式待 v27.8.2 故意失败 1 次抓样本)· 单号重复行为未确认(实测 690507-001 反复 confirm 都成功 · 可能允许重复)

---

## 当前已知小问题(2026-05-11 v17 / v17.1 更新)

**MR.ERP 主线**:
- v14d 整链路完美闭环 ✅ · Korn 0006 真实推送验证 ✅
- v15 批量上传 500 + plan +300 + admin 999→9999 + auto_push 默认开 ✅
- v16 score=1.0 零点击 + 0.7-0.97 中分 undo toast ✅
- v17 商品对照表 + detail 行真 product_code + 子串闸 fix ✅ **已部署 · 等用户测**
- v17.1 租户管理 6 bug hotfix ⏳ **待部署**
- **服务器需单独 scp 覆盖 `mrerp_xlsx_generator.py`**(detail 行 product_code 真码注入 · 不在 deploy.sh 范围 · 不覆盖则商品映射 v17 链路只生效到映射保存 · xlsx 仍写 `123` 占位)
- **完美匹配场景仍要点 modal 确认**(v16 已解 · 待复测)
- **批量推送缺**(v22 解):50 张要点 50 次
- **凭据失效场景没自动检测**(v20 解)
- **推送失败无自动 xlsx 降级**(v20 解)
- **多客户混合上传归属不准**(v18 智能归属解)
- **重复推送防护缺**(v22 解)
- **字段对照表 product subtab 未做**(v17 BACKLOG 写要做 · 实际未做 · 推到 v18 · 理由:99% 用户从 mini modal 走 · 不阻塞主路径 · 铁律 62 已锁定)

**v14d 实施偏离原 BACKLOG**(已锁定为铁律 62):内存缓存 5 分钟 + 按需拉 + mini modal 显示全部 + 智能推荐排前 · 优于原计划 erp_master_cache 24h + 测试连接预热 + top 3 fuzzy modal。

**v15 实施细节**(本窗口决策):
- plan 上限调整全档单调升:trial 15→30 / monthly 30→500 / yearly 50→800 / lifetime 100→1000 / **admin 999→9999**(铁律:admin >= lifetime · 不能更少)
- 大批量提示阈值 100 张:进度条 IIFE + beforeunload + 首次一次性 toast
- ERP 新建表单 auto_push 默认 true(不动老用户已关的状态)

**v16 实施细节**:
- 客户 mini modal 完美匹配零点击:`_fetchAndRender` 拿 auto_select_code → `_autoApplyPerfect` 静默保存 + onSelected 自动重推
- 中分 0.7-0.97 不弹完整 modal · 弹右下角 undo toast(深色底 + 进度条 · 3 秒倒计时 + [改一下] / [没问题])
- 列表 score 徽章:≥0.7 橙色「推荐」/ ≥0.45 浅黄「可能」
- 后端 `_normalize_buyer_name`(去 4 语公司后缀)+ `_match_buyer_score` + `_rank_customers_for_buyer`

**v16 边界 fix**(本窗口主动发现 · 留 v17 顺手修):
- v16 子串规则只判「buyer 包含 name 或 name 包含 buyer」就给 0.85 · 短串挂中长串假阳性(如 "Random XYZ Co" vs "XYZ Limited" 误推荐)
- v17 加占比闸:短串占长串 ≥ 0.5 才认 0.85 · 否则降级 SequenceMatcher
- 测试验证:Random XYZ Co vs XYZ Limited 从 0.85 降到 0.43(不再误推荐)· 完美匹配 1.0 不受影响

**v17 实施细节**:
- DB:`erp_product_mappings` 表(tenant_id / erp_type / item_name / item_name_norm / erp_code / erp_name) + 4 CRUD + `find_erp_product_mappings_batch`(批量预检用)
- `get_mrerp_mappings_bundle` 加 `products` key
- 后端 stkmas(idmenu=24)抓取 + 5 分钟缓存(走铁律 61 同样 showdata.php pattern)
- 4 endpoints:`GET /api/erp/mrerp/products?item_name=X` / `GET/POST/DELETE /api/erp/mappings/products` / `POST /api/erp/mrerp/products/check`(批量预检)
- 前端 `_pushOne` 顶部 hook `_checkProductsBeforePush` · 多 unmapped item 串行 `_runProductMappingFlow` 逐个弹 product mini modal
- `openMrerpPickProduct` 独立 IIFE(350+ 行 · 接 `{itemName, indexHint, totalHint, onSelected, onSkip, onCancel}`)· 完美匹配零点击短路 + 「第 i/n 个待配」进度提示 + 跳过 + 取消
- 服务器 `mrerp_xlsx_generator.py` 改:加 `_norm_product_name`(re sub 标点 + lowercase · 跟 db.py 一致) + `_build_product_lookup` + `_resolve_product_code` · `build_sales_credit_detail_rows` 循环外建 lookup 一次 · 内循环 O(1) 查 item.name 写入 row 的 `product_code`(找不到 None 下游 `or '123'` fallback)
- 4 语 i18n × 19 词条

**v17.1 实施细节**(用户截图报 + 主动深度排查 6 bug):
- Bug 1:`_build_user_info` 只读老 `users.expires_at` · 没读 `plan_expires_at` → 设置页有效期「—」
- Bug 2:前端 settings 页 plan 分支只覆盖老名 pro/team/firm/enterprise · 新名 monthly/yearly/lifetime 走兜底「月度订阅」
- Bug 3:员工继承老板时只继承 `plan` 字段 · 没继承 `plan_expires_at` / `trial_expires_at` / `monthly_quota` → 员工设置页跟老板对不齐
- Bug 4:`admin_upgrade_user` 漏更 `tenants.subscription_expires_at` → tenant 表过期永远停在注册值
- Bug 5:`_build_user_info` 读 `tenant_info["trial_expires_at"]` 幽灵字段(tenants 表无此列)
- Bug 6:`/api/me/plan` 跟 `_build_user_info` 字段不一致 SSoT 违反 · 修法是后者加 `plan_expires_at` / `plan_days_left` 对齐前者
- 新前端 4 语 × 5 词条(settings-sub-monthly / yearly / lifetime / settings-days-left / settings-lifetime-forever)
- 后续监控点:升级套餐后 顶栏 + 设置页 + 员工 设置页 三处显示是否完全一致

**非 MR.ERP**:
- v118.26.2.5 用户管理/租户连环 BUG 全修通过用户测试 ✅
- `/api/me/plan` 慢 2.5-3.4s(测试中心 api_slow 触发)· 加 5 分钟前端缓存 · 0.2 天 · P2
- `deploy.sh` 不复制 `VERSION` · 顺手补
- **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- home.js 死代码 · 0.2 天 · P3
- 老的 `HANDOVER_v118_27_8_1_14e.md` 已过期 · 由 Zihao 删除(铁律 13)
- 新的 `HANDOVER_v118_27_8_1_17_1.md` 给下个窗口接 v18 用 · 必读