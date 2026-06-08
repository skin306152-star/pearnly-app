# 📸 Pearnly · 视觉回归(REFACTOR-WC-D5)

> 整顿期 D5 · 给前端 10 个核心页面打 Playwright screenshot baseline · 防 home.css / src/home/* 改动悄悄破图(2026-05-28 窗口 C)。

---

## 0. 什么是视觉回归

不是测功能 · 是测"长得对不对":
- 抓一页截图 → 跟基线对比
- 像素差 > 阈值 → fail
- 像素差 < 阈值 → 通过

典型抓住的 BUG:
- 改 home.css 把按钮位置错了 1px(单测 / E2E 抓不到)
- 改 Vite chunk 把字号从 13px 变 14px
- 4 语切换某语言文字溢出 / 折行
- 暗 / 浅色 mode 配色漂移

---

## 1. 跑法

**第一次运行(出基线)**:
```powershell
# 环境变量(默认打 https://pearnly.com · 也可改 localhost)
$env:PEARNLY_VISUAL_BASE_URL = "https://pearnly.com"
$env:PEARNLY_E2E_USER = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_USER','User')
$env:PEARNLY_E2E_PASS = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_PASS','User')

# 出基线(首次 · 把当前页面状态当 ground truth)
npx playwright test --config tests/visual/playwright.visual.config.js --update-snapshots

# baseline 落地在 tests/visual/__screenshots__/baseline.spec.js-snapshots/
```

**之后跑(对比基线)**:
```powershell
$env:PEARNLY_VISUAL_BASE_URL = "https://pearnly.com"
$env:PEARNLY_E2E_USER = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_USER','User')
$env:PEARNLY_E2E_PASS = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_PASS','User')

# 对比(像素差 > 阈值 fail)
npx playwright test --config tests/visual/playwright.visual.config.js
```

**故意更新基线(UI 改了 · 接受新外观)**:
```powershell
npx playwright test --config tests/visual/playwright.visual.config.js --update-snapshots
git add tests/visual/__screenshots__/
git commit -m "chore(visual): 更新视觉基线 · REFACTOR-<task-id>

<理由 · 改了什么 UI · 验过 4 语 / 移动端>

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
"
```

---

## 2. 覆盖的 10 页

| # | 页面 | 路径 | 需登录 | 备注 |
|---|---|---|---|---|
| 1 | 登录 | `/login` / `/` | ❌ | login.html 着陆页 |
| 2 | 着陆 | `/landing`(或 `/`) | ❌ | 营销首屏 |
| 3 | 识别(上传)| `/#upload` 或 `/home#recognize` | ✅ | OCR 主入口 |
| 4 | 历史 | `/#history` | ✅ | OCR 历史列表 |
| 5 | 客户 | `/#clients` | ✅ | 客户管理 |
| 6 | 对账 | `/#reconcile` 或 `/#recon` | ✅ | 销项税核对中心 |
| 7 | 异常 | `/#exceptions` | ✅ | 异常处理中心 |
| 8 | 设置 | `/#settings` | ✅ | 用户级设置 |
| 9 | 充值 | `/#recharge` 或 `/#billing` | ✅ | 充值申请 |
| 10 | 超管 | `/admin` | ✅(admin)| Earn admin SPA |

**前 2 个(公开页)**:可以跑无需登录的基线 · 抓得最稳。
**后 8 个(认证页)**:需要真账号 env · 在 CI 默认 skip(没 env)。
**第 10 个(admin)**:需要 admin env · 没设直接 skip 该 case。

---

## 3. 不进 CI(2026-05-28 窗口 C 决策)

理由:
1. 视觉基线 PNG 文件大(每页 ~100-300KB · 10 页 ~2MB)· 每次更新 git diff 重
2. 真打 `pearnly.com` 在 CI 跑慢 · 失败率高(网络抖动)
3. CI Linux runner 字体跟本机 Windows 不一样 · 跨平台基线易飘
4. 我们 17 个真账号 E2E spec 已经覆盖核心交互 · 视觉回归是辅助 · 不是必跑

**手动跑的时机**:
- 每完成一波 home.css / src/home/* 抽出/重构 → 跑一次确认无视觉漂移
- 每次部署前(`/api/version` 200 后)跑一次
- Zihao 报"那个页面看起来不对了"→ 跑视觉回归定位是不是真漂了

---

## 4. 跨平台基线策略

Playwright 默认在 baseline 文件名里加平台后缀:
```
baseline.spec.js-snapshots/login-page-chromium-win32.png
baseline.spec.js-snapshots/login-page-chromium-linux.png
```

Pearnly 决定:**只维护一个平台的基线**(Windows · 因为 Zihao + Claude 主跑环境),不为 Linux 单独维护。CI 若启用视觉回归就 skip Linux platform diff。

`playwright.visual.config.js` 里:
```js
expect: {
    toHaveScreenshot: {
        // 跨平台容忍像素差 · 5% 像素不一样 OK · 大改就 fail
        maxDiffPixelRatio: 0.05,
        threshold: 0.2,  // 每个像素的色彩差异容忍
    },
}
```

---

## 5. 漂移调试

跑完 fail 的话:
```bash
# Playwright 会生成 actual / expected / diff 三张图
npx playwright show-report

# 看 tests/visual/playwright-report/index.html
# 三张图并排:左 expected(基线)· 中 actual(当前)· 右 diff(红色高亮区)
```

常见 false positive:
- 字体抗锯齿(Mac vs Linux vs Windows 不同 · 字号微差) → 调 `maxDiffPixelRatio`
- 时间戳 / 用户名等动态内容 → 用 `page.evaluate(() => { document.querySelectorAll('.timestamp').forEach(e => e.textContent = '[masked]'); })` 抢先 mask
- 滚动条出现 / 消失 → 设 `viewport: { width, height }` 锁死

---

## 6. 与现有 E2E 套件的关系

| 套件 | 测什么 | 数量 | 位置 |
|---|---|---|---|
| `tests/e2e/*.spec.js` | 真账号端到端流程(登录 → 上传 → 改密 → 充值)| 17 spec | `tests/e2e/` |
| `tests/visual/baseline.spec.js`(本文)| 10 页 screenshot 基线 | 1 spec · 10 test | `tests/visual/` |

视觉跑挂 → 看图找漂移点。E2E 跑挂 → 看流程哪步错。两套互补。

---

## 7. 后续 / 待办

- [ ] 等整顿期收官 · 视觉基线稳定 · 评估上 CI(本机 Windows runner 或 self-hosted)
- [ ] 加移动端 viewport baseline(375x667 iPhone SE)· 验"手机端铁律"无破图
- [ ] 4 语都打基线(目前只打默认 zh · 因为 zh 字最短 · 漏的少)
- [ ] 暗 / 浅色 mode baseline(如果将来上 dark mode)

---

## 8. 参考

- Playwright 视觉回归官方文档:https://playwright.dev/docs/test-snapshots
- 主 E2E config:`playwright.config.js`(testDir 是 tests/e2e · 不跑本目录)
- 入门:`docs/ONBOARDING.md` §8 真账号 E2E

---

## 5. 视觉照搬机械闸(test_design_fidelity.spec.js · docs/pos/12)

与上面的 screenshot 回归不同:这是 **令牌级照搬闸** —— 把【设计稿快照】与【生产页本地渲染】的关键
元素 `getComputedStyle` 逐项比对(主色 #2563EB / 圆角 / box-shadow / font-size / 容器左对齐),
不一致 = 退出码 1 + 打印"哪页/哪选择器/稿 X 生产 Y"。治"施工不照搬设计稿反复返工"。

**自洽**:内置静态服务器伺服 repo + Playwright stub 所有 `/api/**`,渲染本地真 bundle,**无需真账号/
真后端**。设计稿快照入库在 `tests/visual/design/*.html`(不依赖桌面 · CI 也能跑)。

**跑法**:`node tests/visual/test_design_fidelity.spec.js`

**挂在哪**:pre-push(改 `static/pos/**` 或 `src/home/{pos,inventory,purchase}-*` 或 `tests/visual/design/*`
触发)。红了就是没照搬,自己回去对齐,不用肉眼抓。

**加新照搬页怎么补映射**(3 步 · 无隐藏步骤):
1. 把设计稿拷进 `tests/visual/design/<短名>.html`(设计稿改版也更新这份)。
2. 在 spec 的 `MAPPINGS` 加一项:`{name, design:'<短名>.html', route:'<core-boot 路由>', ready:'<生产就绪选择器>',
   layout:{sel,maxWidth}, tokens:[{design:'<稿选择器>', prod:'<生产选择器>', props:[...]}], bluemust, nosvgemoji}`。
3. 若该页要 stub 的接口没覆盖,在 spec 顶部 `API` 加 canned 响应(信封 `{ok,data}`)。
跑 `node tests/visual/test_design_fidelity.spec.js` 绿 = 照搬到位。
**就这 3 步**:"bundle 就绪"探针已数据驱动(只认 `routeTo`),加页不必再改它。

> **已覆盖**:桌台管理(餐厅稿 05 v2)、收款设置(POS 稿 13 · 即现金/PromptPay/刷卡那页 · 已建已上线)。
> **待页建好再补**(现在无页可比 · 不是漏做):
> - 收银设置(POS 稿 14「收银设置-平铺页」· 含小票/打印 · **与已建的「收款设置 13」是两个不同页** · 尚未建);
> - 采购主屏 / 拍照识别(采购稿 01/02 · 采购模块尚未建)。
> 这些页一旦建出来,按上 3 步加即可。
