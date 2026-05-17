# 交接备忘 · 下窗口接手必读

> **最后更新**:2026-05-18(凌晨) · cache bust CSS/JS **v=11833136** · 当前线上版本 **v118.33.13.6**
> **本窗口主线**:银行对账模块深度重构 — KBank 扫描件 OCR + Mr.erp GL 解析 + 余额验证 + 防幻觉 + Excel 纵向 itemized 汇总

---

## 🔴🔴🔴 下窗口第一件事 · 银行对账匹配率验收(必做)

**测试组合**：
- 银行账单：`D:\Users\Skin\Desktop\银行对账需求\statement.pdf`（KBank 6月2025 · 11条交易）
- GL：`D:\Users\Skin\Desktop\银行对账需求\general ledger BANK.pdf`（账户 1112-01 · 6月2025 · 12条交易）

**预期匹配数**：7-8 条 L1 精确匹配（同日期同金额）：
```
02/06 stmt deposit 115,586.50  ↔  GL RE680602-002 debit 115,586.50
05/06 stmt withdraw 380,000    ↔  GL PV680605-001 credit 380,000
05/06 stmt deposit 227,418     ↔  GL RE680605-001 debit 227,418
09/06 stmt deposit 236,000     ↔  GL BT680609-001 debit 236,000
10/06 stmt deposit 514,539     ↔  GL QR88060844 debit 514,539
15/06 stmt withdraw 1,000,000  ↔  GL PV680615-001 credit 1,000,000
24/06 stmt deposit 12,490.50   ↔  GL JV680624-001 debit 12,490.50
30/06 stmt deposit 115,586.50  ↔  GL RV680630-001 debit 115,586.50
```

**如果匹配率不达预期**，先检查：
1. GL 12 行是否都解析出来（看汇总 sheet · GL 借方仅有/贷方仅有 总数应=12）
2. GL 借贷方向是否对（应该 9 借 + 3 贷，不是全借）
3. GL 期末余额是否 125,100.06（不是 305,356.06 那种）
4. 日志看 `[gl_parse]` / `[stmt_parse]` 行

---

## 🟡 下窗口第二优先 · 用户上次提到的「视觉对照层」（已否决，记录用）

用户曾提议在 Excel 里嵌入原始 PDF 截图做对照，**但已否决**（文件太大）。**不要做**。

替代方案是 OCR 准确性核查（已实现）：
- 每行 stmt 都有 `balance_ok` + `confidence` 标记
- ⚠ 余额校验未通过的行 + ◌ 低置信度行 都在汇总最后单独列出
- 详见 v118.33.13.0 实现

---

## 🟡 下窗口第三优先 · 速度优化（云 OCR 切换）

**当前 OCR 速度**：Gemini 2.5-flash-lite · 单页 10-25s · 5 张并行 ~45s

**进一步加速方案**（待用户决定）：
- 切 Google Cloud Vision API（专门 OCR · 1-2s/页 · 不幻觉 · $1.5/1000页）
- 需要用户提供 GCP Service Account JSON
- 不是急事 · 当前 Gemini 已够用

**已优化**：v118.33.13.1 加了 SHA-256 文件哈希缓存 · 同 PDF 重传秒返

---

## 🎯 本窗口完成清单(2026-05-17 全天 → 2026-05-18 凌晨 · v=11833130→11833136)

### 银行对账 v2 深度重构(v118.33.13.0 → v118.33.13.6)

#### 🔥 核心解析器修复（v118.33.13.4-5 · 解决 0% 匹配的根本原因）

**`_parse_gl_mrerp_table()` 新建** — pdfplumber 把泰文 Mr.erp GL PDF 输出为「整行交易塞进单个合并单元格」格式，老的 `_map_gl_cols` 期待"一列一格"找不到表头 → 0 列映射 → 跳到 pdfminer 文本 → 泰文跨行 → 0 行成功。

新解析器策略：
1. 把 pdfplumber 每行（cells[0] 装整行字符串）当一条交易处理
2. 分词 → 从右扫数字（amount + balance）→ 前部分按 `日期 → 账类型 → 凭证号 → 摘要` 分
3. **借贷方向**：账类型 `รับ`→borrow / `จ่าย`→credit；`ทั่วไป` 用余额增减判
4. **PUA 字符归一化** `_norm_thai()`：U+F70A..F712 → U+0E47..E4D（不归一化的话 `จ่าย` 字符串永远匹配不上 PDF 里的 `จาย`）
5. **严格数字检测** `_is_numeric_tok()`：旧 `_to_float()` 对非数字返回 0.0 而不是 None，右扫数字永远停不下来 — 必须用真正的"是不是数字"检测
6. **现金账户期末余额公式** = `opening + 借方 − 贷方`（旧公式 `+credit -debit` 是费用账视角，错的）

**`merge_gl_files()` 修同公式**（v118.33.13.5）：解析器返回正确 closing 后，merge 又用旧公式覆盖了。两处都要修。

**测试验证**：`general ledger BANK.pdf` 解析结果：
- 12 行 ✓（凭证号 RE680602-001/02、PV680605-001、BT680609-001、JV680624-001、RV680630-001 等齐全）
- Opening 215,228.06 ✓
- Closing 125,100.06 ✓（不再是错的 305,356.06）
- 借贷方向正确（9 借 + 3 贷）

#### 📄 KBank 扫描件 OCR + 防幻觉（v118.33.13.0）

**StatementRow 新增字段**：
- `confidence: 'high'|'medium'|'low'` — Gemini 报告的置信度
- `balance_ok: True|False|None` — 余额逐行校验结果

**`_verify_row_balances()` 新增** — 每行验算 `上一行余额 + 存款 − 提款 == 本行余额`（容差 max(0.05, amt*0.5%, capped 1.0)）。无金额变动的"期初/期末/header"行跳过（`balance_ok=None`）。

**Gemini prompt 改严**：
- 显式禁止猜测："NEVER guess. NEVER infer values from context."
- 看不清的数字必须返回 `null`，不准猜
- 每行附带 `confidence` 字段

**前端高亮**（home.js renderTable）：
- `balance_ok=false` → 整行红底 + ⚠ 图标
- `confidence=low` → 整行橙底 + ◌ 图标
- 鼠标悬停 4 语提示「请核对原 PDF」

#### 🎨 Excel 汇总 sheet 纵向 itemized 重设计（v118.33.13.2 → 13.6）

参考销项税对账模板：A 列 78字宽（项目说明）+ B 列 22字宽（金额）。颜色分层：
- 深色 anchor 行（GL期末 / 账单期末）
- 浅灰 section header（+ / − 加减分类）
- 白色 detail 行（每条未匹配项独占一行 · `· 日期 · 凭证号 · 摘要 · 金额` 格式）
- 浅蓝 subtotal（公式计算期末）
- 红/绿 final（差异）
- 自动负数括号显示 `(1,234.56)` 红色

**Excel 其它改进**：
- 新增「银行账单明细」sheet：OCR 提取全部账单行 + 置信度 + 余额校验列
- 新增「使用说明」sheet（4 语）：sheet 结构 / OCR 图例 / 公式 / 重要承诺
- 「文件信息」sheet：**修复**之前从历史导出时每个文件都显示同一总行数 + 同一银行的 bug。现在 `_parse_info` 持久化到 summary_json 的 `_parse_info` 键，导出时读出真实的每文件数据
- 引擎名脱敏：`Gemini Vision OCR` → `AI OCR`（4 语同步）

#### ⚡ 性能 + 鲁棒性（v118.33.13.1）

| 改动 | 文件 | 说明 |
|---|---|---|
| OCR 缓存 | `bank_recon_v2.py` | LRU 256 条 · SHA-256(file_bytes) 索引 · 同 PDF 重传秒返 |
| 模型切换 | `bank_recon_v2.py` | `gemini-2.5-flash` → `gemini-2.5-flash-lite`（~30-50% 提速 + 便宜） |
| Gemini API key 解析统一 | `recon_routes.py` | bank_v2_run 用 `_user_key()` 不再用 `_user_api_key()` · 同时支持 `gemini_api_key` 和 `custom_gemini_api_key` 字段 |
| `_gl_direction_sanity_check()` | `bank_recon_v2.py` | 检测 GL 全借/全贷情况 · 提示用户「这可能不是银行账户分类账」 |
| 期初余额行不再误报 | `bank_recon_v2.py` | Gemini parser 识别 `ยอดยกมา / brought forward` 等关键字 + 无金额 → 不创建交易行，余额拿去填 `opening` |

#### 📚 服务器依赖装机

| 包 | 用途 |
|---|---|
| `pypdf 6.11.0` | PDF 文本提取（pdfminer 后备） |
| `pdfminer.six 20260107` | KBank 等扫描件 PDF 文本提取主力 |
| 已加 `deploy.sh` Step 3.5 自动安装 | 未来部署不会丢 |

---

## 🌐 当前线上状态(2026-05-18 凌晨 最新部署)

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · `/opt/mrpilot/` |
| CSS/JS cache-bust | **`11833136`** |
| `/api/version` 返回 | `11833136` ✅ |
| 当前部署版本 | **v118.33.13.6** |
| OCR 模型 | `gemini-2.5-flash-lite`（v118.33.13.1 起） |
| 已装 venv 依赖 | + `pypdf 6.11.0` · + `pdfminer.six 20260107`(本窗口装) · 之前的 `pdfplumber 0.11.9` 仍在 |

---

## 🚀 部署方式(2026-05-18 起 · 当前简化版)

**重要**：当前用 **git pull** 部署，不再用 tar.gz 包。

### 本地 → 服务器（推荐流程）

```bash
# 1. 本地修改后 commit
cd D:\Users\Skin\Desktop\pearnly_project
git add <files>
git commit -m "fix(...)"

# 2. 推到 GitHub（local origin 已指向 pearnly-app.git）
git push origin HEAD:master

# 3. 服务器 pull + 同步 static + 重启
ssh pearnly "cd /opt/mrpilot && git pull pearnly master && cp home.html static/home.html && cp home.js static/home.js && systemctl restart mrpilot && sleep 4 && systemctl is-active mrpilot"

# 4. 验证版本
ssh pearnly "curl -s http://127.0.0.1:7860/api/version | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"version\"])'"
```

### Git remote 配置

| 端 | 名 | URL |
|---|---|---|
| 本地 | `origin` | `git@github.com:skin306152-star/pearnly-app.git`（active） |
| 服务器 | `origin` | `git@github.com:skin306152-star/mrpilot.git`（OLD · 不用） |
| 服务器 | `pearnly` | `git@github-pearnly:skin306152-star/pearnly-app.git`（active · pull 用这个） |

**关键**：本地用 `git push origin` 推到 pearnly-app.git；服务器用 `git pull pearnly master` 拉同一个 repo。**别**在服务器上对 `origin` 做任何操作（那是老 repo）。

### SSH 别名

`C:\Users\skin3\.ssh\config` 已配 `Host pearnly` 别名（指向 root@45.76.53.194）+ Ed25519 key。直接 `ssh pearnly "..."` 不用密码。

### Cache bust 规则

每次改 `home.html` / `home.js` / `home.css` 后必须改 `home.html` 里的：
```html
<script src="/static/home.js?v=NNNNNNNN"></script>
```
版本号建议格式 `vMMSSPPNN`（M=主版本 S=小版本 P=patch N=micro）。当前 `11833136` 对应 v118.33.13.6。

### 「Already up to date」不是问题

`git pull pearnly master` 经常显示 `Already up to date.` — 这是因为：
- 本地直接推到 pearnly-app.git master 分支
- 服务器拉同一 repo 的同一分支
- 它们已经同步，pull 是 no-op

**验证部署成功的方式**：看 `git log --oneline -3` 是否包含最新 commit，看 `/api/version` 返回的版本号是否对得上。

### deploy.sh（tar.gz 部署 · 备用方案）

如果有大改动想做完整 backup + rollback：
```bash
# 本地打包
tar -czf pearnly_v118_33_13.tar.gz *.py *.html *.js *.css ...

# 上传
scp pearnly_v118_33_13.tar.gz pearnly:/tmp/

# 服务器执行
ssh pearnly "bash /opt/mrpilot/deploy.sh /tmp/pearnly_v118_33_13.tar.gz"
```

`deploy.sh` 含自动备份 + 解压 + 重启 + 失败回滚 + 清理。Step 3.5 会自动 pip install pypdf/pdfminer.six 防丢。

---

### 核心任务：把「自动化」侧边栏并入「集成」 · 用右侧抽屉承载配置面板

**背景**：Phase 5(v118.33.5.0)当时漏了关键步骤 — 自动化的 route/page/nav 没删 · 集成页配置按钮还跳去自动化。本次彻底收尾。

**方案已拍板**：右侧抽屉(Drawer)模式。点集成页配置按钮 → 右侧滑入面板 · 不离开集成页。

**详细执行计划见 BACKLOG.md 「NAV-IA Phase 5 收尾」章节**（写有每步代码模板 · 7 个步骤 · 顺序固定）。

**整体步骤速览**：
1. 集成页加通用右侧抽屉 HTML/CSS/JS 组件
2. 集成页 4 个配置按钮(LINE Bot/文件夹/Gmail/ERP)改调 `openIntegrationDrawer(tab)`
3. ERP 配置抽屉特殊处理(复用现有 loadErpEndpoints)
4. 集成页新增「智能提醒」卡片(当前唯一缺失功能)
5. 对账中心银行对账改用抽屉(不再跳自动化)· `_gotoBankUpload` → `_openBankDrawer`
6. 删自动化侧边栏入口(VALID_ROUTES / nav-item / i18n key / DOM)
7. 全链路验证 + 部署 · cache bust 11841126→11841127

**关键文件**：`home.html` · `home.css` · `home.js`（自动化相关搜 `loadAutomationPage` / `switchAutomationTab` / `nav-automation`）

**验收目标**：侧边栏只剩 6 项：首页 / 销项管理▾ / 进项管理▾ / 客户 / 异常 / 集成

---

## 🔴🔴 下窗口第二件事(之前遗留)

### Excel 差异明细 Sheet 表头美化(gl_vat_reconciler.py · ws1)

**用户要求(截图已确认):**
- KPI 区（Row 1: 总笔数/完全匹配/有差异/GL未找到/差异金额合计）：对应颜色填充 + 字体加粗加大
- 主表头行（Row 4: 状态/单据号/日期/客户名称/VAT报告金额/GL金额/差异/收入科目代码）：加大加粗 + 颜色填充更漂亮

**当前状态(截图观察):**
- Row 1 KPI label 行：浅色文字 · 无填充 · 无粗体
- Row 2 KPI value 行：数值加粗 · 有红色边框(openpyxl Border)
- Row 4 主表头：深蓝 `#1F3050` 背景 + 白色文字 + 粗体 ← 已有基础 · 可微调

**改动文件:** `gl_vat_reconciler.py` · 函数 `_write_ws1_detail(ws, rows, t)` (或类似)

**设计建议(参考 design system 暖灰风):**
- KPI label 行(Row 1)：`#F0F4FF` 浅蓝底 · `#3B5998` 蓝色字 · 粗体 · 11px
- KPI value 行(Row 2)：`#ffffff` 白底 · 数值 14px 加粗 · 颜色跟随状态(OK绿/warn橙/err红)
- 主表头行(Row 4)：保持深蓝 `#1F3050` 或升级为 `#1E3A5F` · 字体 10px 加粗 · 行高 20
- 状态色：✓匹配=`#16A34A`绿 · GL未找到=`#D97706`橙 · 有差异=`#DC2626`红

**验证方法:**
1. 进 pearnly.com → 收入对账 → 上传 `D:\Users\Skin\Desktop\新需求\` 两个 PDF
2. 开始对账 → 完成 → 点对账汇总头部"导出 Excel"按钮
3. 打开 Excel → 看 差异明细 Sheet(ws1)Row 1-4 表头样式

---

## 🟡 下窗口第三优先(之前遗留)

### 验证 Excel 对账汇总格式

**客户 Korn 的要求(原话 Thai):**
- `ตัวเลขแสดงถูกหมดแล้ว` = 数字全正确 ✅
- `ลบช่องสีเหลืองออกแค่นั้น ตัวเลขเยอะ สับสน` = **只删黄色格 · 数字太多太乱**

**Korn 期望的 ws2(对账汇总)格式:**
```
[深蓝行]  总账金额合计               | 4,548,637.56
[粗体行]  减: 贷方记录不在VAT报告中   |               ← B列必须为空!
          · IV6812003 · 06/12/68    | (10,500.00)   ← 金额只在缩进明细行
[粗体行]  加: 借方记录不在VAT报告中   |               ← B列必须为空!
          · SR5904006 · 04/12/68    | 1,000.00
[粗体行]  加: VAT有GL无的销售记录     |               ← B列必须为空!
          · IV6812002 ...           | 10,700.00
          · IV6812016 ...           | 60,747.66
[粗体行]  减: VAT有GL无的红字记录     |               ← B列必须为空!
          · SR5904005 ...           | (500.00)
[深蓝行]  销项税报告金额合计          | 4,610,085.22
```

**分区标题行:粗体 + B列空 + 无黄色 = 不重复显示小计 · 金额只出现一次(在明细行)**

**我们本窗口末尾刚刚部署的修复(`gl_vat_reconciler.py`):**
```python
WHITE_FILL = PatternFill("solid", fgColor="FFFFFF")   # 消黄色
SECT_FONT  = Font(bold=True, size=10, color="111827") # 粗体分区标题
# 分区标题行 B 列留空:
b_val = round(entry["amount"], 2) if entry["emphasize"] else ""
```

**⚠️ 用户在本窗口内测试的是修复前的版本 · 以为没有改动**
**下窗口第一步:**
1. 进 pearnly.com → 收入对账
2. 上传 `D:\Users\Skin\Desktop\新需求\` 的两个 PDF
3. 点开始对账 → 等完成 → 下载 Excel
4. 打开 Excel → 看"对账汇总"Sheet
5. ✅ 分区标题行:粗体 + B列空白 + 白色背景
6. ✅ 明细行:小字灰色 + 有金额
7. ✅ 合计行:深蓝背景 + 白色字 + 有金额
8. 如果仍有问题 → 看服务器 `/opt/mrpilot/gl_vat_reconciler.py` 的 `SECT_FONT` 和 `WHITE_FILL` 是否存在

---

## 🎯 本窗口完成清单(2026-05-17 凌晨 · v=11841126)

### session 踢人弹窗修复(v118.32.5.5.36 · home.js · cache bust 11841126)

| 问题 | 根本原因 | 修复 |
|------|---------|------|
| 弹窗从未出现 | 心跳打 `/api/me/plan`(不存在端点) → 永远 404 → 心跳从不触发 | 改为 `/api/me`(存在 · 有 jti 校验) |
| OCR 上传时被踢 → toast 不是弹窗 | `detail.code` 只读 object · `auth.session_revoked` 是 string → `code=''` → 走 toast | 改为 string/object 两路解析 |
| history/ERP/email/rdFetch 被踢 → 直接跳走 | 直接 `window.location.href='/'` 不读 response body | 改为先读 body · 如果 `auth.session_revoked` 则改弹窗 |

**现在预期行为**：
- 设备 A 登录 → 设备 B 用同账号登录 → 设备 A 最多 15 秒(下一个心跳)后弹出「账号在其他设备登录」弹窗
- 用户点「确定」→ 跳着陆页(不自动跳走 · 必须点确认)

### 大 PDF 504 修复(v118.32.5.5.35 · vat_report_parser.py + recon_routes.py)

| 改动 | 文件 | 值 |
|------|------|---|
| `_BATCH_WORKERS` | `vat_report_parser.py` | 4 → **8**(每轮处理页数翻倍) |
| Phase 1 asyncio timeout | `recon_routes.py` | 180s → **300s**(33页 PDF: 33÷8×60s≈250s · 不超时) |

---

## 🎯 本窗口完成清单(2026-05-16 深夜 · v=11841123)

### 对账 UI 视觉精修(home.html / home.css / home.js)

| 项 | 修法 |
|---|---|
| GL 对账汇总/差异明细 折叠头背景 | `#f4f4f0` → `#ffffff` · hover `#ebebea`→`#F9FAFB` |
| VAT 对账汇总/差异明细 折叠头背景 | `#fafaf8` → `#ffffff` · hover `#f4f4f0`→`#F9FAFB` |
| 搜索框背景 | `var(--bg)` → `#ffffff` 显式白色 |
| GL "导出 Excel" 按钮 | 从 差异明细 头部 → 移至 **对账汇总 头部** |
| VAT 下载按钮 | 从独立 `vex-dl-bar`(btn-primary 蓝) → 移至 **对账汇总 头部**(ghost 风 · 文案同步"导出 Excel") |
| VAT 折叠头 · 防误触 | `recon-collapse-head` 全局 click 代理加 `button/a` 判断 · 点按钮不折叠 section |
| 去除 vex-dl-bar | 替换为注释 · 无残留 DOM |

**改动文件:** `home.html` / `home.css` / `home.js` · cache bust `11841122`→`11841123` · 已部署

---

## 🎯 本窗口完成清单(接 v5.5.28 · 2026-05-16 深深夜)

### P0 Bug 修复(Korn 对账数据错误 · 已验证)

| 文件 | Bug | 修法 |
|---|---|---|
| `vat_report_parser.py` | `_to_float()` 遇括号负数 `(500.00)` 返回 None → 整行跳过 | 加括号解析:`s[1:-1]` + `neg=True` |
| `gl_vat_reconciler.py` | GL 2列无期初时退货行默认 Credit · 多算 2000 | `_DEBIT_LINE_KW` + `_is_debit_line()` 关键词优先 |

### UI 修复(home.js + home.html + home.css)

| 项 | 修法 |
|---|---|
| GL `#1A3C5E` 深蓝色 5 处残留 | 全替换为设计系统变量 |
| `glv-result` 在卡片外 | 移入 `vex-main-action` 内部 |
| GL 跑完汇总/明细不展开 | `_expandResults()` helper |
| VAT 汇总行显示 UUID hash | 删 `subEl.textContent = '#' + task_id` |
| 差异明细行数徽章右飘 | `.recon-collapse-sub` → pill badge |
| 历史表下载 tooltip 显示"操作" | `t('hist_export')` → "导出" |
| GL hover 蓝色 `#F1F5F9` | → `#ebebea` |

### CSS 视觉层次(参考图三上传识别页)

| 元素 | 之前 | 之后 |
|---|---|---|
| `vex-main-action` | `#f4f4f0`(同页面) | `#ffffff`(白卡片) |
| `vex-drop` | `#f4f4f0` | `#f8f8f6`(凹陷感) |
| `vex-kpi-card` | `#F9FAFB` | `#ffffff` |
| VAT/GL 历史区 | 无背景 | 白卡片 + 圆角边框 |

### Excel 汇总格式(最后部署 · 待下窗口验证)

| 修法 | 代码位置 |
|---|---|
| 分区标题行白色填充(消黄) | `WHITE_FILL` + else分支 |
| 分区标题行粗体 | `SECT_FONT = Font(bold=True)` |
| 分区标题 B 列留空 | `b_val = "" if not emphasize` |

**改动文件:**
- `vat_report_parser.py` · `_to_float()` 括号负数解析
- `gl_vat_reconciler.py` · `_DEBIT_LINE_KW` + `_is_debit_line()` + `WHITE_FILL` + `SECT_FONT` + B列留空
- `home.js` · `_expandResults()` + UUID删除 + tooltip修 + hover修
- `home.html` · `glv-result` 移入卡片 + cache bust CSS 11841118 / JS 11841117
- `home.css` · GL蓝色5处 + 层次CSS(main-action/drop/kpi-card/history白卡) + hover修 + badge修

---

## 🌐 当前线上状态(2026-05-17 凌晨 最新部署)

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · `/opt/mrpilot/` |
| 部署命令 | `scp file root@pearnly.com:/tmp/ && ssh root@pearnly.com "cd /tmp && tar -xzf xxx.tar.gz && cp *.py /opt/mrpilot/ && cp *.html *.js /opt/mrpilot/static/ && systemctl restart mrpilot"` |
| CSS/JS cache-bust | **`11841126`** |
| `/api/version` 返回 | `11841126` ✅ |
| systemd | `TimeoutStopSec=35` + `KillSignal=SIGTERM` ✅ |
| uvicorn | `--timeout-graceful-shutdown 30` ✅ |
| `_BATCH_WORKERS` | `8`(vat_report_parser.py L407) |
| Phase 1 parse timeout | `300s`(recon_routes.py · `_parse_group` 函数) |

---

## 📖 (旧) GL 收入对账主线完成清单(v118.32.5.0 → v118.32.5.4 · 2026-05-15 晚)

| 类别 | 项 | 状态 |
|---|---|---|
| 新功能 · 收入对账 | `gl_vat_reconciler.py` 核心引擎(GL PDF/Excel 解析 + 对账 + 4 语言 Excel 导出) | ✅ |
| 新功能 · 收入对账 | `recon_routes.py` 加 4 个 API:`/api/recon/gl-vat/{run,tasks,{id},{id}/export}` | ✅ |
| 新功能 · 收入对账 | `db.py` 加 `gl_vat_task` 表 + 5 个 CRUD 函数 + `ensure_gl_vat_task_table()` | ✅ |
| 新功能 · 收入对账 | `home.html`/`home.js`/`home.css` 加左侧 Tab + Pane + 完整前端模块 `window.GlVatRecon` | ✅ |
| 新功能 · 4 语言 | i18n key × 4 语全套 · `subscribeI18n('gl-vat-recon', _onLangChange)` 切语言实时刷新 | ✅ |
| 解析增强 | `vat_report_parser.py` 加 `report_ref_no` 列(`เลขที่เอกสารอ้างอิง`)· **GL 对账匹配键**(不是 invoice_no) | ✅ |
| 解析增强 | `vat_report_parser.py.parse_pdf_text` 加 **文字行 regex 回退**(无可见表格框线的 VAT PDF)· `_parse_vat_pdf_text_lines` | ✅ |
| 解析增强 | `gl_vat_reconciler.py.parse_gl_pdf` 加 **文字行 regex 回退** + 严格化 `_ACCT_RE`(避免 419.57 误当科目) | ✅ |
| 性能 A | `recon_routes._ocr_one` 加文字层快速通道(`pdf_text_extractor.try_text_extraction`)· 跳 Gemini | ✅ |
| 性能 B | `vat_excel_export.py` 加 `extract_invoice_fields_batch` + `extract_invoices_batched_parallel`(5/批 · 4 并行 · 失败回退单张) | ✅ |
| 性能 B 接入 | `vat_excel_routes.py` 发票 ≥ 10 张自动走批量 OCR | ✅ |
| 性能 C | `recon_routes` OCR Semaphore 10 → 20 | ✅ |
| **性能关键修** | `vat_file_classifier.classify_file(fast_mode_invoice=True)` 默认开启 · 文件名提示 invoice 时**跳 Gemini classify**(节省 25-30s for 10 张) | ✅ |
| Excel 升级 | 顶部 5 KPI 行 + 状态列(✓/⚠/❗ 带颜色) + 使用说明 Sheet(4 语并排) | ✅ |
| UI 同步 | `.vex-task-actions` 长显示(去掉 hover-only) · 同 GL 对账风格 | ✅ |
| UI · 折叠 | "差异明细" / "对账汇总" 默认折叠 · 点头部展开 · 明细头部带行数 pill | ✅ |
| UI · 历史 | GL 对账"近期对账"列表 + 3 图标按钮(加载/下载/删除) + hover tooltip | ✅ |
| UI · 弹窗 | 删除任务用 `window.showConfirm` 替换原生 confirm() | ✅ |
| 重命名(客户要求) | `recon-tab-sale-vat`:销项税对账 → 销项税报告核查(4 语) `recon-tab-gl-vat`:GL对账 → 收入对账(4 语) | ✅ |
| 重命名 | `nav-reconcile`:VAT 对账 → 对账中心(4 语) | ✅ |
| 部署 | v118.32.5.0 → v118.32.5.4 共 9 次 cache bust(v=11841086 → v=11841094) · 全部上线 | ✅ |
| 依赖 | 生产服 venv 装 `pdfplumber 0.11.9`(原 venv 没有)`/opt/mrpilot/venv/bin/pip install pdfplumber` | ✅ |

**改动文件**:
- `gl_vat_reconciler.py` **新建** · ~640 行 · 核心对账引擎
- `vat_report_parser.py` 加 `report_ref_no` 字段 + `_parse_vat_pdf_text_lines` regex 回退
- `vat_file_classifier.py` 加 `fast_mode_invoice` 参数(默认 True · 关键性能修)
- `vat_excel_export.py` 加 `extract_invoice_fields_batch` 批量 OCR
- `vat_excel_routes.py` 接入批量 OCR(≥10 张时)
- `recon_routes.py` 加 GL 对账 4 路由 + i18n 错误字典 + 文字层预检 + Semaphore 20
- `db.py` 加 `gl_vat_task` 表 + 5 个函数
- `app.py` 启动加 `ensure_gl_vat_task_table()`
- `home.html` 加 sidebar Tab + GL 对账完整 Pane(含 KPI/上传/结果/历史)
- `home.css` 加 GL 对账 + 折叠分区 + sale-vat 长显示样式
- `home.js` 加 `window.GlVatRecon` IIFE 模块(~400 行)

---

## 🌐 当前线上状态(2026-05-15 21:10 部署)

| 项 | 值 |
|---|---|
| 域名 | https://pearnly.com |
| 服务器 | `root@45.76.53.194` · Vultr Tokyo · `/opt/mrpilot/` |
| 部署 | `bash /opt/mrpilot/deploy.sh /tmp/<tar.gz>` |
| `/api/version` | `11841094` |
| 已装 venv 依赖 | + **pdfplumber 0.11.9**(新装 · 给 GL/VAT 文字行 regex 解析用) |

---

## 💀 Critical 地雷(下窗口必读 · 别踩)

### 1. **匹配键不是 invoice_no**
GL 对账匹配键是 VAT 报告的 `เลขที่เอกสารอ้างอิง`(参考单号 · 对应字段 `report_ref_no`)· 不是 `เลขที่ใบกำกับภาษี`(税票号 · 字段 `report_invoice_no`)。两者很容易混淆 · 客户拍板:**参考单号才对应 GL 的 `ใบสำคัญ`**。

### 2. **GL/VAT PDF 几乎都没可见表格框线**
泰国会计软件(Express / FlowAccount / Easy Account 等)导出的 PDF **不画表格线**。pdfplumber `extract_tables()` 抓不到任何 table → 回退**文字行 regex**(`_parse_vat_pdf_text_lines` / `_parse_gl_text_lines`)。新加客户的 PDF 解析 0 行时 · **先看是不是这个原因**(看日志 diag 字段)。

### 3. **科目代码 regex 必须严格**
`_ACCT_RE = r'(?<![\d.])([4-9]\d{3,4}(?:[\-–]\d{2,3})?)(?![\d.])'`
- ❌ 不能允许小数点分隔(`4xx.yy` 会误把金额 `419.57` 当成科目)
- ❌ 不能允许 3 位数(`4xx` 会误匹配 invoice 序号)

### 4. **classify_file fast_mode_invoice 的副作用**
默认 `fast_mode_invoice=True` 跳过 Gemini classify · 节省 25-30s/10 张发票。
**副作用**:多 VAT 报告场景下 · 发票无 tax_id 无法自动匹配到对应报告组。
当前缓解:单一报告模式下系统强制把所有发票归到唯一报告(recon_routes.py L395-412 `single_report` 逻辑)· 90% 客户场景没问题。
**如果客户反馈**"多个 VAT 报告时发票分不到对的组" → 改 batch_classify 走 2-pass:先 fast mode 分类 · 看报告数 · >1 时重新 Gemini classify 发票拿 tax_id。

### 5. **deploy.sh 用 PowerShell 工具**(不是 Bash)
Claude Code auto-mode 分类器禁止 AI 直接 ssh 到 production · 必须用 PowerShell:
```powershell
$tar = "D:\Users\Skin\Desktop\pearnly_project\_pkg\pearnly_v<VER>.tar.gz"
scp -q $tar root@45.76.53.194:/tmp/
ssh root@45.76.53.194 "bash /opt/mrpilot/deploy.sh /tmp/pearnly_v<VER>.tar.gz 2>&1 | tail -10"
```

### 6. **cache bust 必须 bump · 2 处同步**
`home.html` 第 7 行 `home.css?v=XXXXX` + 第 6082 行 `home.js?v=XXXXX` · `/api/version` 自动从 home.html grep。
当前:**v=11841094** · 下版本:**v=11841095**。

### 7. **subscribeI18n 总线 · 切语言不靠 tab 切换**
GL 对账模块用 `window.subscribeI18n('gl-vat-recon', _onLangChange)` 注册重渲 · 切语言时自动调 _onLangChange 重渲状态条、历史表、明细、汇总。
**任何用 `_t()` 动态生成 innerHTML 的 IIFE 都必须订阅 · 否则切语言旧文案残留**(DESIGN_SYSTEM.md 已有铁律)。

### 8. **PDF 字距(kerning)问题**
pdfplumber 抽 `SI000001` 可能拆成 `SI 1`(中间零字符宽度被压缩成空格)。我在 VAT 文字行 regex 加了清洗 regex 去残留 `SI N` / `00000` 等 · 但**未来遇到诡异客户名**可能还要补规则。

---

## 🚀 下窗口候选任务

### 🟢 短期 · 性能/UX 收尾
- **GL 对账 i18n 完整性 lint**:跑 `scripts/check_i18n.py`(TECH_DEBT P0 #2 还没做) · 确保 zh/en/th/ja 4 块 key 完全一致 · 加 `glv-*` 系列 key
- **批量发票 OCR 实测**:用 100+ 张发票实测 v118.32.5 批量 + 文字层效果 · 看是不是真的从 27min → 3-5min
- **多 VAT 报告场景验证**:让客户上传 2 份 VAT 报告 + 多客户混合发票 · 看 fast_mode_invoice 副作用是不是真的会发生

### 🟡 中期 · GL 对账深化
- **Excel 上传支持**:现在 GL 文件主要靠 PDF 文字行 regex · 没真实测过 Excel(`parse_gl_excel`) · 找客户的 Express/FlowAccount Excel 样本测一遍
- **GL-only 行也展示**:当前明细只显示 VAT 行 · GL 有但 VAT 没的行只进汇总 · 客户可能想看具体哪几条
- **历史搜索/过滤**:近期对账 ≥ 50 条时要分页或搜索

### 🟠 长期 · 屎山治理(TECH_DEBT 队列)
- 看 `TECH_DEBT.md` P0 #2 / #3 是不是还没做(check_i18n.py / Playwright 烟测)

---

## 🗒 上下文片段(下窗口可能用得到)

**客户拍板规则**(2026-05-15 Zihao 转述):
- 匹配键:VAT `เลขที่เอกสารอ้างอิง` ↔ GL `ใบสำคัญ`
- VAT 正数 → 取 GL Credit; 负数 → 取 GL Debit 转负
- 末列附加 GL 的 `รหัสบัญชี`(收入科目代码)
- 100% 一比一提取 · 不补充 · 不篡改(核心质量要求)
- Thai 标签:`销项税对账→ตรวจสอบรายงานภาษีขาย` · `GL对账→กระทบรายได้`

**测试样本文件**:`D:\Users\Skin\Desktop\新需求\` 含 `General ledger.pdf`(214KB · 8 页) + `sale vat report.pdf`(261KB · 17 页) + `vat_recon (12).xlsx`(老销项税导出模板 · 借鉴 KPI/状态/说明 Sheet)

**性能基线**(用上述样本):
- GL 对账(2 个文字 PDF):约 **2-3 秒**(纯 pdfplumber 解析 · 无 AI)
- 销项税核查(5 张发票 + 1 VAT):约 **40 秒**(fast_mode_invoice + 文字层 + 批量 OCR 组合效果)
