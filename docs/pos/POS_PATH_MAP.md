# POS 路径地图 + 老收银设备兼容(PS-5 · 最终版)

pos.pearnly.com 子域名方案已废弃(不做 nginx/DNS/证书)。POS 全部走主域 pearnly.com 路径。

## 最终地图

| 路径 | 服务内容 | 谁用 |
|------|---------|------|
| `pearnly.com/pos` | **老板后台专属登录页**(仅邮箱+密码,无 Google/LINE/注册;忘记密码走现有重置流)| POS 拆卖店老板 |
| `pearnly.com/pos/*` | 同上(老板登录页)| — |
| `pearnly.com/cashier` | **收银台 SPA 新家**(设备绑定 → PIN 登录 → 收银;PWA 可安装 + 离线)| 收银员设备 |
| `pearnly.com/cashier/*` | 同上(收银台 SPA)| — |
| `pearnly.com/cashier-sw.js` | 收银台 Service Worker(scope `/cashier`)| 收银台 PWA |
| `pearnly.com/pos-sw.js` | 老收银设备的 Service Worker(scope `/pos`)· **字节不动** | 老 metta 设备 |

- 老板登录成功 → `localStorage['mrpilot_token']` → 进 `/home`(pos_only 精简 7 项外壳)。
- `/pos` 页头 guard:本机存过收银台设备绑定凭据 `localStorage['pos_store_token']` → 立即
  `location.replace('/cashier')`;否则渲染老板登录页。凭据键名与收银台 SPA(`static/pos/pos.js`
  `STORE_TOKEN_KEY`)精确一致,同源 localStorage 跨 `/pos`↔`/cashier` 共享。
- 收银台 PWA 作用域:`static/pos/cashier.webmanifest`(start_url/scope=`/cashier`)+
  `static/pos/cashier-sw.js`(cache-first,离线回落 `/cashier`)。老 `pos-sw.js` / 老 manifest 原样保留。

## 老收银设备(metta 已装 /pos 旧 PWA)三种场景

旧 PWA:manifest scope=`/pos`,start_url=`/pos`;Service Worker scope=`/pos`,**cache-first**,
安装时把 `/pos` 外壳(老收银壳)缓存下来了。关键点:cache-first 意味着命中缓存就不走网络。

1. **在线点主屏图标**:PWA 打开 start_url `/pos` → 旧 SW 命中缓存 → 直接吐**缓存的老收银壳** →
   照常跑收银(不会看到新的老板登录页,因为根本没到网络)。零感知。
2. **离线点主屏图标**:同上,旧 SW 从缓存吐老收银壳 → 离线收银照常(本就是 08 ADR-1 的设计)。零感知。
3. **SW 更新后 / 缓存被清后**:
   - 我们**没有改 `pos-sw.js` 的字节**,旧 SW 不会触发更新,老设备缓存长期有效 → 维持场景 1/2。
   - 万一浏览器清了缓存(存储压力/用户手动清):PWA 打开 `/pos` → 走网络 → 命中新的老板登录页 →
     页头 guard 读到本机 `pos_store_token`(绑定凭据在 localStorage,清缓存不清它)→ 立即
     `replace('/cashier')` → 落到收银台新家(在线可直接绑定/收银;此后新装的是 `/cashier` PWA)。
   - 即「最坏情况也能自愈,把老设备接回 `/cashier`」,不会卡在老板登录页。

## 新收银设备

直接开 `pearnly.com/cashier` → 绑定页 → 绑店 → 收银;浏览器「添加到主屏幕」装的是 scope=`/cashier`
的 PWA,SW 注册在 `/cashier`,离线可用。与老板后台 `/pos` 彻底分家,不再混淆。

## 对外文案口径

收银台一律写 `pearnly.com/cashier`;老板后台写 `pearnly.com/pos`。任何引导/二维码/链接照此。
