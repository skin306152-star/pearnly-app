---
name: verification
description: 改完代码怎么算"验过了" —— 批次边界(什么必须当场验)、机械闸自查、真浏览器 E2E 验收硬门、async 路由 tripwire、push 后盯 CI 到绿的判绿口径。改完任何代码、准备 push、要判断 CI 是否真绿、或想说"验过了"之前用。
---

# 验证闭环

自己做 → 自己检 → 自己验 → 自己盯 CI。不把验证或擦屁股甩给 Zihao 或别的窗口。

## 1. 验证绑批次边界,不攒到最后

命中任一 = **大批次,当场验**:

- 碰高敏路径(登录 / OCR / 计费 / 推送 / POS 收款 / 多租户 / RLS / schema 迁移)
- 有用户可见 UI 改动
- 落地新 feature flag / 新路由 / 新迁移
- 改动量 ≥ ~200 行,或攒够一个可独立验证的功能单元(通常 ≥3 个逻辑提交)

**小批次可跳过当场验**(纯格式化 / 纯 docs / 测试-only / 无运行时面的重构 / 单文件 <~50 行机械改),并到批次末或交付前一起兜。

## 2. 机械闸:开工先拿基线,收尾跑全套

- 全套(等价 pre-push,不用真推):Git Bash 跑 `PYTHONIOENCODING=utf-8 sh scripts/git-hooks/pre-push`
- 逐道命令 + 触发条件 + 豁免法:`docs/GATES.md`
- 开工第 0 步先跑一遍,才知道哪些红是别窗口/存量的,不然会替别人的债背锅
- **闸别接管道**:`cmd | tee` / `| grep` 会吞掉退出码,判绿只认脚本自己的退出码
- **Windows 上必须带 `PYTHONIOENCODING=utf-8`**:闸脚本打印中文撞 cp874 会 `UnicodeEncodeError` 退 1 —— 检查其实通过了也报红,而且失败清单印不出来(已复现于 `check_ai_smell` / `check_authz_coverage`)
- 本地钩子当前没挂(原因见 `docs/context-engineering/2026-07-25-claude-md-simplify.md` 遗留表),所以**手跑不是可选项**

## 3. UI / 视觉验收:真浏览器,截图为证

只要改动涉及"看得见的东西",以下三样**都不算验过**:grep 类名、断言 `MODAL=true`、看代码觉得"应该对了"。窗口靠这些自欺过。

必须做的:

1. 真浏览器打开真实路径(Playwright 或本地反代 harness),抓 `isVisible` + `getComputedStyle` 真实值
2. 截图存 `tests/e2e/_artifacts/<批次>/`,报告里给路径
3. 手机视口(390×844)+ 桌面(1280×900)各过一遍;暗色主题看 `docs/ui/THEME_RESPONSIVE_VERIFY.md`
4. **动手改之前先确认要改的组件是生产真实活着的路径** —— 测试脚本能到达 ≠ 生产在用(踩过:改了"集成抽屉"全绿,生产根本没这抽屉,全白干)
5. `fill()` 绕过真实按键,验输入用 `keyboard.type` + 查 `activeElement`

## 4. 测试硬规

- async FastAPI 路由内部调 sync 库(Playwright sync_api 等):必须 `await asyncio.to_thread(...)`,并写真 async tripwire 测试(`IsolatedAsyncioTestCase` + `httpx.AsyncClient`,mock 里检测 `asyncio.get_running_loop()` 命中即 raise)
- sync mock 里跑绿**不能**声明"async 路由通了"。历史:138 个单测全绿,生产 5 个路由全 `Playwright Sync API inside the asyncio loop`
- 改了真 SQL 必须真库验一次:mock 单测测不到 SQL 语法/方言错(`MIN(uuid)` 报表 500 就这么漏的)
- 测出真 bug 必补一条守门测试锁住
- 复测必在**重启后的新进程**上:`/api/version` 返 200 ≠ 新码生效,查 `systemctl show mrpilot -p ActiveEnterTimestamp` ≥ push 时间
- 验真扣费/写库用唯一内容(塞 nonce),防文件指纹缓存命中让复验失真

## 5. push 之后盯 CI 到绿(三个假绿坑)

```powershell
gh run list --repo skin306152-star/pearnly-app --branch master --limit 5
gh run view <RUN_ID> --repo skin306152-star/pearnly-app --log-failed
```

1. **`gh run watch` 对 cancelled 也返回 0** → 判绿只认 `conclusion == success`
2. **多窗口同分支 push 会互掐**:别人的 push 会 cancel 你的 run → 必须确认自己的 commit 是那个绿 run 的祖先
3. **红了自己查自己修**,不推完就走;修不动就 `git revert` 先让 master 绿

## 6. 报告口径

拿 Zihao 的原话当尺子,别拿自己缩小后的范围当"全部完成"。没测到的、跳过的、还红的,直说。
