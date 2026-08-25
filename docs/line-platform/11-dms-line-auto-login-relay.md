# 11 · DMS LINE 自动登录中继(一次性票据 · 批次B · 2026-08-22 · in-app 修订 2026-08-25)

> 用途:LINE DMS 富菜单第三项在 **LINE 内置浏览器**(`liff.openWindow external:false`)
> 打开 MRERP DMS,继续使用后台配置的账号密码自动登录,减少外部浏览器切换等待。
> 后端事实源:`services/line_dms/login_tickets.py`(DAL)· 留档 `alembic 0102`。

---

## 0. 当前状态(2026-08-25)

- **前端**:`static/dms-booking-edit/dms-booking-edit.js?v=7` portalMode 分支调用
  `liff.openWindow({ url, external: false })`,MRERP relay 页面在 LINE 内置浏览器内加载,
  不再弹出外部浏览器。非 LINE 环境回落 `location.replace(portalUrl)`。
- **后端**:一次性票据(`/api/line/dms-portal/ticket` POST)+ relay(`/line/dms-portal` GET)
  不变。票据 TTL 60s、一次性、SHA256 哈希存库、no-store/CSP/no-referrer 头齐备。
- **E2E**:`tests/e2e/33-dms-booking-edit-mobile.spec.js` 首条用例精确断言
  `external: false`,并验证票据只请求一次、页面停留原 LIFF 页、泰语 loading 文案可见。
- **⚠️ 未验**:LINE 真机(iOS/Android)尚未实测。in-app WebView 对第三方 cookie / 表单
  POST 的行为随 LINE 版本变化,需真机验证 relay 登录后是否落在 `home/home.php`。

## 1. JTBD(真实场景)

销售员/店主在 LINE 里点 DMS 门户链接 → 期望**直接看到 MR.ERP DMS**,不跳出 LINE。
现实:LINE 内置浏览器没有 MR.ERP 登录态,每次都要手输用户名+密码;若跳外部浏览器还
增加切换等待。任务:用 LINE 已绑定身份核销一次性票据,在 LINE 内置浏览器内取该员工
在 Pearnly 配置的 MR.ERP 凭据完成一次免输入登录。

## 2. RICE / Kano 判实用性

| 维度 | 判断 |
|---|---|
| Reach | 全部已绑 LINE 的 DMS 用户,每次点门户链接都命中(高频) |
| Impact | 高 —— 去掉登录页 + 去掉外部浏览器切换 = 去掉进入产品前的两道墙 |
| Confidence | 高 —— 一次性票据中继是业界成熟范式(§5),`external:false` 是 LIFF 标准 API |
| Effort | 小 —— 表+两函数(批次A 已落),路由/前端为后续批次,in-app 改一行 |
| Kano | 基础型(Must-be):没有不算错,但一旦有,再回到手输密码或外部浏览器会立刻被感知为退化 |

结论:做。不做灰度(铁律:测完直接全开)。

## 3. 移动端优先

- 主画面 = LINE 内置浏览器(手机竖屏):`liff.openWindow({ external: false })` 在当前
  LINE 会话内打开 relay 页,票据经 URL 参数传入、服务端一次核销换会话。用户在 relay
  页点一次「เข้าสู่ระบบ DMS」按钮后,后台凭据自动提交、不输账号密码、不切应用。
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
| in-app WebView 拦截会话 | LINE 内置浏览器内核拒绝第三方 cookie/表单 POST | 落到 MR.ERP 登录页;记录真机型号与 LINE 版本后评估官方 SSO/同域中继 |

Pearnly 票据失败的出口动作是回 LINE 重进入口(重新发票据)。核销失败一律返 None 走 fail-closed,
宁可让用户重点一次,不放行任何身份不明的请求。

## 5. 参考范式:一次性 SSO relay

照抄业界已验证的一次性凭据中继,不自创协议:

- **CAS Service Ticket / OAuth authorization code**:短寿命、一次性、服务端核销换会话;
  本表 `consume_login_ticket` 的单句 `DELETE ... RETURNING` 即此语义。
- 差异:凭据不是浏览器重定向链,而是 App(已登录侧)发票据 → LINE 侧核销,
  故票据明文只在 App↔webhook 间走一次,库里只有 SHA256 哈希。

## 6. in-app WebView 兼容风险(external:false 特有)

LINE 没有面向此场景的官方 SSO/OIDC 通道,本方案是自建中继 + LINE 内置浏览器承载,
已知风险:

1. **in-app WebView 第三方 cookie / 表单 POST**:relay 在 LINE 内置浏览器内向
   `mrerp4sme.com` POST 登录表单。LINE 内置浏览器的 cookie 策略随版本/OS 变化,
   可能拦截第三方会话 cookie;拦截时用户落到 MR.ERP 登录页,不能声称自动登录成功。
   此前 `external:true` 走系统浏览器避开了此问题,但代价是离开 LINE 应用。
2. **无法跨域判定密码结果**:浏览器同源策略禁止 Pearnly 读取 MR.ERP 的登录响应。中继
   只在表单提交后跳转;密码错误由 MR.ERP 首页/登录页如实呈现,不在 Pearnly 显示成功。
3. **LINE 版本差异(真机未验)**:上线后必须用实际员工手机验证 iOS 与 Android。记录票据
   核销后最终落在 `home/home.php` 还是登录页;若 in-app WebView 拦截会话,备选方案:
   (a) 回退 `external:true` 接受外部浏览器切换,(b) 等 MR.ERP 提供官方 SSO/一次性登录端点,
   (c) 同域中继代理(工程量大,需 MR.ERP 配合)。不能靠前端绕过浏览器安全策略。

## 7. 真机验证步骤(待执行)

1. 在 LINE iOS + Android 真机上打开 DMS 富菜单第三项「เข้าสู่ DMS」。
2. 确认:页面在 LINE 内置浏览器内打开(不弹外部浏览器),loading 泰语文案可见。
3. 确认:relay 页显示「เข้าสู่ระบบ DMS」按钮,点击后 MR.ERP DMS 首页加载(非登录页)。
4. 若落到登录页:记录设备型号、LINE 版本号、iOS/Android 版本号,截图存档,评估 §6 备选。
5. 验证票据一次性:同一链接第二次点击应显示「链接已使用」。
