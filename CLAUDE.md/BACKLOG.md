# 📋 BACKLOG · Pearnly 待办清单

> **最近更新**:2026-05-17 · cache bust **v=11841136** · 银行对账 v2 全面重建(Statement vs GL · 3层匹配 · 4语言Excel导出) · 对账中心横向tab UI优化
> **上次**:NAV-IA 重构 · 侧边栏分组 · 对账中心 tab 样式优化 · Git 自动部署流程建立

## ✅ 已完成 · v118.33.6 · 银行对账 v2

- [x] `bank_recon_v2.py` · 全新银行对账核心引擎
  - KBank / BBL / KKP / KTB / SCB / generic 自动识别 + 专属解析器
  - GL 支持 Excel (.xlsx/.xls) 和 PDF (pdfplumber → Gemini 兜底)
  - 3 层日期匹配：L1 精确日期 · L2 ±3天容差 · L3 仅金额
  - 多文件合并 + 去重
  - 多 GL 科目自动检测 · 用户下拉选择
  - 对账公式验证：GL 期末 ± 调整项 = 账单期末
  - 4-sheet openpyxl Excel 导出 · 全 i18n (th/en/zh/ja) 表头
- [x] API routes `/api/recon/bank-v2/*` · 落库 `bank_recon_v2_task` 表
- [x] DB · `ensure_bank_recon_v2_table()` 幂等建表
- [x] Frontend · 双上传区(账单 + GL) · 统计卡 · 对账公式框 · 可过滤明细表 · 历史记录
- [x] i18n · 40+ 个 brv2- 前缀 key · zh/en/th/ja 全覆盖
- [x] 旧 OCR 银行对账 UI 清除(DOM 瘦身)

## 📌 待办



---

## 🔴🔴 下窗口第一优先 · NAV-IA Phase 5 收尾 · 自动化并入集成

> **背景**:Phase 5(v118.33.5.0 · 2026-05-15)当时标为 ✅ 但漏了关键一步 — 「自动化」侧边栏入口没删 · 集成页的配置按钮还在跳自动化。本次完整收尾。
> **拍板方案**:右侧抽屉(Drawer)模式 · 点集成页配置按钮 → 右侧滑入配置面板 · 不离开集成页
> **银行对账**:自动化里的 bank tab 功能迁移到「对账中心」· 用抽屉承接 · 自动化不再有银行入口

---

### 📋 现状分析(已排查确认)

**集成页现有卡片 vs 配置按钮去向:**

| 卡片 | 配置按钮现在做什么 | 目标行为 |
|------|-----------------|---------|
| Google Drive | 已有内联展开(✅ 不用改) | 保持 |
| Google Sheets | 已有内联展开(✅ 不用改) | 保持 |
| Gmail 抓取 | `switchAutomationTab('email')` → 跳自动化 | 改为打开右侧抽屉 |
| LINE Bot | `switchAutomationTab('linebot')` → 跳自动化 | 改为打开右侧抽屉 |
| 文件夹监听 | `switchAutomationTab('folder')` → 跳自动化 | 改为打开右侧抽屉 |
| ERP 对接 | `switchAutomationTab('erp')` → 跳自动化 | 改为打开右侧抽屉 |
| **智能提醒** | **集成页缺失此卡片** | 新增卡片 + 抽屉 |

**对账中心银行对账现状:**
- 集成页**没有**银行对账卡片(正确 · 银行对账是核心业务不是集成)
- 对账中心有「银行对账」区域 · 上传按钮 → `_gotoBankUpload()` → `routeTo('automation')` + `switchAutomationTab('bank')` → 跳走
- 自动化 bank tab(L17253-18262)是真正的功能体(上传队列 + 会话详情 + 事务匹配)

---

### 🛠 执行步骤(顺序固定 · 可逐步验证)

#### Step 1 · 集成页加通用右侧抽屉组件
**文件**: `home.html` + `home.css` + `home.js`

HTML 结构(加在 `</body>` 前):
```html
<div id="int-drawer-overlay" style="display:none;"></div>
<div id="int-drawer" class="int-drawer">
  <div class="int-drawer-header">
    <button id="int-drawer-close">←</button>
    <span id="int-drawer-title"></span>
  </div>
  <div id="int-drawer-body"></div>
</div>
```

CSS(加到 home.css):
```css
.int-drawer {
  position: fixed; top: 0; right: -480px; width: 480px; height: 100vh;
  background: #fff; z-index: 10000; box-shadow: -4px 0 24px rgba(0,0,0,.12);
  transition: right .25s ease; display: flex; flex-direction: column;
}
.int-drawer.open { right: 0; }
#int-drawer-overlay { position:fixed; inset:0; z-index:9999; background:rgba(0,0,0,.3); }
#int-drawer-body { flex:1; overflow-y:auto; padding:20px; }
@media(max-width:600px) { .int-drawer { width: 100vw; } }
```

JS 函数(加到 home.js · 集成模块 IIFE 内):
```javascript
function openIntegrationDrawer(tab, title) {
    document.getElementById('int-drawer-title').textContent = title;
    document.getElementById('int-drawer-body').innerHTML = '';
    document.getElementById('int-drawer').classList.add('open');
    document.getElementById('int-drawer-overlay').style.display = 'block';
    // 复用现有 panel 加载函数
    const loaders = {
        linebot: window._loadLineBotPanel,
        folder:  window._loadFolderWatcherPanel,
        email:   window._loadEmailIngestPanel,
        erp:     window._loadErpPanel,       // 见 Step 3 说明
        alert:   window._loadNotificationsPanel,
    };
    if (loaders[tab]) loaders[tab]('int-drawer-body');
}
function closeIntegrationDrawer() {
    document.getElementById('int-drawer').classList.remove('open');
    document.getElementById('int-drawer-overlay').style.display = 'none';
}
document.getElementById('int-drawer-close').addEventListener('click', closeIntegrationDrawer);
document.getElementById('int-drawer-overlay').addEventListener('click', closeIntegrationDrawer);
```

#### Step 2 · 集成页配置按钮改调 openIntegrationDrawer
**找到集成页(#page-integrations 或 #page-integration)里各配置按钮的 click 处理:**

```javascript
// 改前:
document.getElementById('btn-int-linebot-config').addEventListener('click', () => {
    routeTo('automation'); setTimeout(() => switchAutomationTab('linebot'), 80);
});

// 改后:
document.getElementById('btn-int-linebot-config').addEventListener('click', () => {
    openIntegrationDrawer('linebot', t('int-name-line'));
});
```
四个按钮(linebot / folder / email / erp)都要改。

#### Step 3 · ERP 配置抽屉特殊处理
自动化的 erp tab 调 `loadErpEndpoints()` + `loadErpLogs()` · 这两个函数可直接在抽屉 body 里调用:
```javascript
window._loadErpPanel = function(containerId) {
    // 把原 #page-auto-erp 的 innerHTML 移到 container 里
    // 或直接 clone 节点
};
```
如果 erp tab 内容与集成页「ERP 对接」功能重叠太多 · 优先复用现有 ERP 对接卡片逻辑 · 不强制搬 tab。

#### Step 4 · 集成页补「智能提醒」卡片
在集成页(#page-integrations)「收票渠道」区块后面新增「自动化」区块:
```html
<div class="int-section-title">自动化 & 提醒</div>
<div class="integration-row" id="int-row-alert">
  <div class="int-icon">🔔</div>
  <div>
    <div class="int-name" data-i18n="auto-alert-title">智能提醒</div>
    <div class="int-desc" data-i18n="auto-alert-desc">异常单/大额单第一时间推 LINE</div>
  </div>
  <button class="btn-int-config" id="btn-int-alert-config" data-i18n="int-btn-config">配置</button>
</div>
```
点配置 → `openIntegrationDrawer('alert', t('auto-alert-title'))`

**i18n 新增(4 语):** `auto-alert-desc` · `int-section-automation`

#### Step 5 · 对账中心银行对账改用抽屉
**文件**: `home.js`

```javascript
// 改前:
function _gotoBankUpload() {
    routeTo('automation');
    setTimeout(() => switchAutomationTab('bank'), 80);
}

// 改后:
function _gotoBankUpload() {
    // 在对账中心内打开右侧抽屉 · 复用银行对账面板
    _openBankDrawer(null);  // null = 新上传
}

function _openBankDrawer(sessionId) {
    openIntegrationDrawer('bank', t('recon-bank-title'));
    if (sessionId) {
        // 加载特定会话
        if (window._loadBankReconPanel) window._loadBankReconPanel('int-drawer-body', sessionId);
    } else {
        if (window._loadBankReconPanel) window._loadBankReconPanel('int-drawer-body', null);
    }
}
```

`_gotoBankSession(sessionId)` 同理改调 `_openBankDrawer(sessionId)`。

**注**: `_loadBankReconPanel` 原来注入到 `#auto-bank` 容器 · 改成接受 containerId 参数即可复用。

#### Step 6 · 删除自动化侧边栏入口
**文件**: `home.js` + `home.html` + `home.css`

清理清单:
1. `VALID_ROUTES` 删 `'automation'`
2. `routeTo('automation')` 所有调用点改向(bank 改 Step 5 · 其他查是否还有)
3. `loadAutomationPage()` 函数 + `switchAutomationTab()` 整段可保留(因为 Step 1-5 的抽屉还在调 panel 函数)· 但可以加注释标记为 deprecated
4. `home.html` 删 sidebar 里 `data-route="automation"` 的 nav-item
5. `home.js` `applySidebarVisibility()` 删 automation 相关 group 显示逻辑
6. i18n 4 语字典删 `nav-automation` / `nav-group-automation` 对应的 key(4 × 2 = 8 个地方)
7. `home.css` 删 `.nav-group-automation` 样式(如有)
8. `#page-automation` DOM 可暂时保留(防万一有遗漏引用)· 加 `display:none`

#### Step 7 · 验证 + 部署
验证清单:
- [ ] 集成页 → LINE Bot「配置」→ 右侧抽屉滑入 LINE Bot 设置面板
- [ ] 集成页 → 文件夹监听「配置」→ 抽屉
- [ ] 集成页 → ERP 对接「配置」→ 抽屉
- [ ] 集成页 → 智能提醒「配置」→ 抽屉
- [ ] 对账中心 → 银行对账「上传」→ 抽屉(不跳走)
- [ ] 对账中心 → 点历史会话 → 抽屉打开对应会话
- [ ] 侧边栏:「自动化」入口消失
- [ ] 侧边栏剩余:首页 / 销项管理▾ / 进项管理▾ / 客户 / 异常 / 集成(底部)
- [ ] 手机端抽屉宽度 100vw

**cache bust**: 11841126 → 11841127

---

## 🔴 下窗口第二优先 · Excel 差异明细 Sheet 表头美化

**任务**: `gl_vat_reconciler.py` → `ws1`(差异明细 Sheet)表头样式升级

**截图现状**:
- Row 1 KPI label(总笔数/完全匹配/有差异/GL未找到/差异金额合计)：无填充 · 小字
- Row 2 KPI value：有数值 · 红色边框框住
- Row 4 主表头(状态/单据号/日期/客户名称...)：深蓝背景 + 白字 · 基础样式已有

**设计目标**：对应颜色填充 · 字体加粗加大 · 整体漂亮专业

**推荐方案**：
- KPI label行(Row 1)：`#EFF6FF` 浅蓝底 · `#1D4ED8` 蓝色字 · 粗体 11px · 居中
- KPI value行(Row 2)：白底 · 数值 14px 粗体 · 颜色按状态(完全匹配绿`#16A34A` · GL未找到橙`#D97706`)
- 主表头行(Row 4)：保持/升级深蓝 · 字体 10→11px · 行高 22 · 白字加粗

**文件**:`gl_vat_reconciler.py` 搜 `_write_ws1` 或 `ws1` Sheet 写入函数 · 加/改 PatternFill/Font 常量

**验证**：pearnly.com → 收入对账 → 上传 `D:\Users\Skin\Desktop\新需求\` 两 PDF → 对账汇总头部"导出 Excel" → 看 差异明细 Sheet

---

## 🟡 下窗口第二优先 · 必须先验证(客户 Korn 要求)

### Excel 对账汇总格式验证

**客户要求(Korn 原话):**
- `ตัวเลขแสดงถูกหมดแล้ว` ✅ 数字已全部正确
- `ลบช่องสีเหลืองออกแค่นั้น ตัวเลขเยอะ สับสน` = **只需删掉黄色格子，数字太多太乱**

**Korn 期望的 Excel 格式(ws2 / 对账汇总 Sheet):**
```
[深蓝]  ยอดรวมตามบัญชีแยกประเภท          | 4,548,637.56
[粗体]  หัก: รายการเครดิตที่ไม่มีในรายงาน  |              ← B 列留空!
[普通]      · IV6812003 · 06/12/68 ...    | (10,500.00)  ← 金额只在明细行
[粗体]  บวก: รายการเดบิตที่ไม่มีในรายงาน   |              ← B 列留空!
[普通]      · SR5904006 · 04/12/68 ...    | 1,000.00
...
[深蓝]  ยอดรวมตามรายงานภาษีขาย           | 4,610,085.22
```

**关键:**分区标题行(หัก/บวก 开头)B 列必须为空 · 金额仅在缩进明细行显示 · 无黄色

**我们已做的修复(本窗口末尾 · 刚部署):**
- `WHITE_FILL` 显式白色填充 → 消除黄色 ✅
- `SECT_FONT` 粗体分区标题 ✅
- `b_val = "" if not emphasize else amount` → B 列留空 ✅

**⚠️ 下窗口第一步: 验证修复是否生效**
1. 用 `D:\Users\Skin\Desktop\新需求\` 里的两个 PDF 重新跑对账
2. 下载 Excel · 查 ws2(对账汇总)
3. 分区标题行:粗体 + B 列空 + 无黄色 → **✅ 完成**
4. 如仍有问题:在 `gl_vat_reconciler.py` 搜 `SECT_FONT` 和 `WHITE_FILL` 确认代码已部署

---

## ✅ 2026-05-16(深夜) 本窗口完成(v118.32.5.5.30 · UI 精修 · cache bust 11841123)

- [x] GL 折叠头 + VAT 折叠头背景 → `#ffffff` 纯白 · hover → `#F9FAFB`
- [x] 搜索框背景 → `#ffffff` 显式白色
- [x] GL "导出 Excel" 按钮从差异明细头部移至**对账汇总头部**
- [x] VAT 下载按钮从独立蓝色 bar 移至**对账汇总头部**(ghost 风 · 同款文案)
- [x] VAT `recon-collapse-head` 全局 click 代理加 button/a 防误触判断
- [x] 去除 `vex-dl-bar` DOM 元素(替换为注释)
- [x] JS 3 处 `vex-dl-bar` 引用改为直接操作 `vex-download` 元素

---

## ✅ 2026-05-16(深深夜) 本窗口完成(接 v5.5.28 · 多项修复)

### Bug 修复(P0 · Korn 对账数据错误)
- [x] `vat_report_parser.py` · `_to_float()` 加括号负数解析 `(500.00)` → `-500.0`
- [x] `gl_vat_reconciler.py` · `_DEBIT_LINE_KW` + `_is_debit_line()` · 退货关键词判 Debit

### UI 修复
- [x] GL `#1A3C5E` 深蓝 5 处全清除
- [x] `glv-result` 移入 `vex-main-action` 白卡片内
- [x] GL 对账跑完自动展开汇总/明细
- [x] VAT 汇总行 UUID hash 删除
- [x] 差异明细行数徽章 pill 样式
- [x] 历史表下载按钮 tooltip "导出"
- [x] GL 折叠头 hover 蓝色修正

### CSS 层次修复(参考上传识别页)
- [x] 主操作卡片 `#f4f4f0` → `#ffffff`(白)
- [x] 上传格子 `#f4f4f0` → `#f8f8f6`(凹陷)
- [x] KPI 卡片 `#F9FAFB` → `#ffffff`
- [x] VAT/GL 历史区加白卡片样式

### Excel 汇总格式(最后部署 · 待验证)
- [x] `WHITE_FILL` 消除黄色
- [x] `SECT_FONT` 分区标题粗体
- [x] 分区标题 B 列留空(金额只在明细行)

---

## ✅ 2026-05-16(深夜) 本窗口完成(v118.32.5.5.26 → v118.32.5.5.28 · 3 个微版本)

### VAT 预览面板数据接通 + UI 清理
- [x] **v118.32.5.5.26** `_fetchAndFillVexPreview` 函数:对账后拉 `/api/vat_excel/tasks/{id}` JSON → 填充 vex-summary/detail-collapse 全量差异行(无截断 · 可滚动) + `app.py` 4 语 release_notes
- [x] **v118.32.5.5.27** 砍掉"对账完成"绿色横幅(`vex-result` + `_watchVexResult` + i18n key + CSS) · 下载按钮移至极简 `vex-dl-bar`
- [x] **v118.32.5.5.28** 蓝色 `#DBEAFE`→暖灰 · 预览面板边框统一 `var(--line)` · "完成"颜色→`var(--success)` · GL 汇总/明细顺序互换

### 下窗口优先
- [ ] 🟡 **GL 收入对账预览面板数据填充** — 骨架在 `glv-preview-panel` · 接 `/api/recon/gl-vat/tasks/{id}` JSON · 套路同 VAT v5.5.26

---

## ✅ 2026-05-16(晚) 本窗口完成(v118.32.5.5.16 → v118.32.5.5.25 · 10 个微版本)

### NAV-IA 视觉 Gap + 首页内容
- [x] **v118.32.5.5.16** 7 处硬编码蓝色全替换 + 首页 dashboard(4 KPI + 快速操作 + 最近动态)

### 版本更新弹窗(新铁律 #6)
- [x] **v118.32.5.5.17** `static/version-banner.js` 新文件 · 30s 轮询 · 顶部条 + modal + 4 语 + snooze
- [x] `/api/version` 加 `release_notes` 4 语字段
- [x] CLAUDE.md 铁律 #6:每次部署写 4 语 release_notes

### 部署 graceful 三层
- [x] **v118.32.5.5.18** systemd `TimeoutStopSec=35` + uvicorn `--timeout-graceful-shutdown 30` + `_recover_interrupted_tasks()` lifespan

### 对账对称化 + 批量删
- [x] **v118.32.5.5.19** 销项税核查加 summary/detail collapse · 收入对账加 glv-preview-panel 骨架
- [x] **v118.32.5.5.20** GL VAT 批量删后端 API + 两个对账历史表前端多选 UI
- [x] **v118.32.5.5.21** version-banner reload bug 修 + 文案 4 语标准化
- [x] **v118.32.5.5.22** Gmail 风格 thead 批量模式 + 表头列宽错位修
- [x] **v118.32.5.5.23** 收入对账清单面板改 vex-pp-grid 两栏
- [x] **v118.32.5.5.24** 删老 pn-version-banner 屎山(116 行 JS + 86 行 CSS) + vex-pp-grid 宽度对齐
- [x] **v118.32.5.5.25** `_renderGlvPreviewPanel` 1:1 复刻(搜索/清除/X 删/分页) + `_reset()` 同步刷新 + `_removeFile` 直写 STATE

### 下窗口优先(已由 v5.5.26-28 解决)
- [x] ~~🔴 **销项税核查预览数据填充**~~ — v5.5.26 已完成 · 全量差异行 · 5 KPI 卡

---

## ✅ 2026-05-16(中) 本窗口完成(17 个微版本)

### Admin SPA 用户管理补全(NAV-IA Phase 8 收尾)
- [x] **v118.44.1.0** 抽屉 7 section + 3 tab + 升级 modal · 移植自 home.js L20600-L22400
- [x] **v118.44.1.1** 封停/解封/级联删除/风控完整版/批量封禁
- [x] admin-i18n.js zh+th 49→130 key

### GL/VAT 多 ERP 兼容
- [x] **v118.32.5.5.0-5** GL 兼容 2/3 列 + 无日期延续行 + 余额变化判借贷 · 科目 4-7 位 · 切粘连 · ref_no 严格化
- [x] **v118.32.5.5.8-9** BAKELAB pypdf 字符序乱 fallback · 销项税核查发票 text_path 快路径(24s→11s)
- [x] **v118.32.5.5.11** Excel 汇总 Sheet 2 展开单据明细(Korn 反馈)

### Session 1 账号 1 设备 + 反薅
- [x] **v118.32.5.5.10/12/13** JWT jti + users.active_jti + ALTER commit=True + 15s 心跳 + focus 立即 check
- [x] **v118.32.5.5.14** Trial 100/7d → 30/3d(Korn 🅱)
- [x] **v118.32.5.5.15** 着陆页 4 真公司名换行业类目假名(4 语)

### UI 系统化修
- [x] **v118.32.5.5.2** 4 处 alert→showToast · filename 500 修(RFC 5987)
- [x] **v118.32.5.5.6/7** z-index 批量修 13 处(modal/overlay 全升 10000)

### 待用户测试确认
- [ ] session 实时踢人(15s 内或 focus 立即)
- [ ] admin SPA 抽屉 / 3 tab / 4 modal / 风控批量封禁
- [ ] z-index 13 处批量修(除"添加员工"已确认)

### 待 Korn 回复
- [ ] 「5 人轮流用 1 账号」想堵法选 🅰/🅱/🅲/不堵
- [ ] 多 ERP 真实样本(Express / Mr.ERP / FlowAccount)收集

---

## ✅ GL 对账主线(2026-05-15 晚 · 收官)

> **PRD 文件**:`C:\Users\skin3\.claude\plans\10-vat-2-800-vat-declarative-cocoa.md`
> **客户原始需求**:`D:\Users\Skin\Desktop\新需求\新需求.md`(Thai/中双语)

| 项 | 工时 | 状态 |
|---|---|---|
| 核心引擎 + API + DB + 前端完整链路 | ~4 h | ✅ v118.32.5.0(v=11841086) |
| Thai 客户重命名 + 4 语 i18n | ~0.5 h | ✅ v118.32.5.1(v=11841087) |
| VAT PDF 文字行 regex 回退(无表格框线场景) | ~1 h | ✅ v118.32.5.2(v=11841089) |
| UI 同 vex 系统对齐 + 历史表 + 折叠区 + showConfirm | ~1.5 h | ✅ v118.32.5.3(v=11841092) |
| 销项税性能修(`fast_mode_invoice=True` 跳冗余 classify · 3min→40s) | ~0.5 h | ✅ v118.32.5.3(v=11841093) |
| Excel 升级:5 KPI + 状态列 + 使用说明 Sheet(借鉴 vat_recon) | ~0.5 h | ✅ v118.32.5.4(v=11841094) |
| 生产服 venv 装 pdfplumber 0.11.9 | ~5 min | ✅ |

**总工时**:~8 小时 · 一窗口落地。

**遗留小项**(下窗口可选):
- 🟢 GL Excel 上传测真实样本(目前主要 PDF 测过)
- 🟢 多 VAT 报告场景验证 `fast_mode_invoice` 副作用
- 🟢 `scripts/check_i18n.py` lint(TECH_DEBT P0 #2)· 验证 `glv-*` 系列 key 4 语完整性
- 🟡 GL-only 行也展示在明细(目前只在汇总)

---

## 🧭 NAV-IA 平行主线任务队列(2026-05-15 拍板 · P1 优先级)

> **唯一 PRD**:`NAV_IA_PRD.md`
> **基准实物**:`D:\Users\Skin\Desktop\pearnly_project\pearnly_nav_prototype_final.html`
> **接力规则**:任何窗口可挑下一个 ⏸️ Phase 接干 · 不抢 P0-VAT 资源

### Phase 0 · 文档体系建立 ✅(0.5 d · 2026-05-15)
- ✅ 写 NAV_IA_PRD.md
- ✅ CLAUDE.md 加「🧭 导航 IA 铁律」段
- ✅ STATE_PEARNLY.md 加 NAV-IA 平行主线段
- ✅ BACKLOG.md 加本队列(本节)
- ✅ MODULE_ROADMAP.md 加 NAV-IA 横切模块
- ✅ DESIGN_SYSTEM.md 加 §18 头像下拉菜单组件

### Phase 1 · 顶栏三件套落地 ✅(实际 ~1 d · 2026-05-15 上线 v118.33.1.0)
**影响文件**:`home.html`(+220 行) · `home.css`(+243 行) · `home.js`(+431 行)

**A. 头像下拉菜单** ✅
- [x] `home.html` topbar 加 `.avatar-wrap` + `.avatar-popup`(9 项 · 全内联 SVG · home.html 未引 Tabler)
- [x] `home.css` 末尾追加 · 变量映射 prototype `--surface/--text/--border` → home.css `--card/--ink/--line`
- [x] `home.js` 末尾新 IIFE 段 · `applyRoleVisibility` 复用 `isSuperAdmin / canManageTeam / shouldHideMoney` 原子函数 · `_isInTestWhitelist` 复刻 home.js:24821 3 条件(URL/localStorage/user_id 硬编码 · 因 `/api/me` 后端无 `is_test_whitelist` 字段)
- [x] 9 个 i18n key 4 语全(写入顺序 th→en→zh→ja)
- [x] loadAll hook 在 `applySidebarVisibility()` 后追加 `applyRoleVisibility() + renderAvatarMenu(u)`

**B. 顶栏搜索框** ✅
- [x] `home.html` 客户切换器左边插入 `.topbar-search`(灰底 + ⌘K kbd · OS 探测 `body.is-windows` 切 Ctrl K 显示)
- [x] `home.css` 加样式 + 响应式(< 800px 缩图标 · **< 600px 完全隐藏**)
- [x] 点击 / Enter / Space 触发 `window.openCmdk()`

**C. Cmd+K 命令面板** ✅
- [x] `home.html` toast 后插入 `.cmdk-mask + .cmdk`(13 跳转项 + 4 切语言 · 含「即将」灰显项 4 个)
- [x] `home.css` 加 `.cmdk-*` 样式 · z-index 9100(避开现有 modal 0-9000)
- [x] `home.js` IIFE 段:`openCmdk / closeCmdk / _cmdkFilter / _cmdkSetFocus / _cmdkMoveFocus / _cmdkActivate / _initCmdk` · 全局 `⌘K | Ctrl+K` + ESC 双关链(cmdk → avatar-popup)
- [x] 8 个 i18n key 4 语全
- [x] cmdk locked 项(dashboard/vouchers/receivables/automation)点击 toast 「即将上线」

**D. 顺带做的 P0 屎山修复**(TECH_DEBT §2)✅
- [x] 删 `showToast` 重复定义旧版(home.js:13461)· 276 调用点全兼容新版(line 14894)
- [x] 写 TECH_DEBT.md(屎山治理路线图 + 已修清单 + 新代码标准 + §4.5 部署铁律的"系统层例外")
- [x] CLAUDE.md 加「🧹 屎山治理铁律」段(在 §4 语并重之后)

**E. 收尾** ✅
- [x] cache bust 11841061 → 11841062(home.html 中 home.css?v= + home.js?v= 两处 · /api/version 自动 grep 不用改 app.py)
- [x] 部署 v118.33.1.0(scp + ssh deploy.sh · PowerShell 工具 · 复刻 settings.local.json line 44 同款格式)
- [x] 验证 https://pearnly.com/api/version → `{"version":"11841062"}` ✓
- [x] 本地 tar.gz 自动删

**验收**(skin 账号已给短版必测清单 · 5 项 · 每项 ≤30 秒)

### Phase 2 · sidebar 重复入口清扫 ✅ 完成(实际 ~0.5 d · 2026-05-15 上线 v118.33.2.0)
**影响文件**:`home.html`(-83 行) + `home.css`(-165 行 adm-lang-bar + sidebar-user 系列) + `home.js`(-150 行 _initSidebarUserMenu + renderSidebarUser + adm-lang-bar IIFE + applySidebarRoleVisibility admin 显隐)

**实施**:
- [x] home.html · 删 Line 2152-2234 整段(管理员组 / 测试组 / adm-lang-bar / sidebar-user 4 块)· 一行注释占位
- [x] home.js · 删 adm-lang-bar IIFE(原 9528-9547)
- [x] home.js · 删 `_initSidebarUserMenu()` + `renderSidebarUser()` + DOMContentLoaded hook 整段(原 9636-9748 共 113 行)
- [x] home.js · 清 loadAll 里的 `renderSidebarUser(u)` 调用
- [x] home.js · 删 `applySidebarRoleVisibility` 的 `.nav-admin-only` / `.nav-group-admin-only` / `adm-lang-bar` 显隐逻辑(原 10729-10739)
- [x] home.js · 测试中心 `_applyVisibility` 改 no-op 外壳(保留 `window._tcApplyVisibility` 兼容外部调用 · nav-group-test DOM 已删)
- [x] home.js · 更新 2 处 Phase 1 残留过期注释("不删旧 sidebar-user-popup" / "不动 sidebar-user-popup 的 ESC")
- [x] home.css · 删 `.adm-lang-bar` + `.adm-lang-pill` 系列(原 5359-5385)
- [x] home.css · 删 `.sidebar-user` + 所有子样式(原 9411-9547 共 137 行 · 保留 `.sidebar { display:flex; flex-direction:column; }`)
- [x] cache bust 11841062 → 11841063
- [x] 部署 v118.33.2.0(scp + ssh deploy.sh · /api/version 返 11841063 · systemctl active)
- [x] 本地 tar.gz 自动删

**保留项**(预期内):
- admin-mode 视图代码(home.js 10672-10681)· Earn 走 `?admin=1` 老逻辑仍需 · Phase 8 独立 admin layout 后再清
- i18n 字典里 `nav-group-test` / `nav-group-admin` / `nav-admin-cost` / `nav-admin-users` 等 key 保留(老顺序不动 · 不破坏字典)

### Phase 3 · sidebar 集成一级入口 ✅ 完成(2026-05-15 · v118.33.3.0 上线 · CTA 在 v118.33.7.3 撤掉)
**实际改动**:
- [x] sidebar 底部加「集成」一级入口 · `data-route="integrations"` · 跳 `page-integrations` 空壳
- [x] 路由表 + i18n × 17 个 key(4 语 全)
- [x] ~~sidebar 顶部蓝色 CTA「上传发票」~~ — Phase 3 加了 · 但 prototype 没这个 · v118.33.7.3 撤(铁律:prototype > PRD 冲突时听 prototype)

### Phase 4 · "即将" badge 大清扫 ✅ 完成(2026-05-15 · v118.33.4.0 上线)
**改动**:
- [x] sidebar 5 个 nav-item 上的 `<span class="nav-badge soon">即将</span>` 全删(仪表盘 / 凭证中心 / 销售发票 / 应收追踪 / 云盘同步)
- [x] 5 个 page 本身保留 coming-soon 空壳 · 点击仍能进

### Phase 5 · sidebar 业务流分组 ✅ 完成(2026-05-15 · v118.33.5.0 上线)
**改动**:
- [x] sidebar 旧 3 组(核心/数据/自动化) → 新结构:首页 / 销项管理▾ / 进项管理▾ / 客户 / 异常 / 自动化(暂留 · Phase 7 没整合) / 底部集成
- [x] 销项管理▾ 5 子项(上传发票 / 发票记录 / VAT 对账 / 销售发票 / 应收追踪)· 进项管理▾ 1 子项(凭证中心 · Phase 6 才补全)
- [x] 折叠组 IIFE(toggle + LS 持久化 + 路由跟随)· 默认销项展开 / 进项折叠
- [x] 改 i18n:`nav-dashboard` 仪表盘 → 首页 / 新增 `nav-group-sales` 销项管理 + `nav-group-expense` 进项管理 / 后续把 `nav-ocr` `nav-history` `nav-reconcile` `nav-exceptions` 4 个 key 改为 prototype 命名(上传发票 / 发票记录 / VAT 对账 / 异常)· 4 语全
- [x] 加 nav-divider 分隔线(客户/异常前)· 对齐 prototype
- [x] 删 cloud 入口(prototype 没 · page-cloud 保留)

### Phase 6 · 进项管理完整模块 🚫 永久跳出 NAV-IA(本质是独立 3 周大模块 · 等 Zihao 拍板独立开)

> ⚠️ **本任务卡由 `MODULE_EXPENSE_PRD_v2.md` 全权负责** · 详见 `pearnly_project/CLAUDE.md/MODULE_EXPENSE_PRD_v2.md`
> 命名:**凭证中心** · 路由 `/expense` · 对标 Paypers 一比一复制 + 全面超越

**影响**:对应 MODULE_ROADMAP 第 6 模块「凭证中心」从 0% → 80%+

**3 子版本拆分**(详见 v2 PRD):

**v118.40 MVP**(8-10 d · 「能用」· Paypers 对齐)
- [ ] 费用分类逻辑(15 类标准 · AI 自动 + 可手改)· 1.5 d
- [ ] PV 生成(标准泰国模板 · 三签名栏)· 2 d
- [ ] **代收据生成 ใบแทนใบเสร็จ**(合规格式)· 1 d
- [ ] 月度支出仪表盘(总额/分类饼图/月对比)· 2 d
- [ ] 多客户费用视图(按客户筛 + 按月筛)· 1 d
- [ ] Google Drive 归档(按客户/月分文件夹)· 2 d
- [ ] 4 语 i18n 全覆盖 · 0.5 d

**v118.41 提升**(5-7 d · 「好用」· 建立差异化)
- [ ] Google Sheets 实时同步 · 2 d
- [ ] Shopee/Lazada/转账单 OCR 支持 · 1.5 d
- [ ] ERP 直推(复用现有 webhook)· 1 d
- [ ] 批量 PV 生成(一次审核多张)· 1 d
- [ ] 操作审计日志 · 0.5 d

**v118.42 专业**(3-5 d · 「超越」· 事务所规模化)
- [ ] 月底批量报告(一键导出当月全部凭证包)· 1.5 d
- [ ] 费用预算管理(设上限 + 超额提醒)· 2 d
- [ ] 费用审批流(员工 → 会计 → 批准)· 2 d

**数据模型**(详见 v2 PRD):
- [ ] 新建表 `expense_records`(费用记录)
- [ ] 新建表 `payment_vouchers`(付款凭证)

**触发**:Phase 1-5 全部完成 + P0-VAT 主线收尾 + Zihao 拍板「开干 v118.40 MVP」

### Phase 7 · 集成模块独立化 ✅ 完成(2026-05-15 · v118.33.7.0 上线)
**目标**:settings 内「集成与连接」整段拆出来 · 升为 sidebar 一级独立页 `page-integrations`
**影响文件**:`home.html` + `home.css` + `home.js`
**实施**:
- [ ] 新建独立 `page-integrations`(从 settings.集成与连接 整段搬出 · 含 Google 服务 / 收票渠道 / ERP 三区)
- [ ] 6 通道统一 `.integration-row` 卡片化:Drive(已连接)/ Sheets(一键开启)/ Gmail / LINE Bot / 文件夹 / ERP 对接
- [ ] settings 删「集成与连接」tab + 默认 tab 改为「账户信息」
- [ ] `home.js`:路由表加 `integrations` + `showSettingsTab` 函数删 `integrations` 引用
- [ ] 4 语 i18n × 7 个新 key(详见 NAV_IA_PRD §5.3)
- [ ] Google 一次授权双服务铁律(Drive + Sheets 共享 OAuth · 蓝色信息条强调)
- [ ] 部署 v118.44.1

### 视觉皮肤对齐(插队任务 · 11 轮迭代 · 2026-05-15 · v118.33.7.1 → v118.33.7.11)✅ 完成
- 整产品配色一刀切对齐 prototype:深蓝主色 → 纯黑 / 浅蓝 active 底 → 暖灰 / 亮蓝强调 → 黑 / 所有页头图标方块改暖灰底 + 灰图标 + 淡边
- token 改:`--brand: #1a365d → #111111` / `--brand-hover: #2a4e7c → #333333` / `--accent: #4299e1 → #111111` / `--accent-soft: #ebf4ff → #f4f4f0`
- 硬编码批量替换 50+ 处:`#EFF6FF` / `#F0F9FF` / `#E0F2FE` / `#BFDBFE` / `#E6F1FB` / `#F0F7FF` / `#185FA5` / `#0C447C` / `#85B7EB` 等浅蓝调一律 → `#f4f4f0` 暖灰 / 暖灰边
- 蓝字硬编码 `#1d4ed8` / `#2563eb` / `#1e3a8a` / `#1e40af` / `#3B82F6` 全部 → `#111111`
- `.btn-primary` 主按钮 深蓝 → 纯黑
- `.page-head-icon` + `.page-head-clean .page-head-icon` 浅蓝渐变 → 暖灰单色 + 淡边(Phase 7.7 改了但被覆盖 · Phase 7.11 修对覆盖 BUG)
- `.drop-zone` 对齐 prototype:浅暖灰底 + 灰虚线 → hover 黑虚线(不变背景)· 图标灰色 hover 变黑
- `.nav-item.active` 浅蓝底蓝字 + 左竖条 → **纯黑底白字** + 去左竖条
- `.topbar-left` 加 border-right 跟 sidebar 顶部「焊接」(prototype 视觉)
- 顶栏高度 56 → 48 · body 字号 14 → 13 · nav-sub-item 缩进 14 → 38(对齐 prototype)
- sidebar 改名:仪表盘 → 首页 / 上传识别 → 上传发票 / 单据记录 → 发票记录 / 对账中心 → VAT 对账 / 异常栏 → 异常(4 语全改)
- 加 nav-divider(客户/异常前)
- BUG 修:
  - X 关闭按钮失效(Phase 2 删 sidebar-user 时把 help-modal close 逻辑误删)— 重新独立绑定 + ESC + 点遮罩关闭
  - sidebar 收起态 nav-sub-item active 黑方块(padding-left 38px 把图标推出容器)— 收起态加 `padding-left: 10px !important`
  - `.page-head-clean .page-head-icon` 覆盖问题(优先级更高 · 我之前改了基类没改这个 · Phase 7.11 修对)

**保留的浅蓝(prototype 也这样)**:`#DBEAFE` / `#dbeafe` info 提示底 — 作 alert / info banner 用

### Phase 8 · Admin Layout 独立 ✅ 完成(2026-05-15 · v118.44.0 → v118.44.0.7 共 8 个微版本)
**Earn 铁律**(2026-05-15 拍板):**不工作 · 只管账户 + 看成本** · sub-nav 仅 2 项 · 砍其他
**新文件**:`static/admin/admin.html` + `admin.css` + `admin.js` + `admin-i18n.js`(完全独立 SPA · 不引 home.js)
**实施**:
- [x] login.html 前端分流:Earn(`is_super_admin=true`)登录后前端跳 `/admin/cost`(后端零改动)
- [x] admin layout sub-nav 只 2 项:成本追踪(`/admin/cost`)+ 用户管理(`/admin/users`)
- [x] 头像菜单「管理员后台」(仅 super admin 可见)→ 跳 `/admin/cost`(home.js L29911 + L30029)
- [x] 顶部 admin banner(黑底渐变 + 橙色腰线 · prototype Earn 视角对齐)
- [x] 沿用 prototype_final CSS token · admin.css 复用 home.css token + 加专属变体
- [x] 部署 v118.44.0(首部署)
- [x] hotfix v118.44.0.1 · 老 `/admin` 路由 301 重定向到 `/admin/cost`(解决浏览器 cache 老 home.js 跳老路径)
- [x] hotfix v118.44.0.2 · 修文字隐形(home.js applyLang 抛错残留 `.lang-switching` class)+ admin.js 持续轮询业务函数
- [x] hotfix v118.44.0.3 · login.html 超管直跳 /admin/cost 跳过 /home 中转 · `/` `/login` 加 no-cache · 卡顿 3s → 1s
- [x] hotfix v118.44.0.4 · 删除「返回普通视图」按钮(死循环) + 修语言下拉关闭(用 contains 判定)
- [x] hotfix v118.44.0.5 · home.js L13585 顶层 try-catch + admin.js 自己 fetch admin 业务 API(独立)
- [x] hotfix v118.44.0.6 · 诊断面板改累积日志
- [x] hotfix v118.44.0.7 · **彻底独立** · admin.html 拔掉 home.js + 新建 admin-i18n.js(zh+th 49 key)+ 修 Google 余额 endpoint(`/api/admin/billing/balance`)+ 加 5 个按钮 listener + 删诊断 chip

**已砍**:平台概览 / 操作日志 / API 健康度(Earn 不需要 · 2026-05-15 拍板)

**cache bust**:`11841078` → `11841085`(本 Phase 累计升 7 次)

**i18n 新增**:`adm-banner-msg/title` `adm-sidebar-section/cost/users` `adm-back-to-home`(zh+th+en+ja 各 6 key)+ admin-i18n.js 内嵌 49 个 admin 视图 key(zh + th)

**承接关系**:NAV-IA 主线 8 Phase 全部完成 · 接下来等 Zihao 拍板独立开 Phase 6(进项管理 v118.40 · 3 周大模块)或回 P0-VAT 收尾

---

## 🆕 优先级状态(2026-05-12 重排)
> **核心约束**:对齐 Xero / QuickBooks / Stripe / Notion 三层原则 L1/L2/L3
> **战略铁律**(2026-05-09 拍板):自动化 ERP 适配器主线升 P0 · 所有窗口必须以 ERP 工作优先 · 其他全部排后
> **战略升级**(2026-05-12 拍板):P0-VAT 销项税对账(月度刚需 · 14-18 d)插队为最高优先级 · P0-A MR.ERP 剩余 5 版暂停 · P0-VAT 全部完成后接力
> **v27.8 拍板红线**(继承 + 累积):三层架构永久并存 · A 不是默认 · Korn 模板克隆(铁律 59) · UI 业务化(铁律 60) · showdata pattern(铁律 61) · 字段对照表后台页(铁律 62) · 子串占比闸(铁律 63) · 用户字段 SSoT(铁律 64) · 员工字段全套继承(铁律 65) · admin_upgrade 同步 tenant(铁律 66) · tenants 表幽灵字段(铁律 67) · 服务器单独覆盖文件清单(铁律 68)
> **P0-VAT 红线候选**(2026-05-12 新增):VAT Excel Korn 模板克隆(铁律候选 60-VAT) · 个人买家字段 6/7 跳过(候选 61-VAT) · 佛历统一转西历存库(候选 62-VAT) · 配对置信度 <0.95 强制人工(候选 63-VAT) · 跨期发票标 cross_period 不入对账(候选 64-VAT)
> **本窗口成果**(2026-05-12):v118.32.3.0 → v118.32.3.9 共 10 个微版本 · BCDEF 优化阶段 · B/F1/F2 代码完成 · UI 主流大厂对齐(Gmail/DeepSeek/QuickBooks)· 系统设置改 modal · 任务批量删除 · ⚠️ 6 张卡 10 分钟仍未解决 · C/D/E 全部未做

## 🆕 优先级状态(2026-05-12 重排)

**P0-VAT 销项税对账升最高优先级 · 完成前一切其他 P0 任务暂停**:

1. 🔥🔥 **P0-VAT · 销项税对账模块**(v118.32.0 → v118.33.1 · 5 版 · 14-18 d) · **本窗口最高优先级 · 月底刚需**
2. ⏸️ **P0-A · MR.ERP 剩余版本**(v118.27.8.1.18 → v22 · 7.5 d) · **暂停 · 等 P0-VAT 完成接力**
3. 🟡 **P1 · 公测前/战略**(Git 私库 + webhook 卡片化 + OCR 速度优化 + 异常栏 P2)
4. 🟢 **P2 · 公测后/模块扩张**(模块依次扩展 · 见后段)
5. 🛡️ **P3 · PDPA + 运维合规底线**(2026-05-11 拍板)· 项目主体完成后做 · 免费 11 项先 / 必付费 1 项后 / 推荐付费 等真客户(见 v118.99.x 章节)

---

## 🔥🔥 P0-VAT 头号主线 · 销项税对账模块(v118.32.0 → v118.33.1 · 14-18 d)

> **业务定位**:对账中心(`reconcile`)第一个子模块 · 月度刚需 · MODULE_ROADMAP.md 第 9 模块从 0% 升到 60%+
> **泰文**:การกระทบยอดใบกำกับภาษีขายกับรายงานภาษีขาย
> **English**:Output VAT Reconciliation against Sale VAT Report
> **来源**:Korn(高级会计师)PDF SOP + Excel PROMT 工作表 + BAKELAB 真样本(33 张发票 · 2026/03)
> **PRD 主文档**:`MODULE_SALE_VAT_RECON_PRD.md`(项目 Knowledge 已落库)
> **拍板**:2026-05-12 · 本模块完成前 P0-A MR.ERP 剩余 5 版全部暂停
> **承接关系**:一级模块「对账中心」早在 MODULE_ROADMAP.md 第 9 模块占位 · 原规划是「ภ.พ.30 PDF 一键生成 + 银行流水对账」(L5 报表层)· 本模块填补更早期的「逐行对账核对」缺口(L3 对账层)· 完成后承接 → ภ.พ.30 PDF 一键生成(原 v118.30.x L5 规划)
### 拍板红线(候选铁律 60-VAT ~ 64-VAT · 完成后写入 CORE_PEARNLY_PLAN.md)

- **候选铁律 60-VAT** · VAT 对账 Excel 输出永远用 Korn 模板克隆 · 不许 openpyxl 直接 save(沿用铁律 59 MR.ERP 经验)
- **候选铁律 61-VAT** · 个人买家(无 tax_id)对账时字段 6/7 必须跳过 · 否则全部个人买家发票误报"分支不一致"
- **候选铁律 62-VAT** · 佛历日期统一 -543 转西历存库 · UI 显示按用户语言切换(泰语佛历 / 其他西历)
- **候选铁律 63-VAT** · 配对置信度 < 0.95 强制人工确认 · 不允许系统自动判定
- **候选铁律 64-VAT** · 跨纳税期间孤儿单据一律标 `cross_period` · 不参与本期对账 · 不可自动接受

---

#### ✅✅ v118.32.0 → v118.32.2.5 已完成(前窗口 · 屏 A/B/C 基础)

详见前窗口 transcript · 本节略。

---

#### ✅ v118.32.3.0 → v118.32.3.9 BCDEF 优化阶段(本窗口 2026-05-12 · 10 微版本) — 已基本完成 · 有 P0 遗留

**完成清单**:
- **v3.0** B-1 batch_classify 并行 10 路(asyncio.gather + Semaphore(10) + run_in_executor)+ F1 金额对齐(`_get_total` 用 amount_pre_vat 对 report_amount · 前税对前税)
- **v3.1** F2 Excel 表头 4 语 i18n(`_LABELS` 字典 · `_t(lang, key)` 函数 · 非泰文加 ` · รายงานภาษีขาย` 副标题给税局 · /export/{id}?lang= 端点 + 前端 _onExport 传 lang)
- **v3.2** 任务批量删除端点 POST `/api/recon/tasks/batch_delete` + 任务卡 checkbox + ⋮ 单条删除菜单 + **batch_process 顺序调整**(先建 vat_report → 建 task → OCR(source_ref=task_id 写入)→ 跑匹配 · 关键!删任务能精准清缓存)
- **v3.3** SQL `%s::int[]` → `ANY(%s)` + showConfirm 替代浏览器 confirm + Gmail 风格切换栏(标题/操作就地切换 · 不出现额外蓝色条)+ ⋮ hover 显示 + Pearnly 弹窗
- **v3.4** **KeyError: 0 修**(RealDictCursor 返回 dict · 用 `r["tid"]` 列名访问 · 不是 `r[0]`)+ 单据记录批量栏改图标按钮(↓ 🗑 ✕)
- **v3.5** 单据记录 ⋮ hover 才显示 + 去除负 margin hack · grid `28px 96px 1fr 100px 90px 36px` + tabular-nums 等宽数字
- **v3.6** 系统设置 → modal 弹窗(`_wrapSettingsAsModal` 动态包装 page-settings · 桌面 1000×85vh 圆角 16 · 移动端全屏 + 顶部 tab 横滚 + 半透明遮罩 · 参考 DeepSeek/ChatGPT/Linear)
- **v3.7** batch_classify 加 **30s 单文件超时**(asyncio.wait_for)+ timing log + 前端进度实时秒数 + "比预期慢 · 可能 AI 限速"提示 · 单据记录列收紧 `88px 76px 28px`
- **v3.8** openSettingsModal 主动 `click` active tab(50ms setTimeout · 触发 access-log/team 的 hook · 修加载卡死)+ DeepSeek 风格右侧内容(填满 + 行间细横线 + 去嵌套卡片边框)
- **v3.9** 单据记录列真贴右(根因:`.card` 自带 padding 20px · 修法 `#history-main.card { padding: 0 }` · 让表格直接铺到 .main 边界)+ ✕ 关闭按钮真显示(根因:close 是 overlay 的子但 overlay 没 position:relative · close 跑到浏览器右上角 · 修法把 close 移进 `#page-settings` 内 · `position: relative !important`)+ batch_classify 加 **5 分钟 AbortController 超时** + inline 红色错误条(失败时显示具体原因 · 用户必须主动点 ✕ 才消失)

**关键拍板**:
- Gmail 切换栏模式(选中后标题区切换为操作栏 · 同一行)
- DeepSeek 设置弹窗模式(右侧填满 + 行间横线 + 去嵌套卡片)
- QuickBooks/Xero 金额列右对齐(列头 + 数据 + tabular-nums)
- 删任务级联清 OCR 缓存(source_ref = task_id 是关键关联)
- UI 文案永不暴露 "Gemini" / "OCR" 技术词(铁律 60-VAT 业务化)

**🔴 P0 遗留**(下窗口必修):
- **6 张文件批量识别仍卡 10 分钟**(v3.7 加 timing log + 30s 超时 / v3.9 加 5 分钟 + inline 错误条 · 都未根本解决)
- **嫌疑根因**:`parse_vat_report` 是同步函数(`def`)· 在 async 路由 batch_process 里直接调 · 阻塞整个 fastapi 事件循环
- **下窗口起手式**:
  1. `ssh ... journalctl -u mrpilot -n 200 | grep batch_classify`
  2. 让用户截图测试中心 24 条异常
  3. 把 parse_vat_report 用 run_in_executor 包(候选 fix)
  4. 部署 v118.32.3.10 hotfix

**🟡 P1 遗留**(用户未实测):
- F1 5/5 BAKELAB 匹配未验证(理论上 v3.0 改后应精确匹配)
- F2 Excel 4 语导出未验证
- 系统设置 modal 各 tab 没逐个测过(可能某些 pane 布局错乱)
- 单据记录列贴右 v3.9 才修对 · 用户没确认

**🟢 P2 遗留**:
- `gemini_engine.py` 不在 project knowledge · E 阶段前必须先 scp 拉到本地
- 测试中心 sidebar badge 显示 "24" 异常 · 让用户截图看具体错误

---

#### 🔥 v118.32.4.9.6 → v118.32.4.11 公式对账成熟化 + UX 大改造(2026-05-13 拍板 · 9 天路线)

> **详细规划见 STATE_PEARNLY.md** "🧪 v4.9.5 内测结果" 段 + "🎯 v4.10 UX 大改造" 段 + "🔍 v4.11 详情抽屉" 段

- **v4.9.6 公式对账成熟化(3.0 天)** · 5 bug + UI 美化 + 504 修复 · 🔥 本窗口正在做
- **v4.10 UX 大改造(3.1 天)** · 撤旧 toggle + UI 汇总页 KPI/筛选/明细 + 试用限 3 次 + 撤白名单
- **v4.11 PDF 溯源(3.0 天)** · 详情抽屉 + PDF.js + bbox 三层降级
- **v4.12 暂缓 P3 候选** · 见下方 P3 段 · 等真实会计师 2-3 周反馈再决定

---

#### 🔥 v118.32.4 · C 进度反馈业务化(1-1.5 d) — **下下窗口主任务**(P0 解决后开工)

来源:`MODULE_SALE_VAT_RECON_PRD.md` §6.4 + 本窗口讨论

**前端**:
- [ ] 分阶段进度条:① 解析报告 (10%) → ② 识别发票 (10-70%) → ③ 自动匹配 (70-90%) → ④ 完成 (100%)
- [ ] 实时滚动样本:轮换显示当前正在处理的文件名 + 公司名("正在识别 INV2026030003 · บริษัท เบคแล็บ...")
- [ ] 预估剩余时间(基于已用时间 + 已完成数)
- [ ] 业务结论文案("识别完成 · 28 张待复核" 不是 "OCR 完成")
- [ ] 失败时给具体业务原因(不显示 stack trace)

**铁律 60-VAT 业务化原则**:
- 永不出现 "Gemini" / "OCR" / "API" / "engine" / "并发" / "限速" 等技术词
- 用 "智能识别" / "未能识别此文件 · 请手动选类型" / "服务繁忙 · 稍后重试" 等业务话术

---

#### 🔥 v118.32.5 · D 后台异步 + 3 路通知(2-3 d) — 月底 800 张刚需

**后端**:
- [ ] 任务队列(Celery 或 FastAPI BackgroundTasks · 简单的先用后者)
- [ ] 任务状态表 `recon_async_task`(status / progress / result_json / created_at)
- [ ] 关网页继续跑(任务不依赖 HTTP 连接 · 后端独立处理)
- [ ] WebSocket 或长轮询通知前端进度
- [ ] LINE Bot 推送(任务完成 · 加 "BAKELAB + 其他 35 个客户已对账完成 · 12 行待复核")
- [ ] 邮件 hello@pearnly.com 推送(同 LINE)
- [ ] 顶部红点 badge(进入对账中心看任务列表)

**前端**:
- [ ] 任务列表加进度条卡(进行中的任务)
- [ ] 关网页前提示 "任务在后台继续 · 完成会 LINE 通知您"
- [ ] LINE 绑定提示(未绑定时引导)

---

#### 🔥 v118.32.6 · E OCR prompt 升级(1 d) — `gemini_engine.py` 拉回本地后

**前置**:让用户 `scp root@45.76.53.194:/opt/mrpilot/gemini_engine.py D:\Users\Skin\Desktop\` 加进 project knowledge

**改动**:
- [ ] buyer_name prompt 加更明确提示:`"买方完整公司名 · 含 บริษัท / Co.,Ltd 后缀"`
- [ ] branch prompt 强化:`"如显示 'สำนักงานใหญ่' / 'HQ' / '00000' 都识别为总部 = 00000"`
- [ ] amount_pre_vat 强化:`"前税金额(不含 VAT)· 通常是 รวมเป็นเงิน 那一行 · 注意不要识别成 จำนวนเงินรวมทั้งสิ้น(含税总额)"`
- [ ] 解决用户曾遇 INV2026030003/004 字段缺失问题

**测试方法**:重跑 BAKELAB 5 张发票 · 看 buyer_name / amount_pre_vat / branch 是否准确

---

#### 🔥 v118.32.0 · 数据底座 + 单客户对账核心(4 d) — **前窗口已完成**

来源:`MODULE_SALE_VAT_RECON_PRD.md` §4 数据模型 + §5 核心算法 + §6.2 屏 A

**后端**:

- [ ] 新建 3 张表 schema:`reconciliation_task` / `reconciliation_row` / `vat_report`(详见 PRD §4.1)
- [ ] 9 字段对比引擎(`field_comparator.py`)· 包含:
  - 字符串标准化(去前缀差 INV vs IV / 空格 / 全角半角 / 大小写折叠)
  - 数字容差(±0.01 · 7% 计算精度容忍)
  - 日期佛历↔西历自动转换(-543)
  - 13 位税号 Mod-11 校验算法
  - 总部 ↔ "00000" ↔ "สำนักงานใหญ่" 三种写法视为同
- [ ] 三轮配对算法(`reconciliation_matcher.py`):
  - 第一轮主键(标准化 invoice_no)→ confidence 1.0
  - 第二轮复合键(date + buyer_tax_id + total)→ confidence 0.95
  - 第三轮模糊(date ±1 + name Levenshtein ≥ 90% + total)→ confidence 0.75
- [ ] 差异自动归类(`diff_categorizer.py`)· 11 个 category(详见 PRD §5.3)
- [ ] VAT Report 解析器骨架(`vat_report_parser.py`)· 先支持 Excel + BAKELAB 样本格式
- [ ] 4 个 API endpoints:
  - `POST /api/recon/task` 创建对账任务
  - `POST /api/recon/upload_report` 上传 VAT 报告 → 返回 parsed_rows
  - `POST /api/recon/run/{task_id}` 触发对账
  - `GET /api/recon/result/{task_id}` 拉取结果

**前端**:

- [ ] 主导航加 `对账中心 → 销项税对账` 入口(对账中心一级模块从占位升为可点)
- [ ] 屏 A 单客户对账创建页 UI:
  - 选客户(色块头像)+ 纳税期间下拉
  - 系统立即显示该期间已归档发票数 · 总额 · 数据源分布(蓝色提示框)
  - 拖拽虚线区上传 VAT 报告(支持 .xlsx / .xls / .pdf)
  - 「从邮件抓取」按钮(复用 IMAP 通道)
  - 折叠区「还有未归档的发票?在此补传(可选)」
  - 底部「开始对账」CTA + 预计耗时提示
- [ ] 客户色块头像系统(跨模块视觉一致 · 给每个客户分配固定颜色)
- [ ] 最近对账记录列表(顶部 3 条 · 月度任务节奏感)
- [ ] 4 语 i18n × 30+ 词条(含「งวดภาษี」「ก่อน VAT」等专业税务术语)
- [ ] cache bust 递增

**验收**:

- BAKELAB 2026/03 样本 33 张发票 + 1 份 VAT Report PDF · 对账总耗时 < 10 秒
- 9 字段对比准确率 100%(已知样本)
- 个人买家场景字段 6/7 跳过 · 不报差异(候选铁律 61-VAT)
- 佛历日期自动转换正确(候选铁律 62-VAT)
- 配对置信度 < 0.95 强制人工确认(候选铁律 63-VAT)
- 4 语 UI lint `check_i18n.py --strict` 通过

---

#### 🔥 v118.32.1 · 对账结果详情页 + AI 分析(3 d)

来源:`MODULE_SALE_VAT_RECON_PRD.md` §6.2 屏 C

**后端**:

- [ ] AI 分析层(`ai_analyzer.py`)· 复用 Gemini · 输入 diff_fields + 历史相似案例 · 输出:
  - 一句话原因推断(「报告日期晚发票 1 天 · 可能客户录入时手误」)
  - 建议操作(更正报告 / 接受差异 / 让客户重开发票)
  - 起草客户邮件草稿(泰中双语)
- [ ] AI 起草客户邮件 endpoint `POST /api/recon/draft_email/{row_id}`
- [ ] 行级动作处理 `POST /api/recon/row/{row_id}/action`(resolved / customer_issue / accepted_diff)
- [ ] AI 失败 fallback · 模板化解释(「字段 X 不一致 · 差额 Y · 建议复核」)

**前端**:

- [ ] 屏 C 对账结果详情页 UI:
  - 顶部 4 KPI 卡(总数 / 完全匹配绿 / 字段差异橙 / 单边孤儿红)
  - 匹配率水平进度条(三段:绿橙红)
  - 状态色 chip 筛选(全部 / 已匹配 / 日期差 / VAT 精度差 / 单边孤儿)
  - 列表表格 · 7 列(序号 / 发票号 / 日期 / 客户 / 货款 / VAT / 状态)· 颜色编码
  - 点击行展开 → 双栏字段级 diff:
    - 左栏「原始发票」· 右栏「客户 VAT Report」
    - 差异字段红底高亮 · 旁标 `差 +1 天` / `少前缀 N` / `差 -0.01`
    - 一致字段后打 ✓
  - 底部 AI 分析卡(蓝色背景)· 3 按钮(起草邮件 / 标记客户问题 / 接受差异)
  - 顶部右上角操作组:导出 PDF / 导出 Excel / 提交客户 / 推送 MR.ERP
- [ ] 起草邮件 modal · AI 生成后可二次编辑 · 一键发送(复用现有邮件管道)
- [ ] 4 语 i18n × 40+ 词条
- [ ] cache bust 递增

**验收**:

- AI 解释准确率 > 80%(Korn 提供 20 个真差异行人工评估)
- 起草邮件可生成泰中双语 · 客户老板可直接发
- 用户操作流畅:从展开 diff → 看 AI 分析 → 起草邮件 ≤ 3 次点击
- 4 语 UI lint 通过

---

#### 🔥 v118.32.2 · Excel 导出 · Korn 模板克隆(2 d)

来源:`MODULE_SALE_VAT_RECON_PRD.md` §7 Excel 导出规范

**前置依赖(阻塞 · 必须先准备)**:

- [ ] **找 Korn 老师要 1 份标准对账报告 Excel 样本**(没有样本无法克隆 · 参考铁律 59 经验)
- [ ] 拿到后 MD5 验证 6 个 metadata 文件

**后端**:

- [ ] 模板克隆生成器(`vat_recon_xlsx_generator.py`)· 复用铁律 59 的 MR.ERP 经验
- [ ] 6 个 metadata 文件不动(`workbook.xml` / `Content_Types` / `styles` / `theme` / 2 rels · MD5 跟 Korn 完全一致)
- [ ] 只重写 `xl/sharedStrings.xml` + `xl/worksheets/sheet1.xml`
- [ ] 表头 6 行固定输出(经营者名/地址/13 位税号/分支/期间/标题)
- [ ] 列结构 20 列 + 9 个 / 标记栏(详见 PRD §7.1)
- [ ] 多差异行展开规则:同发票多差异 → 拆 N 行(每差异 1 行 · 9 个 / 全打 · 备注列写差异)
- [ ] 底部签字栏固定输出(ผู้จัดทำ / ผู้ตรวจสอบ / ผู้อนุมัติ)
- [ ] 尾部 `รวมยอดทั้งสิ้น` 总计行
- [ ] 导出 endpoint `GET /api/recon/export/{task_id}.xlsx`
- [ ] 导出 PDF endpoint `GET /api/recon/export/{task_id}.pdf`(复用 weasyprint)

**前端**:

- [ ] 「导出 Excel」按钮 · loading 状态 · 完成后自动下载
- [ ] 两种导出选项 modal:
  - 折叠视图(每发票 1 行 · 适合内部审计)
  - 展开视图(每差异 1 行 · 客户传统报告格式)
- [ ] 4 语 i18n

**验收**(候选铁律 60-VAT 落地):

- 导出 Excel 跟 Korn 传统模板像素级一致(单元格位置/字体/边框)
- **Korn 老师本人验收**(发邮件附 Excel · 等回复)
- 字节级自诊断 endpoint(参考 v27.8.1.10 经验):服务器对比 Korn 样本 vs 我们输出
- 多差异行展开规则正确(同 BAKELAB INV2026030004 拆 2 行)

---

#### 🔥 v118.33.0 · 批量智能识别 · 多客户场景(4 d)

来源:`MODULE_SALE_VAT_RECON_PRD.md` §6.2 屏 B

**后端**:

- [ ] 文件类型自动识别(`file_classifier.py`):
  - OCR 后扫关键词:`ใบกำกับภาษี` → 发票 · `รายงานภาษีขาย` → 报告
  - 表格结构识别(N 列 X 行 = 多行项目 = 报告)
  - 单页 + 单一供应商抬头 = 发票
- [ ] 自动分组算法(`auto_grouper.py`):
  - 按 (issuer_tax_id, period_year, period_month) 分组
  - 多页 PDF 合并(同 issuer_tax_id 同 period 的 PDF 各页拼为 1 份逻辑报告)
  - 多 sheet Excel 合并(同条件下多 sheet 拼为 1 份)
- [ ] 置信度计算(每组任务的整体配对置信度)
- [ ] 新 endpoint `POST /api/recon/intake_bulk`
- [ ] 大文件量队列(>100 文件触发异步模式 · 复用现有 OCR 队列基础设施)
- [ ] 进度报告 endpoint `GET /api/recon/intake_bulk/{batch_id}/progress`

**前端**:

- [ ] 屏 B 批量智能识别确认页 UI:
  - 大拖拽区(680px 高 · 支持文件夹拖拽)
  - 上传进度条(>100 文件时)· 「已上传 X / Y · 剩余约 N 分钟」
  - 顶部 4 统计卡(上传文件 / 识别为发票 / 识别为报告 / 无法识别)
  - 任务分组列表:
    - 每个对账任务 1 行(客户色块头像 · 公司名 · 13 位税号 · 期间 · 文件统计 · 置信度徽章)
    - 99% 绿色「直接执行」/ 84% 黄色「请确认」/ <70% 红色「强制人工」
    - 展开看明细(发票号范围 · 报告文件名)
  - 低置信度警告 banner:「3 份报告分散在多个 PDF · 系统判属同一份 · 请确认」
  - 「无法识别 X 个文件」专区 + 3 按钮(逐个查看 / 手动指派客户 / 忽略)
  - 手动调整分组(拖拽改归属)
  - 底部「全部启动对账」CTA(展示已勾选数)
- [ ] 4 语 i18n × 30+ 词条
- [ ] cache bust 递增

**验收**:

- 300 张混合文件 + 多份报告:< 60 秒识别完
- 分组准确率 > 95%(Korn 提供 5 家客户混合样本)
- 低置信度(< 0.84)强制弹「人工确认」(候选铁律 63-VAT)
- 手动拖拽调整后系统记住(写入历史归属表)
- 多页报告合并正确(同 issuer_tax_id 同 period 的多 PDF 自动并)

---

#### 🔥 v118.33.1 · 边界场景 + 异常栏联动 + Korn 整体验收(2 d)

来源:`MODULE_SALE_VAT_RECON_PRD.md` §8 边界场景 + §9.3 异常栏联动

**后端**:

- [ ] 个人买家(无 tax_id)· 字段 6/7 跳过 · 不算差异(候选铁律 61-VAT)
- [ ] 同税号多分支 · 必须 (tax_id, branch) 联合配对 · 仅按税号会错位
- [ ] 已废止发票(ใบกำกับยกเลิก)· 单列警告 · 不进对账
- [ ] 跨期发票 · 标 `cross_period_orphan` · 不强制对账(候选铁律 64-VAT)
- [ ] 零税率(出口/国际服务)· 字段 9 跳过
- [ ] 含税开票自动反算(net = total / 1.07)
- [ ] 重复发票号 · 标 `duplicate_invoice_no` · 单列警告
- [ ] **与异常栏联动**:发票自检失败(卖家信息缺 / VAT ≠ 7% / 税号假)→ 自动进异常栏现有规则引擎(复用 v118.20 5 类规则)
- [ ] 异常栏跳转 hook · 对账详情页 → 异常栏对应行(双向跳转)

**前端**:

- [ ] 边界场景 UI 文案 + 提示徽章:
  - 个人买家行显示「บุคคลธรรมดา · 跳过分支核对」灰色徽章
  - 跨期发票行显示「跨纳税期间」黄色徽章 + 跳到下月对账按钮
  - 已废止行显示「已废止 · 不参与对账」红色徽章
  - 零税率行显示「零税率 · 跳过 VAT 对比」蓝色徽章
- [ ] 异常栏联动:对账行点「进异常栏看详情」直接跳转 + 高亮该行
- [ ] 4 语 i18n

**整体验收**(模块完成标准):

- [ ] Korn 老师验收至少 2 家不同客户的真样本通过测试(BAKELAB + 1 家个人买家为主的客户)
- [ ] 所有候选铁律 60-VAT ~ 64-VAT 经实战验证 · 写入 `CORE_PEARNLY_PLAN.md` 正式铁律
- [ ] MODULE_ROADMAP.md 的「对账中心」从 0% 升到 60%+
- [ ] 4 语 UI lint check_i18n.py --strict 通过
- [ ] 整体对账场景操作步骤 ≤ 3 次点击(单任务)/ ≤ 5 次点击(批量)
- [ ] 3 屏完整链路录屏 demo · 发 Korn 验收

---

### 📊 P0-VAT 操作数对比(对标手工对账)

| 场景 | 手工对账 | Pearnly P0-VAT 完成后 | 减少幅度 |
|---|---|---|---|
| 单客户 33 张发票 + 1 份报告 | 2-3 小时 | < 30 秒(含人工 review) | **-99%** ★★★ |
| 月底批量 30 家客户混合上传 | 3-5 天 | < 1 小时 | **-95%** ★★★ |
| 差异行追溯 + 起草客户邮件 | 5-10 分钟/行 | 1 分钟/行(AI 起草) | -80% |
| 导出 Excel 客户报告 | 30 分钟手工排版 | 1 秒(模板克隆) | -99% |
| 跨月连续对账 100+ 客户 | 几乎不可能 | Dashboard 一屏看全 | **质变** |

### 风险与缓解

| 风险 | 缓解 |
|---|---|
| Korn 模板 Excel 难拿到 | v118.32.2 开始前必须先找 Korn 要标准样本 · 否则该版本阻塞(参考铁律 59 经验) |
| 客户 VAT 报告格式多样(各 ERP 不同) | 渐进式 · 先支持 BAKELAB + 4 家常见 ERP(FlowAccount / Express / Business Plus / MR.ERP)· 其他走模板自学习 |
| AI 解释准确率不够(< 80%) | 准备 fallback:LLM 失败时模板化解释 · 不阻塞主流程 |
| 多差异行展开导致 Excel 行数膨胀 | 提供折叠视图 + 展开视图两种模式 · 用户自选 |
| 模糊匹配错配率 > 5% | 置信度 < 0.95 强制人工确认 · 候选铁律 63-VAT |

### 🔑 P0-VAT 启动前必须准备的物料(发 Korn 要)

| 物料 | 用途 | 紧急度 |
|---|---|---|
| Korn 标准对账报告 Excel 样本 1 份 | 模板克隆(铁律候选 60-VAT) | **v118.32.2 阻塞** |
| 个人买家为主的客户真样本 1 家(5-10 张发票) | v118.33.1 边界场景验收 | v118.33.1 前 |
| 多客户混合样本 5 家(每家 20-50 张发票 + 1 份报告) | v118.33.0 批量识别验收 | v118.33.0 前 |
| FlowAccount / Express / Business Plus 等 ERP 导出报告样本 | v118.33.0 解析器扩展 | v118.33.0 之前 |

发 Korn 的泰语请求邮件:
```
เรียน คุณคอน,

ขอความอนุเคราะห์ส่งตัวอย่าง 3 ไฟล์เพื่อเริ่มพัฒนาโมดูล "การกระทบยอดภาษีขาย":
1. ไฟล์ Excel "รายงานตรวจสอบภาษีขาย" ฉบับมาตรฐานที่ท่านใช้อยู่ 1 ไฟล์
2. ตัวอย่างใบกำกับภาษีที่ผู้ซื้อเป็น "บุคคลธรรมดา" 5-10 ใบ
3. ตัวอย่างรายงานภาษีขายจากลูกค้า 5 รายที่ใช้ระบบบัญชีต่างกัน

จะใช้เป็นต้นแบบในการพัฒนา + ทดสอบความถูกต้อง 100%
ขอบคุณครับ
```

### 📅 P0-VAT 执行节奏估算

```
今天 2026-05-12  ────────────────────────────────────────┐
                                                          │
  v118.32.0  数据底座 + 单客户对账(4 d) → 2026-05-16    │
  v118.32.1  结果详情页 + AI(3 d)      → 2026-05-19    ├─ P0-VAT 14-18 d
  v118.32.2  Excel Korn 模板克隆(2 d)  → 2026-05-21    │
  v118.33.0  批量智能识别(4 d)         → 2026-05-25    │
  v118.33.1  边界场景 + 验收(2 d)      → 2026-05-27    │
                                                          │
  Korn 验收通过 ───────────────────────────────────────────┘
                                                          │
  v118.27.8.1.18  OCR 智能归属(1.4 d)  → 2026-05-29    │
  v118.27.8.2-5   MR.ERP 剩余(7.1 d)   → 2026-06-05    ├─ P0-A 恢复 7.5 d
                                                          │
  P0-A 全部完成,进入 P1 ───────────────────────────────────┘
```

---

## 🔥 P0 头号主线 · 自动化 ERP 适配器(剩 6-8 天 + v118.30+ 浏览器扩展)

> Pearnly 核心商业闭环 · 比银行对账 / 用户管理优先级高
> 「不让用户换 ERP · 让 Pearnly 适配所有 ERP」
> **本窗口确认**:三层 A+C+D 永久并存 · A 不是默认 · 任何一层失败自动降级

### v118.27.0 - v118.27.7.1 已完成 · 跳到 v118.27.8

- [x] **v118.27.0** 客户/科目/税码映射底座 · 3 张表 + 6 接口 ✅ 测试通过
- [x] **v118.27.0.1** 弹窗统一 + ERP 映射搬「自动化」+ seed 提速 ✅ 测试通过
- [x] **v118.27.1** MR.ERP xlsx 适配器(stub-first)· sales_credit 单张可用 ✅
- [x] **v118.27.4** Xero OAuth 2.0 适配器(连接 + 推 ACCREC + 错误码 4 语) ✅
- [x] **v118.27.4.1** 修 Xero `invalid_scope`(broad → granular) ✅ 测试通过
- [x] **v118.27.4.2** MR.ERP sheet 数动态(铁律 28 修正)✅
- [x] **v118.27.5** 抽屉 1 推按钮统一 split + 下拉 + connectors/status ✅
- [x] **v118.27.5.1** 多发票文件导出 hotfix · invoices 数组 + 拆 N 行 ✅
- [x] **v118.27.5.2** race condition hotfix + SKIN 双闸 ✅
- [x] **v118.27.5.3** 泰国销售明细导出模板 ✅
- [x] **v118.27.5.4** 新版本检测横幅 ✅
- [x] **v118.27.5.5** unified IIFE race hotfix(placeholder-first)✅
- [x] **v118.27.6** 4 模板对齐 + 砍 ERP 录入 + 路由分发 ✅
- [x] **v118.27.6.1** 抽屉推送下拉改 dropup ✅
- [x] **v118.27.7** 识别中心下拉向上弹 + export-by-history-ids ✅
- [x] **v118.27.7.1** 客户导出 BUG hotfix · retention_days Optional ✅

### 🔥 v118.27.8 · 三层 ERP 对接架构 · MR.ERP A 层闭环(2026-05-10 ~ 11)

**红线**(继承 + 本窗口新增):
- 三层架构永久并存(A 后端模拟 + C xlsx 兜底 + D 浏览器扩展)· A 不是默认
- ERP 对接主页 UI 三件套(留 v27.8.2)
- 完整映射 UI(留 v27.8.2)
- MR.ERP 反向工程 ✅ 100% 完成
- **MR.ERP sales_credit xlsx 必须 Korn 模板克隆生成**(铁律 59 · 本窗口新增)
- **UI 文案业务化**(铁律 60 · 本窗口新增)

#### v27.8.0 · 反向工程 + 后端骨架 ✅ 完成

- [x] 反向工程 5 步全实测 + `mrerp_pusher.py`(MrErpPusher 类 · 5 步 + 4 类异常 + bs4 解析 · 430 行)
- [x] `kms_helper.py`(Fernet 加密 · 70 行)
- [x] `PEARNLY_KMS_KEY` env 配
- [x] v27.8.0.1-0.4 hotfix(login 字段名 + selectdb 步骤 + scrape idus bs4 + dump 诊断)
- [x] 临时部署 + 实测 5 步全通

#### v27.8.1.0 - 27.8.1.14d · MR.ERP MVP + 推送通道打通 + 整链路完美闭环 ✅ 完成

| 版本 | 内容 | 状态 |
|---|---|---|
| **v27.8.1.0** | MVP · `mrerp_credentials` 表 + 5 db 函数 + 3 endpoints + 凭据 modal + 4 语 i18n | ✅ |
| **v27.8.1.1** | hotfix · setTimeout 600/700ms 自检定时(防 IIFE race) | ✅ |
| **v27.8.1.2** | excel_template_th.py Korn 公式修复(=E*F · 防循环引用) + `_userInfo` 轮询 | ✅ |
| **v27.8.1.3** | 「识别完自动推送」toggle 端到端 · auto_push BOOL 字段 + OCR 钩子(2 处)+ Xero/MR.ERP IIFE 加 toggle | ✅ |
| **v27.8.1.4** | mrerp_xlsx_generator schema 大改对齐 Korn 真样本(header 18 / detail 8 / tail 3 列 · 默认值 BOI1/00002/0000/'7 (แยก)'/กร ทดสอบ/สุพรรณบุรี/ขนส่งโดยบริษัท) | ✅ |
| **v27.8.1.5** | invoice_no `INV-2026-0501` → `690415-001`(BE+MM+DD+seq 标准格式) · bill_no `SI690415-001` · 失败时存 xlsx_b64 + 下载 endpoint | ✅ |
| **v27.8.1.6** | 🔥 抢救式抓 MR.ERP 错误 hint(关键诊断改进) · 扫 raw HTML 找红色文字/JS alert/关键词 ไม่พบ/ผิดพลาด · push log 详情显示「🔥 MR.ERP 服务端的提示」红框 · raw HTML 存 response_body | ✅ |
| **v27.8.1.7** | 强制 cell 物理保留(' ' 空格占位) + sheet1 末尾 col 19 spacer cell · dim=A1:S2 | ✅ |
| **v27.8.1.8** | 🧪 Korn 真样本对照测试 endpoint + UI 按钮 · **决定性诊断**(Korn 真样本能推 → mrerp_pusher OK + 服务端 OK · 我们 xlsx 字节差异) | ✅ |
| **v27.8.1.9** | 后处理 inlineStr → sharedStrings · 处理 `&#NNNN;` numeric char ref 双重 escape 坑 | ✅ |
| **v27.8.1.10** | 🔬 服务器端字节级自诊断 endpoint(zip 文件级 diff) + UI modal + 两 xlsx 下载按钮 | ✅ |
| **v27.8.1.11** | XML 后处理 · row spans + 完全空 cell + sheet3 只 header + 去 t="n" + 重算 dimension | ✅ |
| **v27.8.1.12** | ⭐ **Korn 模板克隆方案** · 6 metadata 文件不动(workbook.xml + Content_Types + styles + theme + 2 rels MD5 跟 Korn 完全一致) · MR.ERP 推送 100% 打通 · `SI690415-001` 真进 TEST2019 库 | ✅ **真写库验证** |
| **v27.8.1.13a** | 凭据 modal 重构(登录信息分组 / 公司备注→公司名称 / comidyear-seldb 折叠) + 字段映射 UX(「ERP 端编号」→「客户在 ERP 里的编号」+「怎么找客户编号」引导)+ **OCR 上传自动归属当前选中客户 bug 修复** | ✅ |
| **v27.8.1.13b** | 凭据 modal 测试连接 → 自动探测账套(POST /api/erp/mrerp/list-databases + selectdb.php 解析 + 单账套自动选 / 多账套 radio chip · 不再要用户填 comidyear/seldb) | ✅ |
| **v27.8.1.14a** | dev 调试入口 · 抓 MR.ERP 任意页(skin 白名单 · 反向工程基础) | ✅ |
| **v27.8.1.14a.1** | dev 调试入口 · 抓 MR.ERP 客户列表 POST 翻页(showdata.php 通用 pattern 反向工程) | ✅ |
| **v27.8.1.14b** | 🔥 OCR 抽屉推送失败 mini modal 内联引导 · 拉 combrhcus 客户表 + 模糊匹配 + 手动输入备份 + 自动重推 | ✅ |
| **v27.8.1.14b.1** | hotfix · 错误码归一(`no_customer_mapping` → `no_client_mapping`)· 让 mini modal 真能弹 | ✅ Korn 0006 真实推送验证 |
| **v27.8.1.14b.2** | A · 上传识别页 "已自动保存到单据记录" banner · B · 单据记录页客户过滤 banner · mini modal 顶部加 OCR 买方名展示 | ✅ |
| **v27.8.1.14b.3** | 🧹 UX 减重 · 砍重复客户过滤入口(banner + 历史页死下拉)· 顶栏成 Single Source of Truth | ✅ |
| **v27.8.1.14c** | 数据源从 combrhcus(分支表)切到 **armas(真客户主表 · AR Master)** · 深度栈精确抓顶层 span 避开 URA hover 嵌套 · 自动识别 6 列 combrhcus / 8 列 armas | ✅ Korn 真客户进下拉 |
| **v27.8.1.14d** | 🎯 OCR 买方名 → armas 客户名模糊匹配 → 推荐排前 · 归一化(去公司后缀 จำกัด / 株式会社 / Co.,Ltd / 等)+ SequenceMatcher · score≥0.7 加 「🎯 推荐」橙标 · 0.45+ 加「📌 可能」黄标 · 4 语 i18n | ✅ |

**v14d 窗口最大成果**:
- ✅ **MR.ERP 整链路用户旅程完美闭环**(从凭据 → 上传 → 推送 → 失败内联引导 → 自动重推全通)
- ✅ Korn 实测 0006 真客户推送验证
- ✅ 反向工程 armas / showdata.php 通用 pattern(铁律 61 锁定)
- ✅ 字段对照表 = 后台页 · 99% 用户从 mini modal 走(铁律 62 锁定)
- ✅ 智能匹配算法精度高(无关 0.18 / 包含 0.85 / 完美 1.000)

---

### 🔥 P0-A · MR.ERP 全链路完美化 · v15→v22(9.5 天 · 本窗口全采纳排前)

**来源**:`Pearnly_票据到ERP归档_用户旅程分析_v118_27_8_1_14d.md` · v14d 窗口拍板"MR.ERP 相关全部排前"

#### ✅ v118.27.8.1.15 · 批量 500 张 + plan 调整 + 自动推 toggle 默认开 + 新用户引导(1d) — **完成 + 测试通过**

后端:
- [x] PLAN_CONFIG max_upload_files 全档调:trial 15→30 / monthly 30→500 / yearly 50→800 / lifetime 100→1000 / **admin 999→9999**(必须 admin >= lifetime · 否则升级时变量倒挂)
- [x] legacy plan alias 同步(free/pro/firm/enterprise)
- [x] ERP 新建表单后端 auto_push 默认 true

前端:
- [x] `getMaxFiles` 同步 plan 上限
- [x] 大批量进度条 IIFE(>100 张 · 显示「已识别 X/Y · 剩余约 N 分钟」)
- [x] `beforeunload` 警告
- [x] >100 张首次一次性 toast「约 N 分钟 · 可切去做别的 · 完成自动保存」
- [x] ERP 对接页首次引导 modal「开启自动推送 = 0 操作上 ERP」+ [开启] [稍后] + localStorage 防重弹
- [x] 4 语 i18n × 9 词条 · cache bust 11828124

#### ✅ v118.27.8.1.16 · score=1.0 零点击 + 0.7-0.97 中分 undo toast(0.6d) — **完成 + 测试通过**

后端:
- [x] `_normalize_buyer_name`(去公司后缀 4 语:จำกัด/บริษัท/Co.,Ltd/株式会社/有限公司 等)
- [x] `_match_buyer_score`(1.0=exact / 0.85=双向子串 / 0.0-0.84=SequenceMatcher)
- [x] `_rank_customers_for_buyer`(按 score 降序 + auto_select_code 唯一性保护)
- [x] `/api/erp/mrerp/customers` 加 buyer_name 参数 · 返 auto_select_code / auto_select_name / auto_select_score

前端:
- [x] mini modal `_fetchAndRender` 拿 auto_select_code → `_autoApplyPerfect` 静默保存 + onSelected 自动重推(零点击)
- [x] score 0.7-0.97 中分 `_quickConfirmMidScore` 弹右下角 undo toast(深色底 + 进度条 · 3 秒倒计时 + [改一下] / [没问题])
- [x] `_renderList` 加 score 徽章 · ≥0.7 橙「推荐」/ ≥0.45 浅黄「可能」
- [x] CSS `.mrerp-pick-cus-row-match.match-recommend/match-maybe` + `.mrerp-undo-toast`
- [x] 4 语 i18n × 6 词条 · cache bust 11828125

**预警**(已留 v17 修):v16 子串规则太松 · 短串挂中长串假阳性(Random XYZ Co · 3 字符占 9 字符 0.33 仍触发 0.85)。

#### ✅ v118.27.8.1.17 · 商品对照表 stkmas + detail 行真 product_code + 子串闸 fix(1.5d) — **完成 · 已部署 · 等测试**

后端:
- [x] DB:`erp_product_mappings` 表(tenant_id / erp_type / item_name / item_name_norm / erp_code / erp_name)+ 4 CRUD(list / upsert / delete / find_batch)+ `_product_name_norm_for_db` 归一化
- [x] `get_mrerp_mappings_bundle` 加 `products` key
- [x] `_MRERP_PRODUCTS_CACHE`(5 分钟 TTL)
- [x] `_parse_mrerp_products_html`(自适应列数)
- [x] `_mrerp_fetch_products_raw`(走 stkmas /allview.php?idmenu=24 · 同 customers showdata pattern)
- [x] 4 endpoints:`GET /api/erp/mrerp/products?item_name=X` / `GET/POST/DELETE /api/erp/mappings/products` / `POST /api/erp/mrerp/products/check`(批量预检)
- [x] **v16 子串闸 fix**:`_match_buyer_score` 加门槛 · 子串规则只在 `min(len)/max(len) >= 0.5` 时给 0.85 · 否则降级 SequenceMatcher(铁律 63)

前端:
- [x] `_pushOne` 顶部 hook `_checkProductsBeforePush`(mrerp / mrerp_direct 都拦)
- [x] `_runProductMappingFlow`(unmapped item 串行处理 · idx++ · 全完后 toast + 自动重推)
- [x] `openMrerpPickProduct` 独立 IIFE(350+ 行 · 完美匹配零点击短路 + 「第 i/n 个待配」进度提示 + 跳过 + 取消按钮 + 4 语 subscribeI18n)
- [x] CSS `.mrerp-pick-prod-*` 完整样式
- [x] 4 语 i18n × 19 词条 · cache bust 11828126

服务器(**不进 deploy.sh · 必须 Zihao 单独 scp 覆盖**):
- [x] `mrerp_xlsx_generator.py` 加 `_norm_product_name` + `_build_product_lookup` + `_resolve_product_code` 三个 helper
- [x] `build_sales_credit_detail_rows` 循环外建 lookup 一次(O(N))· 内循环 O(1) 查 item.name 写入 row 的 `product_code` 字段
- [x] 下游 `_generate_xlsx_sales_credit_korn_clone` 现有 `row_data.get('product_code') or '123'` 自然生效

**未做**(v17 范围 BACKLOG 写了 · 但实际推到 v18):
- [ ] 字段对照表加 `product` 子 tab(后台审计)· 推到 v18 · 理由:99% 用户从 mini modal 走 · 不阻塞主路径 · 铁律 62

#### ⏳ v118.27.8.1.17.1 · 租户管理 6 bug hotfix(0.3d) — **完成 · 待部署测试**

来源:用户截图报「Earn 给 18685123459@163.com 升级年付 · 顶栏显年付 364 天 · 设置页仍显月度订阅 + 有效期 —」。本窗口深度排查 SaaS 租户管理一致性 · 找出 6 个 bug 一起修。

- [x] **Bug 1**:`_build_user_info` 只读老 `users.expires_at` 不读 `plan_expires_at` → 修:返字段加 `plan_expires_at` · `expires_at` 优先取 plan_expires_at fallback 老列
- [x] **Bug 2**:前端 settings 页 plan 分支只覆盖老 pro/team/firm/enterprise · 新名 monthly/yearly/lifetime 走兜底「月度订阅」 → 修:加 3 个 plan 分支 + lifetime「永久」
- [x] **Bug 3**:员工继承老板只继承 plan 字段 → 修:SELECT 多列同时取 plan_expires_at / trial_expires_at / monthly_quota(铁律 65)
- [x] **Bug 4**:`admin_upgrade_user` 漏更 `tenants.subscription_expires_at` → 修:UPDATE tenants 加该字段(铁律 66)
- [x] **Bug 5**:`_build_user_info` 读 `tenant_info["trial_expires_at"]` 幽灵字段(tenants 表无此列) → 修:改用员工继承的值或 user 表自己的值(铁律 67)
- [x] **Bug 6**:`/api/me/plan` vs `_build_user_info` 字段不一致 SSoT 违反 → 修:`_build_user_info` 加 `plan_expires_at` / `plan_days_left` 字段对齐前者(铁律 64)
- [x] 前端 4 语 × 5 新词条:settings-sub-monthly / yearly / lifetime / settings-days-left / settings-lifetime-forever
- [x] 设置页有效期显示形如「2027/05/12 · 还剩 364 天」· lifetime 显「永久」
- [x] cache bust 11828127

**测试要点**(给下个窗口接力):
1. Earn 后台升 `18685123459@163.com` 到年付 → 设置页应显「年度订阅 / 日期 · 还剩 N 天」(不再「月度订阅 / —」)
2. 同账户建员工 · 员工登录 → 设置页应跟老板一致(继承生效)
3. 同步看顶栏 banner-yearly 跟设置页有效期数字应**完全相等**(SSoT 验证)
4. 切语言 4 个新词条立即变

---

## ⏸️ P0-A 剩余版本 · MR.ERP 全链路(暂停 · 等 P0-VAT 完成接力)

> **暂停日期**:2026-05-12
> **暂停原因**:P0-VAT 销项税对账升最高优先级 · 本章节 5 版(v118.27.8.1.18 → v22)总计 7.5 d 全部暂停 · 等 P0-VAT(14-18 d)完成 + Korn 验收通过后恢复
> **恢复时机**:P0-VAT v118.33.1 完成 + Korn 老师验收通过
> **下面 5 个版本规划保留 · 但开发不动工 · 等接力**

#### ⏸️ v118.27.8.1.18 · OCR 买方名 → Pearnly 客户智能归属 + 学习供应商映射 + 字段对照表 product subtab(1.4d) — **暂停 · 等 P0-VAT 接力**

**痛点**:多客户混合上传 / 被动入口(IMAP/LINE/文件夹监听)归属粗糙 · 完全依赖顶栏切换器。

**额外补做**(v17 遗留):字段对照表加 `product` 子 tab(0.3d)· 复用现有 erp-map-subtab 模式 · 列展示 item_name / erp_code / erp_name · 后台审计用 · 99% 用户不进。

后端:
- [ ] OCR 完成后新增 `_smart_assign_client(buyer_name, tenant_id)` · 用 14d 的 `_mrerp_match_score` 函数算 buyer_name vs 每个 Pearnly 客户 name 的相似度
- [ ] score = 1.0 → 自动归属(覆盖顶栏选中)· 写 `ocr_history.client_id`
- [ ] score = 0.7-1.0 → 自动归属 + 标记 `smart_assigned_flag` 字段
- [ ] score < 0.7 → 回退到顶栏当前选中(13a 现状)
- [ ] 新表 `supplier_client_mapping`(tenant_id / supplier_tax_id / supplier_name / client_id / created_at)· 用户手动改归属 → 自动写入
- [ ] 下次同税号供应商 → 直接用历史归属(优先级高于模糊匹配)

前端:
- [ ] 单据记录列表 `smart_assigned_flag` 行加灰色提示「自动归属 [X] · [点改]」
- [ ] 4 语 i18n

**好处**:**多客户混合可解 · IMAP/LINE 归属精准 · 老客户场景 100% 自动归属**

#### ⏸️ v118.27.8.2 · ERP 主页 UI 三件套(2d) — **暂停 · 等 P0-VAT 接力**

**继承铁律 45**(原版规划保留 · 完整映射 UI 已被 mini modal 替代 · 删除):

- [ ] **统计区**:接 `/api/erp/stats/today` · 4 KPI 卡(今日已推绿 / 待推黄 / 失败红 / 自动化率蓝)· 数字大字 · 点击跳推送日志对应筛选
- [ ] **连接器卡片**:复用 `.erp-connect-card` 基类(铁律 48)· 完整 ERP 列表 · 虚位卡(FlowAccount/PEAK/QB 灰色 disabled)
- [ ] **推送日志**:接 `/api/erp/push-log` · 表格 + 时间筛选(今天/本周/本月/全部)+ ERP 筛选 + 状态筛选 + 单号搜索 · 失败行「解决」按钮跳 OCR 抽屉
- [ ] 三处必须显眼「也支持手动导入」(连接器卡片旁 / 凭据 modal 顶部 / 推送失败 toast)
- [ ] 4 语 i18n

**注**:默认值设置 modal(仓库/部门/销售员)**砍掉** —— 14b 已决定写死默认值 · 99% 用户不动。如果未来 1% 用户要改 · 走「字段对照表」后台页(铁律 62)。

#### ⏸️ v118.27.8.3 · 推送预览 + 凭据失效检测 + 失败自动降级 xlsx(1.7d) — **暂停 · 等 P0-VAT 接力**

**继承原 v27.8.3** + 拆细:

- [ ] **推送预览页**:推送前展示要推的 xlsx 内容(客户码 / 商品码 / 数量 / 金额 / 税额)· 每字段可改 · [取消] / [改为 xlsx 手动导入] / [推送 ✓] · 用户在 ERP 对接页有 toggle "推送前预览"(新用户默认开 / 老司机默认关)
- [ ] **凭据失效检测**:推送失败时识别 MR.ERP 返回的 "密码错" 信号 · 返回 `mrerp.credentials_expired` · 前端弹「MR.ERP 密码可能改过了 · 请重新输入」+ [重新输入] [先用 .xlsx]
- [ ] **失败自动降级 .xlsx**(铁律 44 闭环):推送失败时自动调 `mrerp_xlsx_generator.py` 生成 xlsx · 存 `push_log.xlsx_b64` · toast「自动生成了 xlsx · [下载手动导入到 MR.ERP]」
- [ ] 4 语 i18n

#### ⏸️ v118.27.8.4 · 真实可达性测试(0.5d) — **暂停 · 等 P0-VAT 接力**

**继承原 v27.8.4** · 范围不变:

- [ ] 用 skin OAuth 测试号 + MR.ERP test01 跑 5 张 OCR 单据全推流程
- [ ] 验证首次成功率 ≥ 60% · 第二次起 ≥ 90%(改一些字段后)
- [ ] 验证 fallback 路径 · 故意填错凭据 · 验证降级到 .xlsx 兜底

#### ⏸️ v118.27.8.5 · 重复防护 + 批量推送 + ERP 链接 + LINE 推老板(1.9d) — **暂停 · 等 P0-VAT 接力**

**合并原 v27.8.5 通用增强 + 本窗口新建议**(优化 11/12/13):

**重复推送防护(idempotency)**(原 v27.8.5):
- [ ] `ocr_history` 表加 `last_pushed_at` + `last_pushed_target` 字段
- [ ] 推送前检查:同一 history_id 已推过同一 target · 弹确认「已推过 X 次 · 还要再推吗?」
- [ ] 列表行显示「✓ 已推」徽章 + last_pushed_at 时间

**批量推送 + 全部失败重推**(本窗口新):
- [ ] 单据记录列表加 checkbox 选 N 张 · 顶部加 [批量推送 MR.ERP] 按钮
- [ ] 推送日志页加 [重推全部失败] 按钮(按筛选条件)
- [ ] 失败重试上限 5 次(防队列爆 · 超限 admin 告警)
- [ ] 大批量限速(>50 张时客户端限速 + 服务端队列)

**MR.ERP 链接 + LINE 推老板**(本窗口新):
- [ ] 后端推送成功后 · 拿到 MR.ERP 返回的 `arso/artran` 内部 ID
- [ ] 拼接 URL:`https://mrerp4sme.com/arso/allform.php?id=N` · 存 `push_log.erp_target_url`
- [ ] toast 加「✅ 已推 · [看 MR.ERP →]」链接
- [ ] 老板配 LINE 通道 · 每日推「今天 Pearnly 帮你推了 N 张到 MR.ERP · 总额 X 泰铢」
- [ ] 每周 / 每月推送报告(PDF / 邮件 · 老板视图)

**错误友好化**(原 v27.8.5):
- [ ] HTTP 422 等技术 error → 业务化文案 4 语映射

**好处**:**月底批量处理效率 10× · 财务防错 · 老板感知 Pearnly 价值 · 续费率提升**

---

### 📊 P0-A 操作数对比(用户旅程优化后)

| 场景 | 现状(v14d 后)| P0-A 完成后 | 减少幅度 |
|---|---|---|---|
| **日常 · 已熟客户 + 自动推 toggle 开** | 0-1 次 | **0** | -100% |
| **日常 · 新客户 score=1.0 完美匹配** | 2 次 | **0** | **-100%** ★★ |
| **日常 · 新客户 score 0.7-1.0** | 2 次 | **0-1**(toast 默认确认) | -50%~-100% |
| **日常 · 新客户 score < 0.7** | 2 次 | 2 次(不可压) | 同 |
| **异常单复核 5-20%** | +1 次 | +1 次(不可压) | 同 |
| **批量 50 张** | 50 次 | **1 次批量推** | **-98%** ★ |

**核心目标**:80% 用户场景"想 0 次"· 20% 用户场景"想 1 次"· 0% 用户场景"想 2+ 次"

---

### ✅ 旧版 v27.8.1.13-15 范围归档(已由本窗口完成 + 重排)

~~原计划 v27.8.1.13 P0 简化~~ → ✅ 由 v13a/13b 完成
~~原计划 v27.8.1.14 P1 主数据自动抓取~~ → ✅ 由 v14a/14a.1/14b/14b.1/14b.2/14b.3/14c/14d 完成(实际偏离原方案:不建 erp_master_cache 表 · 改内存缓存 5 分钟 / 不在测试连接后预热 · 改按需拉 / 不弹 top 3 modal · 改 mini modal 显示全部 + 智能推荐排前 · 更优)
~~原计划 v27.8.1.15 P2 商品对照表~~ → 推到 **v17**(本次重排 · 让 v15 留给批量上传)
~~原计划 v27.8.1.16 webhook 卡片化 + 砍蓝按钮~~ → 降到 **P1**(非 MR.ERP 闭环必须 · 见后段)
~~原计划 v27.8.2 完整映射 UI~~ → **删**(已被 mini modal 替代 · 铁律 62)
~~原计划 v27.8.3 推送预览 + Fallback + 凭据失效~~ → 并入新 **v20**
~~原计划 v27.8.4 真实可达性~~ → 同 **v21**(版本号不变)
~~原计划 v27.8.5 ERP 推送通用增强~~ → 并入新 **v22**(+ 本窗口新建议)

---

## 🟡 P1 · 公测前 / 战略(MR.ERP 完成后做)

### v118.27.8.6 · webhook 卡片化 + 虚位卡 + 砍蓝按钮(0.5-1 天)

> 原 v27.8.1.16 · 从 P0 降到 P1 · 因为不是 MR.ERP 闭环必须 · 视觉重构属优化

- [ ] webhook 复用 `.erp-connect-card` 基类 · 跟 Xero/MR.ERP 卡片视觉一致
- [ ] 「虚位卡」展示「即将」连接器(FlowAccount/PEAK/QuickBooks 灰色 disabled)
- [ ] 砍掉旧「+ 新增端点」蓝色按钮
- [ ] 改为「+ 添加连接器」 · 点了弹选择器
- [ ] 字段对照表的「ERP 系统」选择列在只 1 个 ERP 已连接时隐藏(冗余)

### v118.27.2 · FlowAccount API 直推(2 天)
依赖:Zihao 拿 FlowAccount sandbox client_id + secret(MyCompany 后台)
- [ ] 用 GitHub 开源 SDK(`flowaccount/flowaccount-typescript-node-client`)
- [ ] OAuth 2.0 鉴权 + token 刷新
- [ ] 销售单 / 采购单 / 客户主数据 推送接口
- [ ] 接 v118.27.0 映射底座

### v118.27.3 · PEAK API 直推(2-3 天)
依赖:**PEAK partnership 邮件回**(Zihao 给 `info@peakengine.com` 发):
- [ ] 申请 sandbox + API 文档
- [ ] 看是否有付费门槛
- [ ] 拿到文档后 ~2 天实现

### v118.27.4 · Xero OAuth 2.0 直推(已完成 ✅ + 后续增量)
- [x] **v27.4** OAuth 2.0(Web app · 标准 REST · `https://developer.xero.com/`)· 推 ACCREC Invoice DRAFT · 错误码 4 语 ✅
- [x] **v27.4.1** scope broad → granular(2026-03-02 后新建 app 强制 · 见铁律 44)✅
- [ ] **v27.4.2** Xero 端自动建 Contact(1 天 · v27.4.1 测完后做 · 解决 Contact not found 阻塞)
- [ ] **v27.4.x** 多 organisation 切换 + 推送时选 org(0.5 天)
- [ ] **v27.4.y** Xero 推 ACCPAY 采购应付(0.5 天)

### v118.27.4.QB · QuickBooks API 直推(1.5 天)
- [ ] QuickBooks Intuit Developer(`https://developer.intuit.com/`)
- [ ] OAuth 2.0 鉴权 · 类 Xero 流程
- [ ] 推 Invoice + 接 client_assignments filter

### v118.28.0 · Express 适配器(3 天)
依赖:**Express 商务联络**(Zihao 给 Express 发):
- [ ] 拿 API 文档 · 看是 REST / SOAP / FTP
- [ ] 若有 API → API 直推 · 若没 → 走方案 A xlsx 兜底

### v118.28.1 · 「我的 ERP 是 ___」反馈框 + admin 汇总(0.5 天)
- [ ] 配置页加自由输入框
- [ ] Earn `/admin` 加汇总 tab(按 ERP 名分组用户数 + 月排行)
- [ ] 公测反馈反推下一波 ERP 适配优先级

### v118.28.2 · ERP 推送通用增强(2 天)
- [ ] 失败重试上限 5 次(防队列爆)
- [ ] 推送日志按客户 + 月份 + 状态 3 维度筛选
- [ ] 错误 reason 4 语友好文案映射(全 ERP 通用)
- [ ] 推送成功返回 ERP 端的链接(可点跳转)
- [ ] 「这张已推过」徽章在历史列表
- [ ] ERP 端点「连接测试」按钮 + 后台定时探活

---

## 🔥 第 3 优先级 · 审计报告大整改清单(2026-05-08 ~ 09 累积 · 本窗口确认全部采纳)

> **来源**:之前窗口讨论的 ERP 对接审计 + 用户管理 UI 评审 · 用户拍板「全部采纳 · 写进清单」
> **执行**:依次落实 · 部分已合并到 v27.8.1.13-15 / v27.8.5 / v29.x · 其余按版本顺序排

### 审计 A · ERP 对接漏掉的高频场景(10 个)

| # | 场景 | 大厂参考 | 状态 / 落地版本 |
|---|---|---|---|
| 1 | 客户 ↔ ERP customer_id 映射表 | FlowAccount / Xero | ✅ v27.0 已上 |
| 2 | 科目映射(GL Code Mapping) | QB Auto-categorization | ✅ v27.0 已上 |
| 3 | 税码映射(VAT 7%/0%/免税/进销项) | 用友 T+ / Xero | ✅ v27.0 已上 |
| 4 | 批量重推「全部失败的」一键 | Xero / QB | ⏳ v27.8.5 |
| 5 | **重复推送防护(idempotency)** | 大厂全有 | ⏳ v27.8.5 |
| 6 | 推送预览(dry-run) | Odoo / 用友 | ⏳ v27.8.3 |
| 7 | 凭证日期 vs 发票日期分流 | 用友 T+ / 飞书 | ⏳ v27.8.5 |
| 8 | 多币种(THB/USD/EUR) | Xero 强项 | ⏳ v27.9 |
| 9 | 推送审批流(员工提 + 老板审) | FlowAccount Pro | ⏳ v29.x |
| 10 | 本月推送仪表盘(总数/失败/成功/金额) | 大厂全有 | ⏳ v27.8.2 三件套 |

### 审计 B · ERP 推送隐藏 bug(7 个)

| # | bug | 触发 | 落地版本 |
|---|---|---|---|
| 1 | 自动重试无上限 | 一直失败 | ⏳ v27.8.5 |
| 2 | history.client_id NULL 时推送 | 客户被删 | ⏳ v27.8.5 |
| 3 | 大批量没限速 | 一次推 100+ | ⏳ v27.8.5 |
| 4 | ERP 端点 down 没 health check | 厂商挂 | ⏳ v27.8.5 |
| 5 | 日志按时间排 · 不按客户分组 | 月底审计 | ⏳ v27.8.2 三件套 |
| 6 | 失败 reason 是英文技术 error | HTTP 422 | ⏳ v27.8.5 |
| 7 | 推送成功无「ERP 那边的链接」 | 总是 success | ⏳ v27.8.5 |

### 审计 C · ERP 对接 UX 小毛病(5 个)

| # | 毛病 | 修补 | 落地版本 |
|---|---|---|---|
| 1 | ERP 端点列表没分组 | 按 type(销售/采购/凭证)分组 | ⏳ v27.9 |
| 2 | 推送日志没按「客户/月份/状态」筛选 | 加 3 个筛选 chip | ⏳ v27.8.2 三件套 |
| 3 | 没有「连接测试」按钮 | 已部分实现(test-connection) | ✅ 部分 |
| 4 | 没有「这张已推过」提示 | history 表加 last_pushed_at + 列表徽章 | ⏳ v27.8.5 |
| 5 | 推送规则全局 · 没法按客户单独配 | rule 加 client_id 维度 | ⏳ v27.9 |

### 审计 D · 用户管理 UI 评审(8 个 P0/P1)

| # | 痛点 | 严重度 | 落地版本 |
|---|---|---|---|
| 1 | 无搜索 · 无分页 · 无筛选 | 🔴 致命 | ⏳ v29.1 |
| 2 | 无用户详情(只看列表) | 🔴 致命 | ⏳ v29.1 |
| 3 | 无 tenant 维度视图 | 🟡 中 | ⏳ v29.3 |
| 4 | 无操作审计 | 🔴 致命 | ✅ v29.0 已上 |
| 5 | 无批量操作 | 🟡 中 | ⏳ v29.1 |
| 6 | 无数据导出 | 🟢 低 | ⏳ v29.1 |
| 7 | 删除账号一键就执行 | 🔴 致命 | ✅ pearnlyConfirm 已上 |
| 8 | 无异常监控(登录失败 / API 滥用) | 🟡 中 | ⏳ v29.4 |

### 审计 E · 大厂调研沉淀的共性提炼

每家(Stripe / Linear / Notion / Vercel / 飞书 / GitHub Enterprise / Slack / Atlassian)都做的:

1. **列表必带分页 + 搜索 + 多维筛选** → v29.1
2. **详情抽屉**(不打断列表上下文) → v29.1
3. **操作审计日志独立模块** → ✅ v29.0
4. **危险操作多重保护**(软删除 / 二次确认 / 影响预览) → ✅ pearnlyConfirm 已上 + 软删除待 v29.x
5. **批量操作支持** → v29.1
6. **URL 状态化筛选**(链接可分享给同事)→ v29.1
7. **异常活动告警** → v29.4

### 审计 F · 用户体验对标 6 大厂(具体做法 · 抄 / 放大)

| 厂商 | 他们做的我们没做 | 我们超过 |
|---|---|---|
| **FlowAccount** | 客户/科目/税码全自动映射(基于历史)· 推送审批流 | 多语言 OCR · 多 ERP 中立 |
| **Xero** | Smart Bank Rules · Hubdoc 多端集成 · 完整 audit | 一页多发票 · 泰文 RD 验真 |
| **QuickBooks** | Auto-categorization(AI)· Recurring rules · Two-way sync | OCR 速度 5-10× |
| **Odoo** | 双向同步 + Server actions + 完整 audit | UI 上手快 |
| **用友 T+** | 智能凭证模板 · 税务申报联动 ภ.พ.30 | 多 ERP 中立 |
| **飞书多维表格** | 表格视图 + 公式字段 + 自动化规则面板 | 启发:加「表格视图」批改 OCR |

> 「他们做的我们没做」整理进 BACKLOG · 排 v27.8.5 / v27.9 / v29.x。

---

## 🟢 P0 公测启动并行(0.5 天)

### A.1 Git 远程私库 push ✅ 完成(2026-05-17)
- [x] 在 GitHub 创建私有 repo → `github.com/skin306152-star/pearnly-app`
- [x] `.gitignore` 配置完成(`.env` / `*.tar.gz` / `__pycache__` / `uploads/` 等)
- [x] 服务器 deploy key 配置(`/root/.ssh/github_pearnly`)
- [x] GitHub Webhook 接口(`POST /internal/deploy`)写入 app.py
- [x] 服务器 `/opt/mrpilot/git-deploy.sh` 部署脚本
- [x] CLAUDE.md 部署铁律更新为 Git Push 流程
- [x] 首次 push 成功 · 38 个文件上传 GitHub
- [x] GitHub Webhook 配置 `https://pearnly.com/internal/deploy`
- [x] 端到端测试通过 · push → 自动部署 → 版本更新 · 全程零 SSH
- 目的:代码自动备份 · fail2ban 问题永久消失 · 自动部署 ✅ 全部达成

**Git 全自动部署已完全通 · fail2ban 问题永久解决**

---

## 🔵 P1 浏览器扩展平台 · 公测后做(15-18 天)

### v118.31.0 · 浏览器扩展框架(8-10 天)
- [ ] Chrome 扩展骨架(manifest v3 + content scripts + background)
- [ ] 监听 Pearnly 推送通知 → 检测当前 tab 是否在 ERP 入口页
- [ ] DOM 选择器规则引擎(json 配置每家 ERP 的字段映射)
- [ ] OAuth 接 Pearnly 账号
- [ ] 4 语 UI

### v118.31.1 · MR.ERP web 自动点击(3-4 天)
- [ ] 写 MR.ERP 的 DOM 选择器 + 字段映射 json
- [ ] 自动打开 `/impartran/formrdpc.php` 销售导入页
- [ ] 自动选文件 + 点导入按钮
- [ ] 弹窗自动点确认 / 失败标记返回

### v118.31.2 · SMEMOVE / Business Plus 适配(各 2-3 天)
- [ ] 分别写 DOM 选择器 + 字段映射

### 维护成本预估
- 每年 5-10 天 · ERP UI 改版就要更新 DOM 选择器
- 但比单做一家 MR.ERP 性价比高得多(平台能力复用)

---

## 🟢 P0.5 大厂调研抄回来的(v2 · 2026-05-09 新增 · **版本号顺延 2 号 · 等 P0-VAT 完成**)

> 来源:PEARNLY_ERP_RESEARCH_2026_05.md v2 第八节 · 抄 Stampli / 大厂业界做法
> **2026-05-12 版本号调整**:原 v118.32-34 已让位给 P0-VAT 销项税对账 · 本章节顺延为 v118.34-36

### v118.34 · 三角对账(银行↔ERP↔Pearnly)· 5 天 ·(原 v118.32 · 已顺延)
- [ ] 三方数据源对照视图:银行流水 / ERP 已记账 / Pearnly OCR 识别
- [ ] 自动找差异:ERP 已记 + 银行未到 / Pearnly 已识别 + ERP 没的 / 银行有 + 双边都没
- [ ] 差异列表 + 逐条解决(忽略 / 补登 / 重 push ERP)
- [ ] 价值:L3 跨系统对账 · 大厂没有面向事务所的这视角 · 高客单价支撑
- [ ] 抄 Stampli "ERP-aligned" 思路:从 ERP 拉数据 · 不强迫客户改 ERP

### v118.35 · immutable audit trail · 3 天 ·(原 v118.33 · 已顺延)
- [ ] 所有关键操作(OCR 识别 / 推 ERP / 用户分配 / 升级套餐 / 删除发票)写不可改 audit_log 表
- [ ] WHO 做了 / WHEN / WHAT / IP / 之前值 / 之后值
- [ ] 老板视图:看自己 tenant 的全部操作记录
- [ ] 超管视图:看任意 tenant
- [ ] 抄 Stampli "complete immutable audit trail" + 合规需求(泰国会计法保留 5-10 年)

### v118.36 · AI 自动 GL coding(轻量版)· 7 天 ·(原 v118.34 · 已顺延)
- [ ] 学一段时间(异常栏 5 类规则)后 · 主动猜下一张发票应该走哪个会计科目
- [ ] 高置信度自动填 · 中置信度提示 · 低置信度问用户
- [ ] 用户接受 / 拒绝都反喂学习
- [ ] 抄 Stampli Billy(83M 小时学习) / Ramp AI 简化版
- [ ] 暂用 OpenAI / Gemini 简单 prompt + 历史规则 · 不上 fine-tune

---

## 🟡 P2 暂停 / 推后(等 ERP 闭环)

### v118.26.3 · 银行对账拖拽匹配 + 一键确认(1.5 天)· ⏸️
- [ ] 发票卡片拖到流水行 → 创建匹配
- [ ] 一键确认所有「高置信度」匹配 · 撤销 / 重做

### v118.26.4 · Excel/CSV 银行流水解析 + tab 简化(0.75 天)· ⏸️
- [ ] xlsx / csv 解析(继承 OCR 上传管道)
- [ ] 银行 5 行:KBANK / SCB / BBL / KTB / 通用 · 自动列名映射
- [ ] 简化对账页 tab 结构

### v118.29.x · 用户管理深化(3.6 天)· ⏸️ 公测后
- [ ] v29.1 批量 + 抽屉深化 + 跨时区(1.3 天)
- [ ] v29.2 主用户角色补完(0.8 天)
- [ ] v29.3 tenant 聚合视图(0.7 天)
- [ ] v29.4 权限矩阵 + 登录锁 + 紧急超管恢复(0.8 天)

### v118.30.x · 老板看板(L4)+ 风控告警(L6)+ 合规导出(L5)· ⏸️ ERP 闭环后(7-10 天)
- [ ] 老板看板:本月概览 4 KPI + 供应商 TOP 3 + 智能告警 + 现金流预测(L4)
- [ ] 风控告警:假发票 / 重复账号 / 数额突增(L6)
- [ ] ภ.พ.30 PDF 一键生成(L5 · VAT 申报)
- [ ] ภงด.3 PDF(L5 · WHT 申报)
- [ ] 客户月度对账单 PDF(L5 · 给客户签字)
- [ ] 审计师友好导出 zip(L5)

### v118.30.x · 安全合规深化(公测之后)
- [ ] Customer-Lockbox(微软首创 · 1.5 天)
- [ ] 弱密码黑名单扩展(0.3 天)
- [ ] forgot_password 客服提示(0.2 天)
- [ ] RBAC 内部多角色(3 天)

### 🛡️ v118.99.x · PDPA + 运维合规底线(P3 · 项目主体完成后做 · 2026-05-11 拍板)

> **背景**:v14d 窗口跟 Zihao 盘点客户问"数据存哪里 / 安全吗" 时发现 · 我们目前对客户说的"符合 PDPA / 99.9% SLA / SOC 2"是话术包装 · 部分是 Supabase 借势 · 不是 Pearnly 真实做到的。
> **决策**(2026-05-11):**项目主体(MR.ERP P0-A v15-v22 + P1 + P2 模块扩张)全部完成后才做** · 不在主路上抢资源。
> **顺序铁律**:**免费项全部做完 → 必须付费(只 1 项)→ 推荐付费(等真客户) → 永远不做(P3-X 砍掉)**
> **第一年总投入**:约 700 USD / 5,000 RMB / 20,000 THB(对比同行做 SOC 2 一年 50 万+ THB · 我们 1/25 成本搞定底线)

#### P3-A · 全免费项(0 元 · 累计 2.5 天)

| # | 项 | 方案 | 估时 |
|---|---|---|---|
| 1 | **隐私政策 Privacy Policy 4 语**(中/泰/英/日) | 参考 Stripe / Xero / FlowAccount 模板改写 · 写在 `static/legal/privacy.html` + i18n key 接入 | 0.5d |
| 2 | **服务条款 Terms of Service 4 语** | 同上 · `static/legal/terms.html` | 0.5d |
| 3 | **Cookie 同意 banner** | 30 行 vanilla JS · 写在 `home.html` / `login.html` · 不引 OneTrust / Cookiebot 这种 SaaS · 4 语 i18n | 0.2d |
| 4 | **DPA 模板(数据处理协议)** | 用 Supabase 官方 DPA 模板改 · 4 语版本 · 给企业客户签字用 · 上传到 `legal/dpa_template.pdf` | 0.3d |
| 5 | **数据泄露应急流程文档** | PDPA 要求 72 小时内通知用户 · 写 `docs/incident_response.md`(内部) + 4 语邮件模板(用户通知) | 0.2d |
| 6 | **DPO 数据保护官指定** | Zihao 自己挂名 · 在公司注册文件 + 隐私政策标明 · 小公司不需专聘(法律阈值是雇员 250+ 或处理大规模敏感数据) | 0d |
| 7 | **UptimeRobot 监控配置** | Free plan 50 个监控 5 分钟探活 · 配 5 个关键端点(/health / /api/me/plan / OCR / 推送 / 数据库) · LINE Bot 告警 | 0.1d |
| 8 | **cron 冷备份脚本** | bash 30 行 · 每日 `pg_dump` → 上传 Google Drive / GitHub 私库(加密) · 双备份不依赖 Supabase · 重要表保留 90 天 | 0.3d |
| 9 | **Sentry 错误监控接入** | Sentry Free Plan 5K events/月 · 前端 + 后端都接 · 错误自动上报 + LINE 告警 | 0.2d |
| 10 | **Cloudflare WAF 调优** | Free plan 自带基础 WAF · 调优规则(SQL injection / XSS / rate limit) · 不升 Pro | 0.2d |
| 11 | **OWASP ZAP 自动扫描** | 公测前手动跑一次 Zed Attack Proxy · 0 元开源工具 · 修补发现的中危以上漏洞 | 0.5d(含修补) |

**合计**:0 THB · 2.5 天工作量 · 全部 P3-A 在项目主体完成后做完

#### P3-B · 必须付费(1 项 · 880 THB/月)

| 项 | 月费 | 为什么不能省 |
|---|---|---|
| **Supabase Pro Plan** | **$25/月 = 880 THB/月** | Free Plan 致命缺陷:① **1 周不活跃自动暂停**(老用户 1 月不来 → 数据库挂)② **无 PITR**(Point-in-time Recovery · 数据丢了不可恢复)③ **500MB 限额**(几个月就到顶)④ **无 SLA**(不能对客户承诺) |

**前置动作**(Zihao 一次性 35 秒):登 `supabase.com/dashboard` 查当前 plan · 如果还是 Free · 立刻升 Pro。
**触发时机**:**第一个付费客户签约后立刻升**(在那之前用 Free 也行 · 但要承担风险)

#### P3-C · 推荐付费(公测后 + 真有付费客户后做)

| 项 | 一次/月费 | 时机 |
|---|---|---|
| **律师审 Privacy Policy + ToS + DPA** | **5,000-10,000 THB(一次性)** | 公测后 + 第一个企业付费客户签约后做 · 律师只审 · 不重写 · 用 P3-A 1/2/4 写好的模板版做底稿 |
| **Resend / Postmark 邮件服务** | $20/月 = 700 THB/月 | Gmail SMTP 限额 500 封/天 · 1000 用户内能撑住 · 限额触顶才换 · 一般公测后 6 个月内不用 |
| **DocuSign 电子签 DPA** | $10/合同 | 企业客户多了才需要 · 个体会计师不签 DPA |

#### P3-X · 严格砍掉(创业期绝对不做 · 永远拒绝)

| 项 | 厂商报价 | 不做理由 |
|---|---|---|
| SOC 2 Type II 认证 | 50-150 万 THB | 等年收入 100 万 USD 后考虑(Pearnly 远远没到) |
| ISO 27001 认证 | 30-100 万 THB | 同上 |
| 渗透测试(第三方) | 3-20 万 THB | 等签真大客户(年单 50 万 THB+)做 · OWASP ZAP 自扫够 |
| Datadog / New Relic 监控 | $500+/月 | UptimeRobot + Sentry 免费版功能 80% 重叠 |
| OneTrust / Cookiebot | $1000+/月 | 30 行自写 Cookie banner 完全够 PDPA 要求 |
| Cloudflare Pro Plan | $20/月 | Free plan 基础 WAF 够创业期 |

#### P3 落地步骤(顺序固定 · 不可换)

1. **项目主体完成确认**:MR.ERP P0-A(v15-v22) + 公测前 P1 + 公测后 P2 模块扩张全部跑完
2. **P3-A 11 项免费项**:2.5 天集中做完 · 全部上线
3. **P3-B 升 Supabase Pro**:35 秒升级 · 立刻生效
4. **公测启动 + 第一个企业付费客户签约**:触发 P3-C 律师审
5. **常态化**:每年律师过一次 · 每月看一次 Sentry / UptimeRobot 报表
6. **永远不做 P3-X**:除非年收入跃到 100 万 USD 级

#### 给客户的诚实话术(对外口径 · 已锁定)

替代之前过度包装的话术 · 公测期对外只说:

> 数据存在 **AWS 新加坡 · Supabase 托管** · 您的 MR.ERP 密码用 Fernet 算法加密(连我们后台都看到密文) · 多租户严格隔离 · 您随时一键导出全部数据。
>
> 关于合规:我们**正在对齐 PDPA 要求**(隐私政策 / 数据处理协议正在准备) · 目前还没拿 SOC 2 等正式认证 · 等公测稳定后会推进。
>
> **数据所有权 100% 是您的** · 您不续费随时可以导出走人。

⚠️ **不要说**:"符合 PDPA" / "等同 GDPR 国际标准" / "99.9% SLA" / "SOC 2 认证" —— 没正式做就是夸大 · 客户用这话告你反而麻烦。说"**正在对齐**"才安全。

---

## 🟡 P2 自动化模块(长期持续)

- [ ] LINE bot 命令面板(查配额 / 重发 / 停推)
- [ ] 邮件监听规则 UI(白名单 / 黑名单 / 主题正则)
- [ ] 文件夹监听:多文件夹 + 不同 client_id 自动归属
- [ ] ERP webhook:重试队列 + 失败告警(已部分在 v118.27.x 实现)

---

## 🟢 P3 候选 · 等真实用户反馈再决定

### v118.32.4.12 P0-VAT 高级功能(2026-05-13 拍板暂缓 · 等 v4.11 上线后 2-3 周真实会计师反馈)

**前置条件**:v4.11 必须上线 · 真实会计师试用 2-3 周 · 反馈表明这些功能确实是高频需求(不是"想要"而是"必需")

**候选清单(总 2.7 天 · 触发后 1 个版本搞定)**:
- [ ] **审计 PDF 导出(1.2 天)** · 「[客户名] 销项税对账报告 · [期间]」 · KPI 汇总 + 异常明细表 + 每张异常发票截图缩略图 + 会计师签字栏 + 4 语(默认泰文)
- [ ] **历史对比卡片(0.5 天)** · 同客户跨期"上月 X 张 · 这次 Y 张 · 异常增加 Z" · 在对账结果页底部
- [ ] **批量操作(0.5 天)** · 选行 → 标已审 / 驳回 / 全部接受匹配项 · 防呆撤销 5 秒
- [ ] **其他真实反馈衍生需求(0.5 天预留)** · 给会计师真实需求空间

**砍掉的判断标准**:
- 真实会计师试用后 < 30% 用过这些功能 → 直接砍 · 不做
- 会计师反馈"完全不需要 PDF · 把 Excel 改好就行" → 砍 PDF · 做 Excel 优化

---

## 🔵 P3 阻塞中(等外部条件)

- [ ] **MR.ERP 物料 2b 采购-现金购模板**(Zihao 让网页 Claude 补 · 7/8 已收齐) · ⛔ 卡 v118.27.1.1 的 `purchase_cash` schema(可不阻塞 v27.1.1 上线 · 物料 1 / 2a / 3 已够)
- [ ] **Xero Demo Company**(Zihao 在 xero.com → Account → Try the demo company · 5 分钟) · ⛔ 卡 v27.4.1 测试完整流
- [ ] **PEAK partnership 邮件**(Zihao 发 · 1 周内) · ⛔ 卡 v118.27.3
- [ ] **Express 商务联络**(Zihao 发 · 2 周内) · ⛔ 卡 v118.28.0
- [ ] **Google OAuth Client Secret 轮换** · 公测前(可选)
- [x] ~~LINE Login Channel 创建~~ · ✅
- [x] ~~MR.ERP 物料 1 销售-现金真模板~~ · ✅(2026-05-10)
- [x] ~~MR.ERP 物料 2a 采购货品 PG 真模板~~ · ✅(2026-05-10)
- [x] ~~MR.ERP 物料 3 会计凭证 真模板~~ · ✅(2026-05-10)
- [x] ~~MR.ERP 物料 4 错误码字典(13 条 · 部分)~~ · ✅(2026-05-10 · 网页 Claude 实测)
- [ ] **Facebook App 申请** · ❌ 已永久砍

---

## 🛠 技术债 / 顺手修

- [ ] **性能债 · `/api/me/plan` 慢 4018ms / 2835ms**(测试中心 api_slow 触发 · v27.0 部署后发现)· 加 5 分钟前端缓存 · 0.3 天 · P2
- [ ] **性能债 · Xero 卡片首次加载慢 ~20s**(v27.4 新发现 · 疑似前端串行 fetch)· 0.3 天 · P2
- [ ] `deploy.sh` 不复制 `VERSION` 文件 · 任意版本顺手补 `cp VERSION /opt/mrpilot/`
- [ ] **A.1 Git 远程私库 push**(0.5 天)· **公测前必做**
- [ ] tar.gz 打包脚本(`scripts/pack.sh`)· 杜绝多嵌一层目录
- [ ] `scripts/check_i18n.py --strict` 挂入 `deploy.sh` 第一步(可选)
- [ ] **home.js 死代码清理**(admin-modal-reset-pw 词条 4 套 / showResetPwdResult / `_admin_*_LEGACY`)· 0.2 天 · P3
- [ ] timezone / date_format / number_format 后端 schema · 0.3 天 · P2

---

## 📦 永久砍掉(从 BACKLOG 撤出)

- ❌ Mr ERP 直推对接(2026-05-10 · v118.27.1 已上线 · sales_credit 单张可用 · stub 等填空)
- ❌ Facebook 社交登录
- ❌ 超管直接重置客户密码(v118.28.7 砍)
- ❌ 老板看到员工临时密码(v118.28.7 砍)
- ❌ v27.8 全表 RLS 路线
- ❌ **桌面 RPA(D)**(2026-05-09 · 行业黑洞 · 维护 > 收益)
- ❌ **UI Automation API(E)**(2026-05-09 · 同上)
- ❌ **用友 T+ 适配**(2026-05-09 · 泰国基本无用户)
- ❌ **Tally 适配**(2026-05-09 · on-premise + API 弱)
- ❌ Xero broad scope `accounting.transactions/.settings`(2026-05-10 · 铁律 44 · granular 替代)

---

## 🧠 已完成归档场景

1. ~~Earn 自己被锁怎么办~~ → 落 v29.4 紧急超管恢复(P2 推后)
2. ~~员工被禁用后他名下的客户去哪了~~ → ✅ v28.0 + v28.1 已落地
3. ~~跨时区显示~~ → 落 v29.1 抽屉深化(P2 推后)
4. ~~tenant 改名后旧 KPI 一致性~~ → 落 v29.0 + v29.3
5. ~~LINE App OAuth 失败~~ → ✅ v28.3
6. ~~移动端 settings tabs 重叠~~ → ✅ v28.5.1
7. ~~Cloudflare 橙云拦截自建 SSL~~ → ✅ HANDOVER 铁律
8. ~~NameCheap whois pendingDelete~~ → ✅ HANDOVER 铁律
9. ~~移动端 page-head 标题逐字换行~~ → ✅ v28.5.2
10. ~~移动端历史表格中文供应商竖排~~ → ✅ v28.5.2
11. ~~移动端对账客户切换器贴左屏边~~ → ✅ v28.5.2
12. ~~LINE 登录 + Email scope 申请~~ → ✅ v28.4.x
13. ~~超管直接改客户密码合规问题~~ → ✅ v28.7 砍
14. ~~老板看员工明文密码合规问题~~ → ✅ v28.7 改成发链接
15. ~~/reset 落地页缺失~~ → ✅ v28.7.1 紧急补
16. ~~客户审计 Pearnly 内部访问~~ → ✅ v28.8
17. ~~改密后旧设备 token 还能用~~ → ✅ v28.9
18. ~~超管混在普通用户视图里有越权风险~~ → ✅ v28.2 /admin 独立
19. ~~老板没法分客户给员工~~ → ✅ v28.1 完整版含后端 filter
20. ~~银行对账左右双栏 + 自动匹配引擎~~ → ✅ v118.26.2.1(测试通过)
21. ~~Pearnly 推送 ERP 战略调研~~ → ✅ 2026-05-09 · 11 家 ERP 调研 + 二分法定调
22. ~~ERP 客户/科目/税码映射底座~~ → ✅ v118.27.0 测试通过
23. ~~ERP 字段映射搬到「自动化 → ERP 对接」~~ → ✅ v118.27.0.1
24. ~~原生 confirm() 用法不规范~~ → ✅ v118.27.0.1 加全局 pearnlyConfirm(铁律 47)
25. ~~MR.ERP xlsx 一键导出~~ → ✅ v118.27.1 sales_credit 可用 · 4 stub 等 v27.1.1 填
26. ~~Xero OAuth 2.0 + 推 Invoice~~ → ✅ v118.27.4 上线 · v27.4.1 修 invalid_scope · 等 Demo Company 测试

---

## ✅ 已完成归档

### v118.27 系列 ERP 适配器(2026-05-09 ~ 11 · 累计 28 版 · MR.ERP 整链路完美闭环)
- v27.0 客户/科目/税码映射底座 ✅
- v27.0.1 pearnlyConfirm + ERP 映射搬「自动化」+ seed 提速 ✅
- v27.1 MR.ERP xlsx 适配器(stub-first)✅
- v27.4 Xero OAuth 2.0 适配器 ✅
- v27.4.1 修 Xero invalid_scope(broad → granular)✅
- v27.4.2 - 27.7.1 抽屉 1 推按钮 / 多发票拆 / 4 模板 / dropup / 客户导出 hotfix(11 版)✅
- v27.8.0 反向工程 + mrerp_pusher.py + kms_helper.py(5 步实测全通)✅
- **v27.8.1.0** MVP · mrerp_credentials 表 + 3 endpoints + 凭据 modal ✅
- **v27.8.1.1** hotfix · setTimeout race fix ✅
- **v27.8.1.2** Korn 公式修复 + _userInfo 轮询 ✅
- **v27.8.1.3** 自动推送 toggle 端到端 ✅
- **v27.8.1.4** schema 大改对齐 Korn 真样本 ✅
- **v27.8.1.5** invoice_no `690415-001` 格式 + 下载 xlsx debug ✅
- **v27.8.1.6** 抢救式抓 MR.ERP 错误 hint(关键诊断)✅
- **v27.8.1.7** 强制 cell 物理保留 + dim spacer ✅
- **v27.8.1.8** 🧪 Korn 真样本对照测试(决定性诊断神器)✅
- **v27.8.1.9** inlineStr → sharedStrings 后处理 ✅
- **v27.8.1.10** 🔬 服务器端字节级自诊断 ✅
- **v27.8.1.11** XML 后处理对齐 row spans + 完全空 cell ✅
- **v27.8.1.12** ⭐ Korn 模板克隆方案 · MR.ERP 推送 100% 打通 · 真写库验证 ✅
- **v27.8.1.13a** 凭据 modal 重构 + 字段映射 UX + OCR 上传自动归属当前选中客户 bug 修复 ✅
- **v27.8.1.13b** 测试连接 → 自动探测账套(selectdb.php 解析 / 单账套自动选)✅
- **v27.8.1.14a** dev 调试入口 · 抓 MR.ERP 任意页(反向工程)✅
- **v27.8.1.14a.1** dev 调试入口 · 抓客户列表 POST 翻页(showdata.php pattern)✅
- **v27.8.1.14b** 🔥 OCR 抽屉推送失败 mini modal 内联引导 · 客户表 + 手动输入 + 自动重推 ✅
- **v27.8.1.14b.1** 错误码归一(no_customer → no_client_mapping)· Korn 0006 实测验证 ✅
- **v27.8.1.14b.2** 上传识别页 banner + 单据记录页 banner + mini modal OCR 买方名 ✅
- **v27.8.1.14b.3** 🧹 UX 减重 · 砍重复客户过滤入口 · 顶栏成 SSoT ✅
- **v27.8.1.14c** 数据源切到 armas(真客户主表)· 深度栈精确抓顶层 span ✅
- **v27.8.1.14d** 🎯 OCR 买方名 → armas 客户名模糊匹配 → 推荐排前 · score=1.0/0.85/0.18 区分度极佳 ✅

### v118.26 银行对账 + 用户管理修补系列(2026-05-09)
- v26.0 顶级菜单 + 当月概览 ✅
- v26.1.x 批量上传 + 列表筛选 ✅
- v26.2.0/.1 右半屏 + 自动匹配 + 客户徽章 ✅(用户测试通过)
- **v26.2.2** OCR P0 紧急修补(quota gate 早返回 · 修 v27.7 fix_orphan tenant=0 死结) ✅
- **v26.2.3** admin_upgrade_user 字段修正 + forgot_password 改 SMTP ✅
- **v26.2.4** banned/inactive 安全闸 + 员工 plan 继承 + _require_owner_or_super 懒建 ✅
- **v26.2.5** signup 3 路径同事务建 tenant(根因修复)✅
- v26.3 拖拽匹配 ⏸️ 推 ERP 之后
- v26.4 Excel/CSV 解析 ⏸️ 同上

### v118.28 系列收官(17 版 · 大厂合规 + 公测合规 9/10)
### v118.27 系列(原):登录注册 + 邮件 + 多租户(已收官)
### 早期里程碑:多语言 OCR / AP 自动化 / admin 后台 80% / 4 语 i18n 总线

---

## 📌 关键运维事件归档

### 2026-05-09 · pearnly.com DNS 全打通
### 2026-05-09 · LINE Bot Greeting message 启用
### 2026-05-09 · LINE Login Channel + Email scope Applied
### 2026-05-09 · 大厂合规底线对齐完成(v28.6/28.7/28.8 三联击)
### 2026-05-09 · 公测合规线 9/10 完成 · 只剩 Git 私库
### 2026-05-09 · VERIFY_SOP 整合进 PEARNLY_WORKFLOW_SOP
### 2026-05-09 · **战略调整 · 自动化 ERP 适配器升 P0**(银行对账 / 用户管理 / 老板看板全部排后)
### 2026-05-09 · **泰国 ERP 市场调研完成**(11 家 · API 状态 + 优先级)
### 2026-05-09 · **MR.ERP 测试环境锁定**(`mrerp4sme.com` · 8 件物料拿到 4 件 · 文件格式铁律 28-31 锁定)
### 2026-05-09 · **v118.26.2.2-2.5 紧急扑救** · 大改造 user/tenant 后连环 BUG · 4 版 hotfix · 用户测试 OK
### 2026-05-09 · **SOP §7.5 大改造后 5 步回归测试铁律新增** · 防类似事件再发
### 2026-05-09 · **大厂 ERP 对接深度调研完成 v2**(11 家 美/欧/中)· Stampli 70+ ERP / Bill.com / Ramp / Tipalti / Dext / Hubdoc / Mindee / Veryfi / 金蝶 / 合思 / 轻易云
### 2026-05-09 · **Pearnly v118.32-34 新规划**(三角对账 / immutable audit / AI 自动 GL coding)· 来自大厂调研抄(**2026-05-12 顺延为 v118.34-36** · 让位给 P0-VAT 销项税对账)
### 2026-05-10 · **v118.27.0 ERP 客户/科目/税码映射底座上线** · 3 张表 + 6 接口 + 设置页 3 tab · 测试通过
### 2026-05-10 · **v118.27.0.1 全局 pearnlyConfirm 弹窗 + ERP 映射搬「自动化」+ seed 提速 4s→<500ms**
### 2026-05-10 · **v118.27.1 MR.ERP xlsx 适配器上线**(stub-first · 4 个口子) · sales_credit 单张可用
### 2026-05-10 · **v118.27.4 Xero OAuth 2.0 适配器上线** · 连接 + 推 ACCREC Invoice + 错误码 4 语
### 2026-05-10 · **v118.27.4.1 修 Xero invalid_scope** · 2026-03-02 后新建 app 强制 granular scope(铁律 44)
### 2026-05-10 · **MR.ERP 物料拿到 7/8** · 销售-现金真模板(4 sheet)+ 采购货品 PG 真模板(3 sheet)+ 会计凭证真模板(2 sheet)+ 错误字典 13 条
### 2026-05-10 · **铁律 28 修正** · sheet 数因单据类型而异(2/3/4)· 不再统一 3 sheet
### 2026-05-10 · **铁律 44/45/46 锁定** · Xero granular scope / Demo Company 测试 / Invoice DRAFT 默认
### 2026-05-10 · **铁律 47/48 锁定** · 禁原生 confirm() / ERP 连接卡片复用基类
### 2026-05-11 · **🎉 MR.ERP 推送通道 100% 打通**(v27.8.1.12) · A 层后端模拟登录闭环 · `SI690415-001` 真写 TEST2019 库验证 · 11 次 deploy 找根因(openpyxl workbook.xml vs PhpSpreadsheet 兼容差异)· **Korn 模板克隆方案**(铁律 59 锁定)
### 2026-05-11 · **抢救式抓 MR.ERP 错误信息**(v27.8.1.6) · push log 显示 🔥 红框 · 不再盲改 schema
### 2026-05-11 · **服务器端字节级自诊断 endpoint**(v27.8.1.10) · 不依赖客户端下载 · 服务器对比 Korn vs 我们 xlsx
### 2026-05-11 · **铁律 60 锁定** · UI 文案业务化 · 「映射」→「对照」/「凭据」→「账号」/ comidyear/seldb 折高级设置 · 99% 用户不动
### 2026-05-11 · **审计报告大整改全部采纳**(用户拍板) · A/B/C/D/E/F 6 类共 35+ 项进 BACKLOG · 依次落实
### 2026-05-11 · **🎉 MR.ERP 整链路用户旅程完美闭环**(v14d 窗口 · 10 个子版本 13a→14d) · 凭据自动探测账套 / 上传自动归属 / OCR 抽屉推送失败 mini modal 内联引导(armas 真客户主表 + OCR 买方名模糊匹配推荐排前) / 自动保存映射 + 自动重推 · Korn 0006 真实推送验证 ✅
### 2026-05-11 · **铁律 61 锁定** · MR.ERP 主数据用 showdata.php 通用 pattern 抓(所有 `/X/allview.php?idmenu=N` 列表页 = 空壳 + AJAX 后填 · POST `/X/component/showdata.php` 翻页拼接)
### 2026-05-11 · **铁律 62 锁定** · 字段对照表 = 后台页 · 不是主入口(99% 用户从 OCR 抽屉 mini modal 走 · 字段对照表只给老司机审计 / 批改用)
### 2026-05-11 · **用户旅程深度分析完成**(`Pearnly_票据到ERP归档_用户旅程分析_v118_27_8_1_14d.md`) · 现状 + 优化后两套流程图 + 13 项优化建议 · 用户拍板全部采纳 + MR.ERP 相关排前
### 2026-05-11 · **P0-A 路线重排**(v15→v22 · 9.5 天) · 批量上传 + 完美匹配零点击 + 商品对照表 + 智能归属 + ERP 主页三件套 + 推送预览 + 容错降级 + 重复防护 + 批量推送 + ERP 链接 + LINE 推老板
### 2026-05-11 · **P3 PDPA + 运维合规底线拍板** · 项目主体(P0-A + P1 + P2)完成后才做 · 免费 11 项先(0 元 · 2.5 天)→ 必须付费 1 项(Supabase Pro 880 THB/月)→ 推荐付费 等真客户(律师 5-10k THB 一次性)· **永远不做**:SOC 2 / ISO 27001 / 渗透测试 / Datadog / OneTrust(创业期不碰)· 给客户的诚实话术也定下来 · 不再说"符合 PDPA"(说"正在对齐")
### 2026-05-12 · **🔥🔥 P0-VAT 销项税对账模块升最高优先级** · 来源:Korn(高级会计师)PDF SOP + Excel PROMT + BAKELAB 真样本 33 张 · MR.ERP 剩余 5 版(v118.27.8.1.18 → v22 · 7.5 d)全部暂停 · P0-VAT(v118.32.0 → v118.33.1 · 14-18 d)插队 · **完成前不做其他 P0** · 原 v118.32-34(P0.5 大厂调研三角对账 / immutable audit / AI GL)顺延为 v118.34-36 · 候选铁律 60-VAT ~ 64-VAT 待验证后写入正式铁律 · PRD 主文档 `MODULE_SALE_VAT_RECON_PRD.md` 落库

---

## 🔌 P1 · v118.30+ · D 浏览器扩展(三层架构最后一层 · 公测后启动)

> 三层架构(铁律 44):A 已在 v27.8 写 · C 已在 v27.5.3+v27.6 上 · D 是最后一块拼图
> 公测后按真实用户反馈决定何时做 · 估时 15-18 天

### 产品定位

「不愿存密码 · 但要一键推送」的中型客户 · 装 Chrome 扩展。用户保留 100% 密码控制权 · Pearnly 永远不存。

### 技术架构

```
[Pearnly OCR 完成] → [识别中心点「推 MR.ERP」]
                          ↓
          [Pearnly 后端检测用户装了扩展 · 发指令]
                          ↓
              [扩展在用户浏览器执行]
                          ↓
        [扩展用浏览器现成 PHPSESSID 直接 fetch 推送]
                          ↓
              [回报结果给 Pearnly 后端]
```

### 任务清单

- [ ] **v118.30.0** Chrome 扩展骨架(MV3 manifest · content script · background SW · popup) · 3 天
- [ ] **v118.30.1** 跟 Pearnly 后端通信协议(WebSocket / 长轮询) · 2 天
- [ ] **v118.30.2** MR.ERP web 自动注入「一键推送」按钮 · 2 天
- [ ] **v118.30.3** Xero / FlowAccount / QB web 同样的注入 · 3 天
- [ ] **v118.30.4** 扩展安装引导 + 兼容性检测(Chrome / Edge / Brave) · 1.5 天
- [ ] **v118.30.5** Chrome Web Store 提交 + 审核响应 · 2-3 天
- [ ] **v118.30.6** 错误处理 + 重试 + 推送日志 · 1.5 天
