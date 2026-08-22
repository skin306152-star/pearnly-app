# 11 · DMS LINE 自动登录中继(一次性票据 · 批次B · 2026-08-22)

> 用途:LINE DMS 内嵌网页(门户/菜单)使用 Pearnly 已保存凭据免输密码进入 MR.ERP DMS。
> 后端事实源:`services/line_dms/login_tickets.py`(DAL)· 留档 `alembic 0102`。

---

## 1. JTBD(真实场景)

销售员/店主在 LINE 里点 DMS 门户链接 → 期望**直接看到 MR.ERP DMS**。现实:LINE 内置
浏览器没有 MR.ERP 登录态,每次都要手输用户名+密码。任务:用 LINE 已绑定身份核销一次性
票据,再取该员工在 Pearnly 配置的 MR.ERP 凭据完成一次免输入登录。

## 2. RICE / Kano 判实用性

| 维度 | 判断 |
|---|---|
| Reach | 全部已绑 LINE 的 DMS 用户,每次点门户链接都命中(高频) |
| Impact | 高 —— 去掉登录页 = 去掉进入产品前的最后一道墙 |
| Confidence | 高 —— 一次性票据中继是业界成熟范式(§5),不依赖 LINE 新能力 |
| Effort | 小 —— 表+两函数(批次A 已落),路由/前端为后续批次 |
| Kano | 基础型(Must-be):没有不算错,但一旦有,再回到手输密码会立刻被感知为退化 |

结论:做。不做灰度(铁律:测完直接全开)。

## 3. 移动端优先

- 主画面 = LINE 内置浏览器(手机竖屏):票据经 URL 参数传入、服务端一次核销换会话,
  全程 0 次手输、0 个额外点击。
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
| WebView 拦截会话 | iOS/Android 内核拒绝 iframe 第三方 cookie | 落到 MR.ERP 登录页;记录真机型号与 LINE 版本后评估官方 SSO/同域中继 |

Pearnly 票据失败的出口动作是回 LINE 重进入口(重新发票据)。核销失败一律返 None 走 fail-closed,
宁可让用户重点一次,不放行任何身份不明的请求。

## 5. 参考范式:一次性 SSO relay

照抄业界已验证的一次性凭据中继,不自创协议:

- **CAS Service Ticket / OAuth authorization code**:短寿命、一次性、服务端核销换会话;
  本表 `consume_login_ticket` 的单句 `DELETE ... RETURNING` 即此语义。
- 差异:凭据不是浏览器重定向链,而是 App(已登录侧)发票据 → LINE 侧核销,
  故票据明文只在 App↔webhook 间走一次,库里只有 SHA256 哈希。

## 6. 无官方 SSO 的 iframe / cookie 兼容风险

LINE 没有面向此场景的官方 SSO/OIDC 通道,本方案是自建中继,已知风险:

1. **第三方 cookie 限制**:MR.ERP 只提供表单登录,没有 SSO/OIDC 或可回跳接口。中继必须在
   隐藏 iframe 向 MR.ERP POST,再顶层进入其首页,因此 MR.ERP 这一腿确实依赖 WebView 允许
   写第三方会话 cookie。iOS Safari ITP、Android WebView 或 Chrome 策略可能拦截;拦截时
   用户会落到 MR.ERP 登录页,不能声称自动登录成功。
2. **无法跨域判定密码结果**:浏览器同源策略禁止 Pearnly 读取 MR.ERP 的登录响应。中继只在
   iframe 收到响应后跳转;密码错误由 MR.ERP 首页/登录页如实呈现,不在 Pearnly 显示成功。
3. **LINE 版本差异**:上线后必须用实际员工手机验证 iOS 与 Android。记录票据核销后最终落在
   `home/home.php` 还是登录页;若会话被拦,可靠解法需要 MR.ERP 提供官方 SSO/一次性登录端点
   或同域回跳,不能靠前端绕过浏览器安全策略。
