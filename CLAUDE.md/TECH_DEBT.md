# 🧹 Pearnly 屎山治理路线图(2026-05-15 启动)

> **大白话**:这个项目像一栋盖到 30 层的违章楼 · 能住但风一吹就晃 · 不能炸了重盖(里面住着真实付费客户)· 只能**每次接力修一点 · 渐进翻新**
>
> 等所有 NAV-IA Phase + 进项模块跑完时 · 代码也跟着翻新成"标准做法"

---

## 一、当前屎山实锤(2026-05-15 诊断)

### 1.1 量化指标

| 指标 | 数值 | 严重度 | 状态 |
|---|---|---|---|
| `home.js` 大小 | **1346 KB / 30071 行** | 🔴 | 待治 |
| TOP1 函数 `deleteEndpoint` | **12694 行** @ home.js:14940 | 🔴 这不是函数是垃圾场 | 待拆 |
| TOP2 函数 `closeSettingsModal` | 2386 行 @ home.js:27686 | 🔴 | 待拆 |
| **重复定义** `showToast`(签名还不一样) | 2 次 @ home.js:13461 + 14894 | 🔴 真 bug | 待修 |
| **空 catch** 静默吞咽错误 | **106 处** | 🔴 出问题查不到根因 | 待治 |
| 版本号注释 `// v##.x` 历史考古 | 713 处 | 🟡 噪音 | 长期清 |
| `window.*` 全局赋值 | 209 处 | 🟡 全局污染 | 长期 |
| `'use strict'` 不一致 | 26 处 | 🟡 | 长期 |
| `var` 残留(应该用 const/let) | 55 处 | 🟡 老/新 JS 混 | 长期 |
| `console.error/warn` 残留 | 92 处 | 🟢 部分留做日志 | 长期评估 |
| **UI 自动化测试** | **0 个** | 🔴 改 UI 没保险 | 待补 |
| **i18n 字典完整性脚本** | 不存在(NAV_IA_PRD §5 写要做但没做) | 🔴 缺翻译可能上线 | 待补 |

### 1.2 翻译成人话

- **home.js 1.3 MB / 3 万行** = 一本 600 页的厚书写在一张纸上
- **一个函数 12,694 行** = 一个人干 50 个人的活 · 不可读 · 不可维护
- **同名函数定义两次** = 装了两个同名开关,**永远只生效后定义的那个** → 真 bug
- **106 处空 catch** = 代码出错时假装没事继续跑 · 用户报 bug 你查不到原因
- **零测试** = 改一行要靠人点 100 次鼠标验证

---

## 二、每个接力窗口修一点 · 优先级清单

> **铁律**:每次接力窗口在干主任务之前,**至少挑 1 个 P0 或 P1 项**修了 · 修了就在本文档「✅ 已修」段打勾
>
> **不要一次修太多**:0.5-1 小时内能搞定的为佳 · 大改另开独立窗口

### 🔴 P0(谁接谁修 · 都是小事但堵大坑)

- [ ] **修 `showToast` 重复定义**(20 分钟)
  - 位置:home.js:13461(签名 `msg, type`)+ home.js:14894(签名 `msg, kind, duration`)
  - 做法:保留 line 14894 的版本 · 删 line 13461 · 全文搜 `showToast(` 看调用点参数对得上不
  - 风险:几乎为零(只是去重 · 不改逻辑)

- [ ] **写 `check_i18n.py` 字典完整性脚本**(30 分钟)
  - 位置:新建 `D:\Users\Skin\Desktop\pearnly_project\scripts\check_i18n.py`
  - 做法:50 行 Python · 解析 `home.js` 的 `I18N` 对象 · 验证 zh/en/th/ja 4 个语言块 key 集合一致 · 退出码非 0 阻塞部署
  - 这是 NAV_IA_PRD §5 自己写要做但项目根目录从来没有的脚本

- [ ] **加 1 个 Playwright 烟测**(2 小时)
  - 位置:新建 `D:\Users\Skin\Desktop\pearnly_project\tests\nav_ia_phase1.spec.js` + `playwright.config.js` + `package.json`
  - 覆盖:页面起得来 + 头像菜单弹得出 + ⌘K 起得来 + 4 语切换不崩
  - 这是项目第一个测试 · 后续测试都能加在这个框架上

- [ ] **批量改空 catch**(分批 · 每窗口 10-20 处)
  - 106 处 → 约 5-7 个窗口能清完
  - 改法:`catch (_) {}` → `catch (e) { console.error('[模块名]', e); }`
  - 真要吞咽的(如 localStorage)写注释 `catch (_) { /* localStorage 失败可吞 · 无用户影响 */ }`

### 🟡 P1(中等优先级 · 大坑但要专门窗口)

- [ ] 拆 `closeSettingsModal`(2386 行 · home.js:27686)→ 按 settings 各 tab 拆 5 个模块
- [ ] 拆 `deleteEndpoint`(12694 行 · home.js:14940)→ 这不是一个函数,是被 function 包住的代码堆 · 先理清边界
- [ ] 评估 92 处 `console.error/warn` · 留真错误日志 · 删调试残留
- [ ] **home.js 1.3MB 首屏加载慢**(2026-05-15 立项 · NAV-IA Phase 8 收尾时发现)
  - 现状:任何页面打开都要下载 1.3MB JS + 4 个 API · 慢 2-3 秒(Earn 进 admin 也卡)
  - 渐进翻新路线(**不一次性炸开**):
    1. 抽出 `loadAdminCostPage / loadAdminUsersPage` 两个 IIFE(约 1500 行)成 `static/admin/admin-business.js` · admin.html 引这个 + admin.js · 不引 home.js · admin 首屏从 1.6MB 降到 ~30KB · 卡顿 3s → 0.5s
    2. 抽出 `loadClientsPage` / 客户管理 IIFE → `static/clients/clients.js`
    3. 抽出 OCR / 上传识别 IIFE → `static/ocr/ocr.js`
    4. 每一步独立部署 + skin 测试 1 周稳定再做下一步
  - 每步 1-2 个接力窗口(0.5-1 天工时)· 不闭眼开干 · 等 Zihao 拍板某次任务专做这个
  - 测试节奏:每抽出一个模块 → skin 账号跑核心场景 → mrerp 老板视角测一次 → 稳定后再下一步

### 🟢 P2(长期清理 · 不急)

- [ ] `var` → `const/let` 全量改(55 处)
- [ ] `'use strict'` 统一(顶层加一次 · 去掉重复的 26 处)
- [ ] 历史版本号注释清理(713 处 `// v##.x`)

---

## 三、新代码必须遵守的标准 · 接力 agent 看这里

> **铁律(2026-05-15 起生效)**:所有新功能**不再往 home.js / home.css / home.html 里塞**
>
> 老的不动(铁律 · 付费用户在用)· 新的全部独立文件 · 等老的某个模块替换完了再删它

### 3.1 模块化铁律

**新功能必须新建独立文件**:

```
NAV-IA Phase 2 → sidebar 清扫
  ✗ 错:把 _initSidebarCleanup() 加到 home.js 末尾
  ✓ 对:新建 home.nav-ia-phase2.js + home.nav-ia-phase2.css · 用 <script type="module"> 引入

NAV-IA Phase 6 → 进项模块  
  ✗ 错:在 home.js 加几千行进项逻辑
  ✓ 对:新建 expense/ 文件夹 + expense.html + expense.css + expense.js
```

**例外**:NAV-IA Phase 1 已经按"老办法" append 到 home.js 了(因为是本路线图启动前做的)· 后续 Phase 2-8 + 进项模块**强制独立文件**

### 3.2 错误处理铁律

- ❌ 禁止 `catch (_) {}` 或 `catch (e) {}` 不写任何东西
- ✅ 至少写 `catch (e) { console.error('[模块名] 上下文描述', e); }`
- ✅ 真正可吞的(localStorage 失败 / sessionStorage 满)写**注释说明为什么吞**:
  ```javascript
  try { localStorage.setItem('key', val); }
  catch (_) { /* localStorage 满或被禁 · 不影响主流程 · 安静失败 */ }
  ```

### 3.3 i18n 铁律(已在 CLAUDE.md §4 语并重)

- 任何用户可见文本必须走 i18n key
- 新 key 4 语全(zh/en/th/ja)· 缺一不部署
- **顺序**:写入顺序 `th → en → zh → ja` · 字典存量顺序 `zh→en→th→ja` 不重排
- 部署前跑 `python3 scripts/check_i18n.py home.js --strict` 退出码 0 才能部署
  - 这个脚本 P0 待补 · 见 §2

### 3.4 函数与文件长度

| 项 | 标准 |
|---|---|
| 单函数行数 | ≤ 150 行(超过要拆) |
| 单文件行数 | ≤ 2000 行(超过要分模块) |
| 嵌套层级 | ≤ 4 层(超过要抽函数) |

### 3.5 测试铁律

- 加新交互(按钮 / 弹窗 / 快捷键)→ 必须配 Playwright 烟测
- 改既有功能 → **先看测试有没有覆盖 · 没有就先补测试再改**
- skin 账号是测试账号 · 任何 UI 改动接力窗口结束时 **给一份 skin 账号专属测试清单**(让用户手动验)
- 有 Playwright 测试的:自动跑 · 不用人验 · 跳过手动清单

---

## 四、治理目标时间表

| 时间 | 目标 |
|---|---|
| 2026-05 | P0 三件套清完(showToast 修 / check_i18n.py 加 / 1 个 Playwright 烟测) |
| 2026-06 | 空 catch 全部清完(106 → 0) |
| 2026-07 | 新代码 100% 模块化(NAV-IA Phase 2-8 + 进项模块全部独立文件) |
| 2026-09 | Playwright 测试覆盖核心路径 ≥ 30% |
| 2026-12 | home.js 拆分到 < 500 KB(deleteEndpoint / closeSettingsModal 拆完) |
| 2027-Q1 | 所有功能完成时 · 代码全是"标准做法" |

---

## 四点五、⚠️ 部署铁律的「系统层例外」(2026-05-15 发现)

**CLAUDE.md §"🚀 部署 & 打包铁律" 写的 "Claude Code 自己跑全部 · 绝不让 Zihao 手动粘贴" 在新版 Claude Code 里**部分失效**

**原因**:Claude Code 客户端有 **auto mode 安全分类器**(Anthropic 系统层 · 在 CLAUDE.md 之上)· 它**专门拦截**:
- AI 自动 SSH 到 production server
- AI 自己修改 `.claude/settings.local.json` 给自己加权限

这一层是 Anthropic 系统级保护 · `permissions.allow` 里的通用规则(如 `Bash(ssh *)`)**不够具体不能解锁**

**解锁方法**(用户做一次 · 永久通行):
在 `.claude/settings.local.json` 的 `permissions.allow` 数组里加这几条精确规则:
```json
"Bash(ssh root@45.76.53.194 *)",
"Bash(ssh -* root@45.76.53.194 *)",
"Bash(scp * root@45.76.53.194:*)",
"Bash(scp -* * root@45.76.53.194:*)",
"Bash(ssh root@45.76.53.194 'bash /opt/mrpilot/deploy.sh *')",
"Bash(ssh root@45.76.53.194 \"bash /opt/mrpilot/deploy.sh *\")",
"Bash(curl -s -o /dev/null -w * https://pearnly.com/*)",
```

加完后 · Claude 可以按 CLAUDE.md 部署铁律自动跑全套 scp + ssh + deploy.sh + 验证

**接力 agent 注意**:
- 看到部署被 auto mode 拦截 → **不是 CLAUDE.md 失效** · 是用户 settings.local.json 还没加精确规则
- 告诉用户加上面那 7 行就行 · 不要自己尝试改 settings(会被拦)

---

## 五、✅ 已修清单(每修一项打勾 + 写日期 + 写哪个窗口干的)

> 接力 agent 修完债务后必须在这段加一行:`- [✅] YYYY-MM-DD · 修了 XX · @<窗口名 / commit hash>`

- [✅] 2026-05-15 · 诊断完成 · 写 TECH_DEBT.md · @NAV-IA Phase 1 窗口
- [✅] 2026-05-15 · 修 `showToast` 重复定义(删 home.js:13461 旧版 · 276 调用点全兼容新版 line 14894) · @NAV-IA Phase 1 窗口
- [✅] 2026-05-15 · 记录"部署铁律的系统层例外"(§4.5) · @NAV-IA Phase 1 窗口

(以下空 · 等后续窗口补)

---

## 六、为什么不能推倒重来?

1. **付费用户在跑**:`mrerp@outlook.co.th`(Yearly)· `BAKELAB`(Pro)· `TIPCO Foods`(Pro)等真实付费 · 推倒 = 商业自杀
2. **P0-VAT 主线在改**:对账核心代码同步迭代 · 不能停
3. **业界标准玩法是"绞杀者模式"**(Strangler Pattern):新代码慢慢"绞杀"老代码 · 老的某个模块完全被新版替换完才删
   - Microsoft / Shopify / Stripe 都这么干过老系统
4. **每个窗口 30 分钟到 2 小时**:成本低 · 收益累积 · 不影响主线
