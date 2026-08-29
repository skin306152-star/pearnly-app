# 11 · DMS LINE 自动登录中继(一次性票据 · 批次B · 2026-08-22 · 全平台 external 2026-08-25)

> 用途:LINE DMS 富菜单第三项打开 MRERP DMS,继续使用后台配置的账号密码自动登录。
> **Android 与 iOS 一律 `external:true`**(走系统外部浏览器,避开 LINE 内置 WebView
> 的 named window 隔离与第三方 cookie 拦截两个坑),并优化了登录中继时延。
> 后端事实源:`services/line_dms/login_tickets.py`(DAL)· 留档 `alembic 0102`。

---

## 0. 当前状态(2026-08-25 · 全平台 external + 中继提速)

- **前端**:`static/dms-booking-edit/dms-booking-edit.js?v=11` portalMode 分支统一
  `liff.openWindow({ url, external: true })`,但按平台安全清理 LINE 启动页:
  - Android **与** iOS 都走外部浏览器(不再按 `liff.getOS()` 分流)
  - iOS 保持打开外部浏览器后立即 `closeWindow()`
  - Android 等 `visibilitychange` 证明系统浏览器已接管后才 `closeWindow()`,避免同一
    JavaScript tick 里提前关闭 LIFF、取消尚未完成的 Android 外部 Intent
  - 非 LINE 环境 → `location.replace(portalUrl)`(不变)
- **后端 relay 提速**:`services/line_dms/mrerp_portal.py` 把旧 1800 ms + 4000 ms
  的两段盲等改成:
  1. 点按钮 → `window.open('about:blank', name)`(瞬时,零网络)
  2. **立即** `form.submit()` 送进 named popup
  3. 轮询 popup:只要它还在同源 `about:blank`,说明 checklogin POST 仍在途;
     一旦落到跨域 checklogin 页(登录已落、会话 cookie 已建)才送 home.php
     —— 慢网也**不会**打断在途登录
  4. `<link rel="dns-prefetch">` + `<link rel="preconnect">` 预热 MRERP 连接
- **票据链路**:一次性票据(`/api/line/dms-portal/ticket` POST)+ relay(`/line/dms-portal`
  GET)不变。TTL 60s、一次性、SHA256 哈希存库、no-store/CSP/no-referrer 头齐备。
- **E2E**:`tests/e2e/33-dms-booking-edit-mobile.spec.js` 锁定:① Android
  `external:true`,外部交接前不关闭、进入后台后才关闭;② iOS 保持立即关闭且重入发
  **新票据**;③ relay 弹窗登录(含 preconnect 链接断言、无 1800/4000 盲等)。

### 平台矩阵

| 平台 | `external` | 行为 | 自动登录 |
|---|---|---|---|
| Android LINE | `true` | 跳外部浏览器;进入后台后清理启动页 | ✅ |
| iOS LINE | `true` | 跳外部 Safari;立即清理启动页 | ✅ |
| 非 LINE 桌面 | N/A | `location.replace` 同窗口跳转 | ✅ |

### 为什么全平台都走 external

LINE 内置 WebView 有两个独立问题:① iOS WKWebView 对 named window 创建独立
browsing context,`form.target=name` 失效,用户看到空白登录页;② Android WebView
默认拦第三方 cookie,MRERP 会话 cookie 落不下来,自动登录在 app 内不可靠。两个平台
统一走外部浏览器,彻底绕开 WebView 内核差异;代价是用户需手动切回 LINE,换来可靠的
自动登录。此问题在桌面 Chromium 不复现,属移动 WebView 已知行为。

### 中继时延实测(2026-08-25 · 文档测试账号 dmstest · 真服务器 · Playwright)

`scripts/_mrerp_relay_bench.cjs`(≥12 次,点按钮 → home.php 加载):

| 场景 | 中位 | 均值 | 与旧 5800 ms 比 |
|---|---|---|---|
| 正常网络 | 1662 ms | 1691 ms | **~71% 快** |
| 慢网(checklogin +3000 ms) | — | — | 登录不被打断,home.php 正常加载 |
| 慢网(checklogin +5000 ms) | — | — | 登录不被打断,home.php 正常加载 |

旧实现 1800 ms(开窗等待)+ 4000 ms(导航等待)= 固定 5800 ms,且固定定时器在慢网下
会在 checklogin POST 完成前就导航 home.php,导致无会话、被 MRERP 弹回登录页。新实现
轮询 popup 是否离开同源 about:blank,天然适配网络快慢,慢网下**绝不**打断在途登录。

## 1. JTBD(真实场景)

销售员/店主在 LINE 里点 DMS 门户链接 → 期望**直接看到 MR.ERP DMS**。现实:LINE
内置浏览器没有 MR.ERP 登录态,每次都要手输用户名+密码。任务:用 LINE 已绑定身份核销
一次性票据,取该员工在 Pearnly 配置的 MR.ERP 凭据完成一次免输入登录。

## 2. RICE / Kano 判实用性

| 维度 | 判断 |
|---|---|
| Reach | 全部已绑 LINE 的 DMS 用户,每次点门户链接都命中(高频) |
| Impact | 高 —— 去掉登录页 = 去掉进入产品前的最后一道墙 |
| Confidence | 高 —— 一次性票据中继是业界成熟范式(§5),全平台 external 基于 LIFF 官方 API |
| Effort | 小 —— 表+两函数(批次A 已落),前端统一 external:true + 中继轮询提速 |
| Kano | 基础型(Must-be):没有不算错,但一旦有,再回到手输密码会立刻被感知为退化 |

结论:做。不做灰度(铁律:测完直接全开)。

## 3. 移动端优先

- Android / iOS 统一一键跳外部浏览器加载 relay,用户在 relay 页点「เข้าสู่ระบบ DMS」按钮后
  凭据自动提交、不输账号密码。自动登录成功后用户手动切回 LINE,代价是可接受的切换,
  换取两个平台都可靠的自动登录(绕开 WebView named window 隔离与第三方 cookie 拦截)。
- relay 页 DNS-prefetch / preconnect 预热 MRERP 连接;点按钮后立即开窗、立即提交,
  轮询登录落地后导航 home,慢网下不打断。
- TTL 60 秒、一次性:票据只够「这一次跳转」,不为桌面端多开窗口留长寿命后门。
- 失败页必须手机可读(一句话 + 一个动作按钮,见 §4),不给技术错误码。

## 4. 失败态(诚实线 · 红线#3:绝不显示"完成/成功")

| 失败态 | 成因 | 用户看到 |
|---|---|---|
| 票据不存在 | 链接被分享/猜错,从未发过 | 「链接无效,请回 LINE 重新点选单」 |
| 已核销 | 一次性票据被第二次使用(双击/转发/重放) | 「链接已使用,请回 LINE 重新点选单」 |
| 已过期 | 超过 60 秒(网络慢/链接留置) | 「链接已过期,请回 LINE 重新点选单」 |
| 核销服务不可用 | DB 故障,DAL 软降级返 None(fail-closed) | 「暂时无法登录,请稍后再试」 |
| MR.ERP 拒绝登录 | 账号密码失效 | 落到 MR.ERP 登录页,由负责人在 Pearnly 更新凭据 |
| 外部浏览器被拦截 | 弹窗被系统/浏览器拦 | relay 页提示允许弹窗后重试 |

Pearnly 票据失败的出口动作是回 LINE 重进入口(重新发票据)。核销失败一律返 None 走 fail-closed,
宁可让用户重点一次,不放行任何身份不明的请求。

## 5. 参考范式:一次性 SSO relay

照抄业界已验证的一次性凭据中继,不自创协议:

- **CAS Service Ticket / OAuth authorization code**:短寿命、一次性、服务端核销换会话;
  本表 `consume_login_ticket` 的单句 `DELETE ... RETURNING` 即此语义。
- 差异:凭据不是浏览器重定向链,而是 App(已登录侧)发票据 → LINE 侧核销,
  故票据明文只在 App↔webhook 间走一次,库里只有 SHA256 哈希。

## 6. 长期目标:MRERP 官方 SSO

当前全平台走外部浏览器是权宜之计。两者兼得(LINE 内置 + 自动登录)需要 MRERP 提供:

- 一次性 token 端点:接受 Pearnly 签发的短寿命 token → 建立 PHPSESSID → redirect home.php
- 或标准 OIDC/SAML 端点

在 MRERP 提供前,Android 与 iOS 都保持 `external:true`。

## 7. 真机验证步骤

1. **Android**:LINE 真机打开 DMS 富菜单第三项 → 确认跳外部浏览器(系统默认浏览器)→
   relay 页点按钮 → MR.ERP DMS 首页加载(非登录页)。
2. **iOS**:LINE 真机打开 DMS 富菜单第三项 → 确认跳转 Safari → relay 页点按钮 →
   MR.ERP DMS 首页加载(非登录页)。
3. 验证票据一次性:同一链接第二次点击应显示「链接已使用」。
4. 若外部浏览器内仍落到登录页:记录设备型号、浏览器版本,截图存档,评估是否凭据已失效。
