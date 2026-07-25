# 入口 / 路由地图(2026-07-10 批次 EN 定版)

⚠️ 改任何对外页面先看这里 —— 改错位置 = 新域名永远跑老版本。原在 `AGENTS.md §5-bis`,
2026-07-25 挪来这里按需装载(改前端才读),AGENTS.md 只留一行指针。

| URL | 浏览器实际拿到 | 要改就改这里(可读源) | 坑 |
|---|---|---|---|
| `/` 品牌门户 | `static/dist/portal.html` | `static/landing/portal.dc.html` | 改完必 `npm run build`;压缩器会吃 `style="{{绑定}}"` 之外的非法 CSS,动 build 管线必逐屏对照 |
| `/login` 老登录(猫页·会计入口兜底) | `static/dist/login.html` | 根 `login.html`(+`static/landing/landing*.js`) | /acc 已取消,会计永久走这里 |
| `/home` 主工作台 | `static/dist/home.html` + `main.js` | 根 `home.html` + `src/home/*` | 改 src 必 build+bump 根 home.html 的 `?v` |
| `/pos` POS 老板登录 | `static/dist/pos-login.html` | `static/pos/pos-login.html` | **routes/pos_login_page.py 已删**,别再造内联页 |
| `/cashier` 收银台 | `static/dist/pos.html` | `static/pos/pos.html` + `static/pos/*.js` | 老设备旧 PWA 认 /pos,靠页头 guard 自动接驳;SW 双轨 /pos-sw.js(旧)+/cashier-sw.js(新)勿动旧字节 |
| `/earn` 超管登录 | `static/dist/earn-login.html` | `static/earn/earn-login.html` | **routes/earn_login_page.py 已删** |
| `/admin/*` Earn 后台 | `static/dist/admin.html` | `static/admin/admin.html/.js/admin-i18n.js` | **改 admin.js/i18n 必 bump admin.html 里 `?v`**(CDN 按旧键回旧文件·缓存闸盲区)+ build 出 dist/admin.html |
| `/ai` `/console` `/invite` `/reset` `/terms` `/privacy` | 各自 `static/dist/*.html` | `static/ai/ai.html` / `static/console/*.html` / 根 `reset.html` / `static/terms\|privacy.html` | 全部源→产物映射的唯一权威=`scripts/build-html-minify.mjs` 的 TARGETS |

**三条硬规**

1. 新对外页面必进 `scripts/build-html-minify.mjs` 的 TARGETS + 外壳闸测试(`test_page_shell_minified`·响应 ≤3 行)+ 路由契约表(`test_pages_routes_contract`)。
2. 登录门只有 `/login`(OAuth 过渡)、`/pos`、`/earn`、`/ai` 四个;pos_only 壳退出回 `/pos`,别再把用户甩去 `/login`。
3. 菜单壳白名单唯一源 = `src/home/nav-presets.ts`(会计版 / pos_only 两份清单),加菜单项改它 + spec 24/25 断言,别再写散 if。
