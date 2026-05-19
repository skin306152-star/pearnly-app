# Changelog · Pearnly

按倒序排列 · 最新发布在上。
版本号约定:`vMAJOR.MINOR.PATCH`(SemVer)+ 日期标签。

---

## [v1.0.0] · 2026-05-19 · Credits System Release

> **里程碑**:旧订阅模型(trial / monthly / yearly / lifetime)全面下线,
> 切换为「按量付费 + 公司钱包」结构。生产环境 commit `5de6cc5` · cache bust `v=11835200`。
> 数据库快照:`/opt/mrpilot/backups/pre_credits_release_20260519_152218.sql` (3.3M)。

### 新增

- **按量付费系统**
  - 前 200 张 / 月 · ฿1.50/张
  - 超过 200 张 · ฿0.75/张
  - 月度重置锚定 **Asia/Bangkok**(UTC+7)· 每月 1 日 00:00
  - 钱包结构 `tenant_credits` · 流水 `credit_transactions` · 月用量 `monthly_page_usage`
  - 扣费路径强制 `SELECT … FOR UPDATE` 防并发

- **角色分离 · owner / employee**
  - `users.invited_by IS NULL` 判定 owner · 否则 employee
  - 员工:不显示余额 / 充值 / 预警 / 报表导出
  - 老板:全功能可见

- **多公司选择器**(`active_tenant_id`)
  - `users.active_tenant_id` 列(可空)· 优先于 JWT `tenant_id`
  - `GET /api/my-companies` · `POST /api/switch-company`
  - 前端单公司静默自动设 active · 多公司全屏卡片选择器
  - 顶栏 `brand-workspace` 点击下拉切换

- **充值流程**(3 步弹窗)
  - 第 1 步:填金额(快捷按钮 + 自定义)
  - 第 2 步:Bangkok Bank 银行信息(账号一键复制)+ 显示金额
  - 第 3 步:上传转账截图 + 付款人 + 备注
  - 后端:`/api/credits/topup/request` · `/api/credits/topup/upload-slip/{id}`
  - admin 审核:`/api/admin/credits/topup/{approve|reject}/{id}`

- **使用历史 + 报表导出**
  - `GET /api/credits/usage-history`(分页 · owner 看全公司 · 员工看自己)
  - 导出 PDF / Excel(`usage_report.py`)

- **余额预警条**(顶栏正下方)
  - 红色:balance = 0 · 红色「立即充值」CTA
  - 黄色:balance < 50
  - 蓝色:本月 ≥190 张(将进入 ฿0.75 分价)
  - 仅 owner + 非豁免账号触发

- **新用户引导**
  - 触发:owner + balance=0 + 无 OCR 历史 + 首次登录
  - 关闭后 `localStorage.pearnly_onboarding_seen_<uid>=1` · 不再弹

- **实时余额轮询**(30 秒)
  - 充值审核通过后前端自动检测到 · toast 提示 · loadDashboard 刷新

- **泰语邮件通知**(SMTP)
  - `send_topup_approved_email(tenant_id, amount, new_balance)` · 触发于充值审核通过
  - `send_low_balance_email(tenant_id, balance)` · 触发于扣费后 balance<50 · 24h 内不重复(`tenant_credits.low_balance_notified_at`)
  - `send_employee_invitation_email(email, password)` · 触发于团队添加员工
  - 全部 try/except 包裹 · 失败仅日志 · 主流程不阻塞

- **i18n 新增**(4 语 zh/en/th/ja)
  - 多公司:`select-company` `switch-company` `company-role-admin/member` `company-balance` `company-pages-month`
  - 余额预警:`low-balance-msg` `zero-balance-msg` `near-tier-msg` `topup-cta`
  - 新用户引导:`welcome-title` `welcome-msg` `welcome-skip`
  - 时间显示:`time-just-now` `time-min-ago-suffix` `time-hour-ago-suffix` `time-day-ago-suffix`
  - 充值流程:`topup-title` `topup-step1/2/3` `topup-amount-label` 等共 23 个键

### 变更

- **admin 后台**
  - 仅支持 zh / th(en / ja 用户自动降级 th)
  - 顶栏只显示 中 / ไทย 两个按钮
  - 默认语言由 `zh` 改为 `th`

- **admin 弹窗组件**
  - `_adminDialog` 新增 `type:'textarea'` 支持(行数可配 · Ctrl+Enter 提交)
  - 新增 `danger:true` 红色确认按钮
  - 驳回充值:textarea + 必填验证 + 红色确认按钮

- **设置页文案**
  - 「套餐 & 用量」tab:删除「订阅类型 · 月度订阅」
  - 改为「计费方式 · 按使用量计费」+ 每月分价说明

- **测试中心入口**
  - 由硬编码 UUID 改为严格按 `email === 'skin306152@gmail.com'`
  - 移除 `?test_center=1` URL 旁路
  - 移除 localStorage `pearnly_test_center` 旁路

- **员工首次登录**
  - `must_change_password=true` 时立即弹强制改密 modal
  - 不再展示 onboarding 等其他弹窗(优先级最高)

- **添加员工弹窗**
  - 邮箱由「选填」改为「必填」
  - 新增 `team-modal-email-required` i18n key
  - 邮箱格式空与不合法分两种错误信息

### 移除

- trial / monthly / yearly / lifetime 订阅相关代码
- 升级弹窗(`showUpgradeModal`)/ 试用横幅(`renderTrialBanner`)/ 配额警示
- admin.js 中所有 `alert()` / `confirm()` / `prompt()` 原生调用 → 内置组件
- admin.html 中 en / ja 语言按钮(只剩 zh / th)
- topup IIFE 老版本(改为 3 步流程)
- 月付 `monthly_quota` 字段在顶栏的展示(改为「套餐 & 用量」tab 内显示)

### 修复

- **语言切换不同步**
  - topup modal 文字不跟随 lang 切换 → 加 `subscribeI18n('topup-v2')`
  - 使用明细表格不跟随 → 加 `subscribeI18n('usage-history')`
  - 时间显示 `7time-hour-ago-suffix` 字面字符串 → 4 个 time-* i18n key 加入 4 语字典
  - `window._i18nGet` 未定义 → 改用全局 `window.t`

- **设置弹窗滚动**
  - 右侧 `.settings-content` 不滚动 → 选择器加 `.settings-modal-overlay` 前缀 · 添加 `min-height:0`
  - 左侧菜单滚动至「联系我们」OK
  - 移动端 `@media (max-width: 860px)` 取消双重滚动

- **充值申请 KeyError**
  - `_AdminTopupApproveBody` 字段补全
  - `topup_requests` 查询字段对齐

- **管理员后台入口可见性**
  - 仅 `is_super_admin=true` 用户可见(已通过 `data-show-if-admin` 控制)

### DB Schema

```sql
-- 本次发布的所有 schema 变更(自动 idempotent migration)
ALTER TABLE users ADD COLUMN IF NOT EXISTS active_tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL;
ALTER TABLE tenant_credits ADD COLUMN IF NOT EXISTS low_balance_notified_at TIMESTAMPTZ;
-- 其它变更:无(均为应用层逻辑)
```

### 已知问题(发布后跟进)

- Supabase Transaction Pooler 偶发 `relation "users" does not exist` 错误(search_path 重置)· 5/16, 5/19 12:54, 5/19 15:21 均出现 · 与本次发布无关 · 待 P1 修复(在 db.get_cursor() 加 `SET LOCAL search_path = public`)
- pg_dump 期间触发瞬态错误窗口(约 30 秒)· 已在 ROLLBACK.md 记录

### 性能基线(2026-05-19)

| 接口 | 平均响应时间 |
|---|---|
| GET /api/health | 0.65 s |
| GET /api/me/credits | 0.61 s |
| GET /api/my-companies | 0.63 s |
| POST /api/switch-company | 0.61 s |

(均为 https 通过 Cloudflare · TLS handshake + edge hop 占大头)

### 部署

- 服务器:Vultr 45.76.53.194 · `/opt/mrpilot/`
- 静态:`/opt/mrpilot/static/` · 已 gzip 预压缩(`.js.gz` `.html.gz`)
- 数据库:Supabase `aydjsgmirjpkjaqknmlg` · pooler 6543
- systemd:`mrpilot.service` · `systemctl restart mrpilot`
- git:`feature/credits-system` · HEAD `5de6cc5`

---

## 历史版本(略)

往期 changelog 参见 `CLAUDE.md/STATE_PEARNLY.md` 与 git log。
