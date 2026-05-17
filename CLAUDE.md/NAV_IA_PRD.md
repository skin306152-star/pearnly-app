# NAV_IA_PRD · 导航 IA(Information Architecture)主规范

> **拍板日期**:2026-05-15
> **作用**:Pearnly 全局导航 + 头像菜单 + Admin layout 的唯一基准
> **优先级**:P1 平行主线(不抢 P0-VAT · 嵌进 P0-VAT 间隙跑)
> **基准文件**:`D:\Users\Skin\Desktop\pearnly_project\pearnly_nav_prototype_final.html`(原型 · 唯一参考实物)
> **承接关系**:与 MODULE_SALE_VAT_RECON_PRD.md 平级 · 但视觉/账号体系是横切性约束
> **触发**:Zihao 2026-05-13 提出"现在产品凌乱不堪 · 用户找不到头"· 2026-05-15 拍板 prototype_final + 头像菜单方案

---

## 1. 背景与目标

### 1.1 问题
当前 `home.html`(v118.x)主导航存在 4 类问题:
1. **5 个"即将" badge 污染主导航**(仪表盘 / 凭证中心 / 销售发票 / 应收追踪 / 云盘同步)· 占总入口 38%
2. **核心工作流跨组分割**(上传识别在"数据处理" · 异常栏在"核心工作区" · 用户找不到头)
3. **管理员组 + 测试组占用普通用户视觉空间**(成本追踪/用户管理/测试中心)
4. **设置入口模糊**(sidebar 底部独立项 · 缺收纳器)

### 1.2 目标
- **市场标准做法**:对标 Xero / QuickBooks / Bill.com / Linear / Notion
- **简约干净**:删除"即将" badge 污染 · 业务流重排
- **方便快捷**:核心操作(上传/收件/对账)1 次点击可达
- **权限分明**:员工/老板/测试/超管 4 类账号看到不同菜单

### 1.3 不动的边界
- ❌ 不改后端 API(`/api/auth/me` 已返 `tenant_role` / `is_test_whitelist` / `is_super_admin`)
- ❌ 不动 P0-VAT 主线代码(reconciliation_matcher.py / vat_report_parser.py 等)
- ❌ 不破坏现有功能(每个功能保留 · 只重排入口)
- ❌ 不动 4 语 i18n 字典 zh→en→th→ja 顺序(只追加新 key · 按 th→en→zh→ja 写)

---

## 2. 账号体系 · 权限矩阵(拍板)

### 2.1 4 类账号

| 角色 | 谁 | tenant_role | is_test_whitelist | is_super_admin | 进哪个 layout |
|---|---|---|---|---|---|
| **员工** | 老板邀请的操作员 | `employee` | false | false | `home.html` |
| **老板** | 事务所所长 | `owner` | false | false | `home.html` |
| **skin** | 测试账号(=老板+测试白名单) | `owner` | **true** | false | `home.html` |
| **Earn** | 平台超管(铁律:永远只看 /admin) | — | false | **true** | **`/admin layout`** |

### 2.2 头像菜单可见性矩阵

| 菜单项 | 员工 | 老板 | skin | Earn(在 /admin) | 数据属性 |
|---|---|---|---|---|---|
| 头部姓名 / 邮箱 | ✓ | ✓ | ✓ | ✓ | — |
| 设置 | ✓ | ✓ | ✓ | (admin 版) | — |
| 团队成员 | ✓ 只读 | ✓ 管理 | ✓ 管理 | (admin 版) | — |
| **订阅 & 套餐** | ✗ | ✓ | ✓ | — | `data-show-if-role="owner"` |
| 键盘快捷键 | ✓ | ✓ | ✓ | ✓ | — |
| **管理员后台** | ✗ | ✗ | ✗ | ✓ | `data-show-if="is_super_admin"` |
| **测试中心** | ✗ | ✗ | ✓ | ✗ | `data-show-if="is_test_whitelist"` |
| 帮助 & 反馈 | ✓ | ✓ | ✓ | ✓ | — |
| 退出登录 | ✓ | ✓ | ✓ | ✓ | — |

### 2.3 判定逻辑
```js
// home.js · 全局启动一次
const me = await fetch('/api/auth/me').then(r => r.json());
// me.tenant_role / me.is_test_whitelist / me.is_super_admin 已有 · 不动后端
applyRoleVisibility(me);

function applyRoleVisibility(me) {
  document.querySelectorAll('[data-show-if-role="owner"]').forEach(el =>
    el.style.display = me.tenant_role === 'owner' ? '' : 'none');
  document.querySelectorAll('[data-show-if="is_test_whitelist"]').forEach(el =>
    el.style.display = me.is_test_whitelist ? '' : 'none');
  document.querySelectorAll('[data-show-if="is_super_admin"]').forEach(el =>
    el.style.display = me.is_super_admin ? '' : 'none');
}
```

### 2.4 Earn 铁律(不破)
- Earn 登录后**直接进 `/admin` 独立 layout** · 不进 `home.html` UI
- Admin layout 内部 sub-nav:平台概览 / 用户管理 / 成本追踪 / 操作日志 / API 健康度 / 退出
- 与 home.html UI **完全隔离**(不共享 sidebar · 不共享头像菜单)

---

## 3. 完整 IA 结构

### 3.1 Topbar(顶栏)
| 位置 | 元素 |
|---|---|
| 左 | Pearnly logo + workspace 标识 |
| 右(从左到右)| **🔍 搜索框(⌘K)**(v3 新)→ 客户切换器 → 头像下拉菜单 |

**顶栏搜索框 + Cmd+K 命令面板**(v3 新 · 2026-05-15 拍板):
- 点击搜索框 或 按 ⌘K(Mac)/Ctrl+K(Win)→ 弹出命令面板
- 面板含 **跳转区**(13 个主页面)+ **操作区**(新建客户/导出 Excel/切语言)
- 实时过滤(输入 "vat" / "客户" / "进项" 等即时匹配)
- ↑↓ 键移动焦点 · Enter 选择 · ESC 关闭

### 3.2 Sidebar(左侧导航)· prototype_final 基准
```
工作台标识: Pearnly 事务所
[上传发票]  ← 主操作 CTA(蓝按钮)
─────
首页
─────
销项管理 ▾
  ├ 上传发票
  ├ 发票记录
  ├ VAT 对账
  ├ 销售发票(placeholder · 不在 sidebar 上挂"即将")
  └ 应收追踪(placeholder)
进项管理 ▾
  ├ 费用总览
  ├ 添加发票
  ├ 付款凭证 PV
  └ 费用分类
─────
客户
异常 [6 红 badge]
─────
集成  ← v3 新一级入口(2026-05-15 拍板 · 从 settings.集成与连接 拆出)
```

**注**:
- 原 sidebar 底部「设置」按钮 + user-row 已删 · 收进右上角头像菜单
- 「集成」= Google Drive/Sheets/Gmail/LINE/文件夹/ERP 全部第三方授权 · 业务运营级 · 对所有角色可见(不区分员工/老板)

### 3.3 Avatar 下拉菜单(右上角 · 核心新组件)
```
┌──────────────────────────┐
│ 老板 · 老王                │
│ wang@事务所.com · 所长    │
├──────────────────────────┤
│ ⚙ 设置                    │
│ 👥 团队成员    [3 人]      │
│ 💳 订阅 & 套餐  ★owner-only│
│ ⌨ 键盘快捷键              │
├──────────────────────────┤
│ 🛡 管理员后台 [超管]★admin │
│ 🧪 测试中心    ★test       │
├──────────────────────────┤
│ ❓ 帮助 & 反馈             │
│ 🚪 退出登录                │
└──────────────────────────┘
```

### 3.4 Admin Layout(Earn 专属 · 独立)

> ⚠️ **Earn 铁律**(2026-05-15 Zihao 拍板):**Earn 不工作 · 只管用户 + 看成本** · sub-nav 只 2 项
> 原 PRD 里的"平台概览 / 操作日志 / API 健康度"已砍 · Earn 不需要

```
TOPBAR: [Pearnly 平台后台] | [Earn ▾]
─────────────────────────────
SIDEBAR:                   MAIN:
  成本追踪                  [选中页内容]
  用户管理
─────
  退出登录
```

**对应现有路由**(完全不动):
- 成本追踪 = 现有 `admin-cost`(不动)
- 用户管理 = 现有 `admin-users`(不动)

---

## 4. 8 Phase 路线图(实施切片)

### Phase 0 · 文档体系建立 ✅ 本窗口完成
- 写 NAV_IA_PRD.md(本文件)
- 改 CLAUDE.md 加「🧭 导航 IA 铁律」段
- 改 STATE_PEARNLY.md 加 NAV-IA 平行主线
- 改 BACKLOG.md 加 Phase 1-8 任务卡
- 改 MODULE_ROADMAP.md 加 NAV-IA 横切模块
- 改 DESIGN_SYSTEM.md 加 §18 头像下拉菜单组件

### Phase 1 · 顶栏三件套落地(1.5 d · 任何窗口可接)
**目标**:右上角搜索框 + Cmd+K 命令面板 + 头像下拉菜单 一并上线(都是顶栏组件 · 一起做最高效)

**改动文件**:`home.html` + `home.css` + `home.js`

**实施步骤**:

**A. 头像菜单**(0.6 d)
1. `home.html` topbar 区把现有 `.avatar` 包进 `.avatar-wrap` · 加 `.avatar-popup` 子元素(9 项 · 详见 DESIGN_SYSTEM §18)
2. `home.css` 加头像菜单样式(从 prototype_final 拷)
3. `home.js`:启动调 `/api/auth/me` · `applyRoleVisibility(me)` 按 §2.3 逻辑显隐

**B. 顶栏搜索框**(0.3 d)
1. `home.html` topbar 客户切换器**左边**插入 `.topbar-search`(灰底 + ⌘K 标签)
2. `home.css` 加 `.topbar-search` 样式(DESIGN_SYSTEM §19)
3. 点击触发 `openCmdk()`

**C. Cmd+K 命令面板**(0.5 d)
1. `home.html` body 末尾插入 `.cmdk-mask + .cmdk` 结构(含 input / 跳转区 / 操作区 / 空状态)
2. `home.css` 加 `.cmdk-*` 样式
3. `home.js`:
   - `openCmdk()` / `closeCmdk()`
   - `filterCmdk(q)` 实时过滤(基于 `data-cmdk-text`)
   - `setFocusItem(i)` / `moveFocus(delta)` 键盘导航
   - 全局 keydown:⌘K/Ctrl+K 打开 · ESC 关闭

**D. 4 语 i18n**(0.1 d · 共 15 个 key)
- 头像菜单 9 个:`avatar-menu-settings/team/billing/shortcuts/admin/test/help/logout/badge-admin`
- 搜索 + Cmd+K 6 个:`topbar-search-ph` / `cmdk-section-jump` / `cmdk-section-actions` / `cmdk-empty` / `cmdk-foot-move` / `cmdk-foot-select`
- 每个 key 必有 zh/en/th/ja 4 语完整 · check_i18n.py 退出码 0 才部署

5. 部署 v118.43.0(NAV-IA Phase 1)· cache bust +1

**验收**:
- 切 4 个测试账号(员工 mock / 老板 mock / skin / Earn)看头像菜单差异 = §2.2 矩阵
- ⌘K 弹出命令面板 · 输入 "vat" / "客户" / "进项" 实时过滤
- ↑↓ Enter ESC 键盘导航
- 4 语切换不溢出
- 移动端 < 600px 搜索框收缩为图标(只剩 🔍 不显示文字)

### Phase 2 · sidebar 重复入口清扫(0.5 天)
**触发**:Phase 1 完成
**改动**:
- 删 sidebar 底部「设置」(已收头像菜单)
- 删 sidebar 底部 `user-row`(已显示在头像菜单顶部)
- 删 sidebar「管理员」整组(成本追踪 / 用户管理 → 头像菜单 → admin layout · Phase 8 才接通)
- 删 sidebar「测试」整组(测试中心 → 头像菜单)

**注**:Phase 8 前 admin layout 还没做 · 头像菜单「管理员后台」点击 = 暂时跳 `?admin=1` 路由仍走老逻辑

### Phase 3 · sidebar CTA + 集成一级入口(0.5 d)
**改动**:
- sidebar 最顶部加蓝色主按钮「上传发票」· 替代当前"上传识别"作为日常入口
- sidebar 底部加「集成」一级入口(图标 `ti-plug-connected` · 跳 `page-integrations`)
  - 注:Phase 7 才把 settings 内「集成与连接」tab 内容真正搬过来 · 此处先建空壳路由

### Phase 4 · "即将" badge 大清扫(0.5 天)
**改动**:5 个"即将"项(仪表盘 / 凭证中心 / 销售发票 / 应收追踪 / 云盘同步)从 sidebar 撤
**替代**:作为 placeholder 卡片显示在对应业务流组内(凭证中心进进项管理 / 销售发票/应收进销项管理 / 云盘进设置→集成)

### Phase 5 · sidebar 业务流分组(1 天)
**改动**:4 组(核心/数据/自动化/管理员) → 新结构(prototype_final §3.2)
- 首页 / 销项管理▾ / 进项管理▾ / 客户 / 异常
**注**:这是最大改动 · 涉及所有路由迁移 · 必须先有 Phase 1-4 收纳准备

### Phase 6 · 进项管理完整模块(预估 3 周 · 不是 3-5 天 · 详见 v2 PRD)

> ⚠️ **本 Phase 不在本 PRD 展开 · 由 `MODULE_EXPENSE_PRD_v2.md` 全权负责**
> 路径:`D:\Users\Skin\Desktop\pearnly_project\CLAUDE.md\MODULE_EXPENSE_PRD_v2.md`
> 版本:v1.0(2026-05-14)· 作者:Zihao + Claude
> 命名:**凭证中心** / ศูนย์เอกสารจ่าย / Expense Center / 経費センター(路由 `/expense`)

**v2 PRD 已覆盖**:
- 16 项 Paypers 功能一比一复制(LINE/Gmail/OCR/分类/Drive/Sheets/代收据/PV/仪表盘/多公司/Credit)
- 10 项 Pearnly 超越(4 语/事务所多客户/异常引擎/ERP 推送/6 通道/批量异步/进销闭环/三签名 PV/审计日志/多发票拆分)
- 数据模型(2 张新表:`expense_records` + `payment_vouchers`)
- 15 类费用分类标准(代码 + 4 语)
- 3 个子版本拆分:
  - **v118.40 MVP**(8-10 d · 「能用」· 跟 Paypers 对齐)
  - **v118.41 提升**(5-7 d · 「好用」· 建差异化壁垒)
  - **v118.42 专业**(3-5 d · 「超越」· 事务所规模化)
- 5 条用户故事(记账员/外勤/事务所老板/SME/审计师)

**Paypers 调研关键发现**(2026-05-15):
- ✅ Paypers 做的"开发票" = **ใบแทนใบเสร็จ 代收据**(没正规发票时公司自开凭证)· 不是销项税票
- ✅ Paypers 自动归档 Drive = 按「公司/月」两级
- ✅ Paypers 自动分类 = 15 类 · "ข้าวกะเพรา"→餐饮 / "เมื่อวาน"→昨天 语义学习
- ✅ Paypers credit 包:50/100/300/1000 张 = ฿219/339/699/1999

**与本 PRD 的依赖关系**:
- Phase 6 必须在 Phase 1-5 完成后启动(导航 + sidebar + 业务流分组就位)
- Phase 6 完成后 sidebar 「进项管理 ▾」子项最终落地:
  - 费用总览(月度仪表盘 · 4 KPI + 分类柱状图 + 月对比)
  - 添加发票(6 渠道 · 含 Shopee/Lazada/转账单 OCR)
  - 付款凭证 PV(ใบสำคัญจ่าย · 三签名)
  - **代收据(ใบแทนใบเสร็จ · v2 PRD 新增 · 子项)**
  - 费用分类(15 类 · AI 自动 · 可手改 + 预算)

**承接**:对应 MODULE_ROADMAP 第 6 模块「凭证中心」从 0% → 80%+

### Phase 7 · 集成模块独立化(1 d)
**目标**:把 settings 内「集成与连接」整段拆出来 · 升为 sidebar 一级独立页 `page-integrations`
**改动**:
- 设置(头像菜单进入)删「集成与连接」tab · 默认 tab 改为「账户信息」
- 新建独立 page-integrations · 6 通道统一 `.integration-row` 卡片化:
  - Google 服务:Drive(已连接)/ Sheets(一键开启)/ Gmail 抓取
  - 收票渠道:LINE Bot / 文件夹监听
  - ERP 系统:ERP 对接(Webhook)
- `home.js` 路由表加 `integrations` · `showSettingsTab` 删 `integrations` 引用
**关键**:Google 一次授权双服务(Drive + Sheets 共享 OAuth)· 蓝色信息条强调

### Phase 8 · Admin Layout 独立(2 d · Earn 专属)

> **Earn 铁律**(2026-05-15 拍板):**不工作 · 只管账户 + 看成本** · sub-nav 只 2 项 · 砍其他

**新文件**:`admin.html` + `admin.css` + `admin.js`(独立 SPA · 不跟 home.html 共享)

**sub-nav**(仅 2 项 · 完全复用现有路由):
1. 成本追踪 = 现有 `admin-cost`(不动)
2. 用户管理 = 现有 `admin-users`(不动)

**视觉**:沿用 prototype_final CSS token(共用 `--bg / --accent / --line` 等)

**接通**:
- Earn 登录后服务端判定 `is_super_admin` → 直接重定向 `/admin/cost`(不进 home.html)
- 头像菜单「管理员后台」(仅 super admin 可见)→ 跳 `/admin/cost`
- 顶部超管 banner(从现有 `admin-mode-banner` 迁过来)

**已砍**(2026-05-15 简化):
- ❌ 平台概览(Earn 不需要)
- ❌ 操作日志(Earn 不需要)
- ❌ API 健康度(Earn 不需要)

---

## 5. 4 语 i18n key 命名(强约束)

### 5.1 头像菜单 key 命名(9 个)
| Key | zh | th | en | ja |
|---|---|---|---|---|
| `avatar-menu-settings` | 设置 | การตั้งค่า | Settings | 設定 |
| `avatar-menu-team` | 团队成员 | สมาชิกในทีม | Team Members | チームメンバー |
| `avatar-menu-billing` | 订阅 & 套餐 | สมัครสมาชิก & แพ็คเกจ | Subscription & Plan | サブスク&プラン |
| `avatar-menu-shortcuts` | 键盘快捷键 | คีย์ลัด | Keyboard Shortcuts | キーボードショートカット |
| `avatar-menu-admin` | 管理员后台 | หลังบ้านผู้ดูแล | Admin Console | 管理者コンソール |
| `avatar-menu-test` | 测试中心 | ศูนย์ทดสอบ | Test Center | テストセンター |
| `avatar-menu-help` | 帮助 & 反馈 | ช่วยเหลือ & คำติชม | Help & Feedback | ヘルプ&フィードバック |
| `avatar-menu-logout` | 退出登录 | ออกจากระบบ | Sign Out | ログアウト |
| `avatar-menu-badge-admin` | 超管 | ผู้ดูแลแพลตฟอร์ม | Super Admin | スーパー管理者 |

### 5.2 顶栏搜索 + Cmd+K key 命名(6 个 · v3 新增)
| Key | zh | th | en | ja |
|---|---|---|---|---|
| `topbar-search-ph` | 搜索发票 · 客户 · 跳转... | ค้นหาใบกำกับ · ลูกค้า · ไปที่... | Search invoices, customers, pages... | 検索: 請求書 · 顧客 · ページ |
| `cmdk-section-jump` | 跳转 | ไปที่ | Jump to | 移動 |
| `cmdk-section-actions` | 操作 | การกระทำ | Actions | アクション |
| `cmdk-empty` | 没找到匹配项 | ไม่พบรายการที่ตรงกัน | No matches found | 一致するものがありません |
| `cmdk-foot-move` | 移动 | เลื่อน | Move | 移動 |
| `cmdk-foot-select` | 选择 | เลือก | Select | 選択 |

### 5.3 集成页 key 命名(v3 新增 · 6 个 + 标题)
| Key | zh | th | en | ja |
|---|---|---|---|---|
| `integrations-title` | 集成 | การเชื่อมต่อ | Integrations | 連携 |
| `integrations-sub` | Google · LINE · 邮箱 · ERP · 文件夹 · 云盘 等第三方授权 · 让 Pearnly 自动同步数据 | (略 · 实施时补全) | Google, LINE, Email, ERP, Folder, Cloud third-party authorizations | Google · LINE · メール · ERP 等の連携設定 |
| `integrations-section-google` | Google 服务 | บริการ Google | Google Services | Google サービス |
| `integrations-section-channels` | 收票渠道 | ช่องทางรับใบกำกับ | Invoice Channels | 受信チャネル |
| `integrations-section-erp` | ERP 系统 | ระบบ ERP | ERP Systems | ERP システム |
| `integrations-google-info` | 授权一次 Google 账号 · Drive 和 Sheets 均可使用 · 无需重复授权 | (实施时补全) | One Google authorization unlocks both Drive and Sheets | Google 一回認証で Drive と Sheets 両方使用可 |

### 5.2 4 语铁律(CLAUDE.md 已有 · 此处再次锁定)
- 每加 1 个 key · 4 语必须全 · 缺一不部署
- 部署前自动跑 `python3 scripts/check_i18n.py static/home.js --strict`
- 退出码 ≠ 0 不部署

---

## 6. DESIGN_SYSTEM 引用

详细组件规范见 `DESIGN_SYSTEM.md §18 · 头像下拉菜单组件`(本 PRD 同步落地)

---

## 7. 接力机制 · 让每个窗口按 IA 路线推

### 7.1 启动 sequence
任何新窗口开「继续」时,自动:
1. 读 CLAUDE.md → 看见「🧭 导航 IA 铁律」段 → 知道 prototype_final 是唯一基准
2. 读 STATE_PEARNLY.md → 看见「NAV-IA 当前 Phase = X」
3. 读 NAV_IA_PRD.md(本文件)→ §4 Phase X 段拿到具体 spec
4. 在 BACKLOG.md 找对应 Phase X 任务卡 → 拿到工时/影响文件清单
5. 直接干 → 完成 → 自动更新 STATE_PEARNLY.md「NAV-IA 当前 Phase = X+1」
6. 部署核心场景必测 = 拿 prototype_final 截图逐点核对

### 7.2 与 P0-VAT 主线的关系
- **不冲突**:NAV-IA 改前端导航 · P0-VAT 改后端 + 对账核心 · 同窗口可并行小改
- **资源优先级**:P0-VAT > NAV-IA(P0-VAT 是月度刚需付费用户)
- **NAV-IA 触发**:P0-VAT 收尾期(等用户测/等真实数据)= 嵌入 NAV-IA 1 个 Phase
- **典型节奏**:1 个 P0-VAT 微版本 + 1 个 NAV-IA Phase 同窗口推完

### 7.3 验收准则(全 Phase 通用)
| 检查项 | 标准 |
|---|---|
| 视觉对照 | 像 prototype_final 截图 ≥ 95% |
| 4 语完整 | zh/en/th/ja 4 语切换无溢出 |
| 权限矩阵 | 切 4 个测试账号(员工/老板/skin/Earn)看到 §2.2 表 |
| 移动端 | iPhone 12 / Pixel 5 视口无溢出 |
| 现有功能 | 重排前能用的功能 · 重排后还能用 |

---

## 8. 历史决策追溯

- **2026-05-13** · Zihao 提出导航凌乱 · 要求「市场标准做法 · 简约干净」
- **2026-05-14** · 第一版 prototype(纯重排)被否 · Zihao 提供 `pearnly_nav_prototype.html` 自有方案
- **2026-05-15** · 拍板:在原 prototype 基础上**只采纳头像菜单升级** · 其他 100% 保留
- **2026-05-15** · 拍板:4 类账号矩阵(员工/老板/skin/Earn)· Earn 走独立 admin layout
- **2026-05-15** · 拍板:NAV-IA 升 P1 平行主线 · 8 Phase 切片 · 嵌入 P0-VAT 间隙跑

---

*本文件由 Claude 与 Zihao 共同维护 · 一切 NAV-IA 实施的唯一权威*
*更新触发:新 Phase 完成 / 视觉规范修订 / 账号体系变化*
