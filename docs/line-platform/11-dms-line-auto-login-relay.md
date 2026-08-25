# 11 · DMS LINE 自动登录中继(一次性票据 · 批次B · 2026-08-22 · 平台分流 2026-08-25)

> 用途:LINE DMS 富菜单第三项按平台分流打开 MRERP DMS,继续使用后台配置的账号密码
> 自动登录。Android 走 LINE 内置浏览器(`external:false`),iOS 走外部 Safari
> (`external:true`)以避开 WKWebView named window 隔离问题。
> 后端事实源:`services/line_dms/login_tickets.py`(DAL)· 留档 `alembic 0102`。

---

## 0. 当前状态(2026-08-25 · 平台分流)

- **前端**:`static/dms-booking-edit/dms-booking-edit.js?v=8` portalMode 分支使用
  `liff.getOS()` 判定平台:
  - `android` → `liff.openWindow({ url, external: false })`(LINE 内置浏览器)
  - `ios` → `liff.openWindow({ url, external: true })`(外部 Safari,保自动登录)
  - 未知/缺失 getOS → `external: true`(安全兜底)
  - 非 LINE 环境 → `location.replace(portalUrl)`(不变)
- **后端**:一次性票据(`/api/line/dms-portal/ticket` POST)+ relay(`/line/dms-portal` GET)
  不变。票据 TTL 60s、一次性、SHA256 哈希存库、no-store/CSP/no-referrer 头齐备。
  `services/line_dms/mrerp_portal.py` 登录协议未改。
- **E2E**:`tests/e2e/33-dms-booking-edit-mobile.spec.js` 三条用例分别锁定 Android
  `external:false`、iOS `external:true`、未知 OS `external:true`。relay 弹窗测试不变。

### 平台矩阵

| 平台 | `liff.getOS()` | `external` | 行为 | 自动登录 |
|---|---|---|---|---|
| Android LINE | `"android"` | `false` | LINE 内置浏览器加载 relay | ✅(待真机验) |
| iOS LINE | `"ios"` | `true` | 跳转 Safari 加载 relay | ✅(Safari 支持 named popup) |
| 未知/旧 LIFF | `undefined`/其他 | `true` | 外部浏览器(安全兜底) | ✅ |
| 桌面/非 LINE | N/A | N/A | `location.replace` 同窗口跳转 | ✅ |

### 为什么 iOS 不能走内置浏览器

MRERP 登录协议是两步握手:POST checklogin.php → 纯文本 `lct::1::1` → 客户端 JS
`sdpt()` 导航到 home.php。relay 页面用 `window.open(url, name)` + `form.target=name`
把表单提交送入 named popup。iOS WKWebView(LINE 内置浏览器内核)对 named window 创建
独立 browsing context,导致 form target 失效、用户看到空白 MRERP 登录页。此问题在
桌面 Chromium 不复现,属 WebKit 已知行为。详情见诊断报告(2026-08-25)。

## 1. JTBD(真实场景)

销售员/店主在 LINE 里点 DMS 门户链接 → 期望**直接看到 MR.ERP DMS**。现实:LINE
内置浏览器没有 MR.ERP 登录态,每次都要手输用户名+密码。任务:用 LINE 已绑定身份核销
一次性票据,取该员工在 Pearnly 配置的 MR.ERP 凭据完成一次免输入登录。

## 2. RICE / Kano 判实用性

| 维度 | 判断 |
|---|---|
| Reach | 全部已绑 LINE 的 DMS 用户,每次点门户链接都命中(高频) |
| Impact | 高 —— 去掉登录页 = 去掉进入产品前的最后一道墙 |
| Confidence | 高 —— 一次性票据中继是业界成熟范式(§5),平台分流基于 LIFF 官方 API |
| Effort | 小 —— 表+两函数(批次A 已落),前端加 getOS 判定 |
| Kano | 基础型(Must-be):没有不算错,但一旦有,再回到手输密码会立刻被感知为退化 |

结论:做。不做灰度(铁律:测完直接全开)。

## 3. 移动端优先

- Android:LINE 内置浏览器内加载 relay,用户在 relay 页点「เข้าสู่ระบบ DMS」按钮后
  凭据自动提交、不输账号密码、不切应用。
- iOS:跳转 Safari 加载 relay,自动登录成功后用户手动切回 LINE。代价是可接受的切换,
  换取可靠的自动登录。
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
| in-app WebView 拦截会话 | Android LINE 内置浏览器内核拒绝第三方 cookie | 落到 MR.ERP 登录页;记录真机型号与 LINE 版本后评估 |

Pearnly 票据失败的出口动作是回 LINE 重进入口(重新发票据)。核销失败一律返 None 走 fail-closed,
宁可让用户重点一次,不放行任何身份不明的请求。

## 5. 参考范式:一次性 SSO relay

照抄业界已验证的一次性凭据中继,不自创协议:

- **CAS Service Ticket / OAuth authorization code**:短寿命、一次性、服务端核销换会话;
  本表 `consume_login_ticket` 的单句 `DELETE ... RETURNING` 即此语义。
- 差异:凭据不是浏览器重定向链,而是 App(已登录侧)发票据 → LINE 侧核销,
  故票据明文只在 App↔webhook 间走一次,库里只有 SHA256 哈希。

## 6. 长期目标:MRERP 官方 SSO

当前 iOS 走外部浏览器是权宜之计。两者兼得(LINE 内置 + 自动登录)需要 MRERP 提供:

- 一次性 token 端点:接受 Pearnly 签发的短寿命 token → 建立 PHPSESSID → redirect home.php
- 或标准 OIDC/SAML 端点

在 MRERP 提供前,iOS 保持 `external:true`,Android 保持 `external:false`。

## 7. 真机验证步骤

1. **Android**:LINE 真机打开 DMS 富菜单第三项 → 确认在 LINE 内置浏览器内打开(不弹
   外部浏览器)→ relay 页点按钮 → MR.ERP DMS 首页加载(非登录页)。
2. **iOS**:LINE 真机打开 DMS 富菜单第三项 → 确认跳转 Safari → relay 页点按钮 →
   MR.ERP DMS 首页加载(非登录页)。
3. 验证票据一次性:同一链接第二次点击应显示「链接已使用」。
4. 若 Android 落到登录页:记录设备型号、LINE 版本号,截图存档,评估是否也需切 external。
