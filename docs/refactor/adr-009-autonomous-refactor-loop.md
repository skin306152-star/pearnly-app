# ADR-009 · 无人值守自主重构 loop(/loop + 安全替身机制)

> **状态**:已采纳(2026-05-28 · Zihao 拍板「无人值守 · 含高敏」· 见铁律 #26 + `docs/refactor/AUTONOMOUS_LOOP.md`)· 已实跑一夜验证
> **关联 task**:REFACTOR-B2(`db.py`)· B1(`app.py`)· C1(`home.js`)· C3(`home.html`)· I1/I2(死码/静默吞错)
> **关联文档**:`docs/refactor/AUTONOMOUS_LOOP.md`(Loop 指令原文)· `BATCH_STRATEGY.md`(§9.5 操作模型)· ADR-007(services 抽取范式)
> **关联铁律**:#26(无人值守自动修 + 安全区/高敏两档 + 自主 loop 高敏例外)· #16(C 档 push)· #25(自跑闭环)

---

## 背景

整顿到 2026-05-28,巨石拆分(`db.py`/`app.py`/`home.js`/`home.html`)还剩大量重复性「拆=copy-out、搬=接线、删=死码」的活。Zihao 希望**无人值守**也能持续推进——没人盯着的窗口、headless、或定时 `/loop` 自跑——并且这次**含高敏**(计费/auth/OCR 热路径),不再像 `BATCH_STRATEGY.md` §9.5 那样「高敏一律等 Zihao 在场」。

但「无人值守碰高敏」与既有铁律(#16 关键路径大改先汇报、§9.5 高敏 Zihao 在场)冲突。本 ADR 记录怎么用**安全替身**化解冲突,以及一夜实跑后发现的**边界**。

## 决策

**用 `/loop` 动态自调度跑「每轮一块拆搬删」的循环;高敏块用 4 条「安全替身」替代「Zihao 在场」(铁律 #26 自主 loop 例外)。**

### 每轮闭环(经一夜 12 轮验证有效)

1. 读 4 文档(CLAUDE.md 铁律 #26 / STATE / REFACTOR_MASTER_PLAN / BATCH_STRATEGY)→ 找下一块。
2. **re-grep 真实行号**(行号每轮漂移 · 绝不信文档旧行号)。
3. 做这块:`copy-out` 新文件 → `import db` + 运行时 `db.get_cursor()` → db.py 尾 `from services.X import a as a` re-export(调用点零改 · ADR-007 范式)→ node 按行号删原定义(保 LF/CRLF + 边界 assert + 字节校验)。
4. 跑全 6 道守门(black/ruff · check_imports · check_i18n · 全量 unittest · node --check · build)+ 每块带契约测试。
5. commit(含 `· REFACTOR-id`)+ **单独一条** `git push origin master`。
6. `gh run watch` 独立查 CI 真绿;高敏块再用测试账号跑真账号 E2E。
7. CI 或 E2E 红 → `git revert` + push,绝不留红。
8. 更新 STATE + 主计划 + BATCH §10(**每轮必写** = 抗上下文压缩 · 下轮重读即接上)。

### 4 条安全替身(替代「Zihao 在场」· 仅自主 loop 场景成立)

| # | 替身 | 作用 |
|---|---|---|
| A | **纯结构性 · 0 逻辑改** | 只挪代码,绝不改业务逻辑/判定/字段。verbatim 搬 + 程序化提取(node 切片+正则),不手抄。 |
| B | **真账号 E2E 闸** | 推送部署后用测试账号跑真站点 E2E(登录 + 受影响流程),通过才算这块完成。 |
| C | **失败自动回滚** | CI 或 E2E 红 → `git revert` + push,绝不把红留在 master。 |
| D | **永不真付** | 计费可测(系统无自动支付通道 · 改内部台账数字 · Earn 可重置),但只动测试账号,绝不碰真付费用户(mrerp)余额。 |

## 实跑结果(2026-05-28 一夜 · 经验数据)

- **12 轮 · 25 commits · CI 全绿 · 0 回滚 · 0 红**。
- `db.py` **3356 → 1731 行(-48%)**:抽 7 个 services 域(user_settings / ocr_history 整域 / line_binding / credits 只读分析 / 多公司·账套 / 定价纯计算 / preferred_lang)+ 删 2 批死码(用量计数器 / demo 播种)。
- `home.html` 6428 → 4410(抽 head 内联 `<style>` 巨块 → `home-37`)。
- `home.js` I1 静默吞错 2 → 0。
- Google 级综合进度 **83% → 87%**。
- 每块:re-export 范式 → 调用点零改;ruff 多次抓出漏 `db.` 前缀的跨域裸调(如 `_bkk_year_month`、`_extract_summary_fields` patch 目标),补齐即过 —— **守门链确实兜住了「纯搬家」里的细节漏洞**。

## 发现的边界(重要 · 下一窗口必读)

**「干净无人值守 surface」会耗尽。** 一夜跑完后,剩下的块**都不适合无人值守**,即便铁律 #26 授权:

1. **安全替身 B(E2E 闸)只和 E2E 覆盖一样强**。`charge_ocr` 扣费写入、LINE 绑定、routeTo 多点派发——现有 E2E 套件覆盖不到的路径,「绿」不代表真没坏。这类**不该**无人值守 rush,残余风险会悄悄上线给付费用户。
2. **「纯结构性」对某些块不成立**。`home.js` 顶层函数组(`loadHistoryPage` 等)被 routeTo 9+ 处裸名调 + 引用 module-local `currentRoute`,抽出要改 routeTo 调用点 = 牵动导航中枢,不是干净 copy-out。
3. **有些块要先造新机制**。`home.html` body 拆分需要运行期模板注入机制(新代码,不是搬)。
4. **死码判定要严**:本夜一度以为 `page-automation`(标了"永久隐藏·无路由")是死的,严格 grep 才发现仍被 integration 配置按钮 + recon-center `navigateTo` 调用 —— **活的**。低引用 auth 函数(`reset_password` 等)是「单调用」不是「死」。

**结论**:自主 loop 最擅长的是**有充分 E2E/单测兜底的、纯结构性的 copy-out 与死码删除**。一旦进入「E2E 盖不全 / 非纯结构 / 需设计新机制」的块,应**留给 Zihao 在场会话或单独谨慎一轮**,而不是继续无人值守硬推。

## 后果

- ✅ 重复性安全拆分/删死码可无人值守批量推进,速度快、质量有守门链保证。
- ✅ STATE 每轮写 = 上下文压缩/换窗口无缝接力。
- ⚠️ 高敏块的安全性**完全依赖 E2E 覆盖广度**;E2E 不足的高敏块,无人值守不安全(本 ADR §边界 #1)。
- ⚠️ 需要人判断「这块是否还属于干净 surface」;判断错(把非纯结构当纯结构)会引入静默回归。

## 备选(未采纳)

- **全等 Zihao 在场做所有高敏**(§9.5 旧口径):安全但慢,且 Zihao 是非技术用户,逐块陪跑成本高。
- **完全不碰高敏,只无人值守做安全域**:更保守,但 `db.py`/`app.py` 永远到不了验收行数(剩余大头在高敏域)。

本 ADR 取中间:**安全域 + 有 E2E 兜底的高敏域无人值守跑;E2E 盖不全的高敏 + 需设计的块留人在场**。
