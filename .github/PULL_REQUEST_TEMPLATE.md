<!--
  Pearnly PR 模板 · 整顿期(REFACTOR）协作用
  权威规则:CLAUDE.md/CLAUDE.md(铁律)· CLAUDE.md/REFACTOR_MASTER_PLAN.md(整顿主计划)
-->

## 改了什么 / 为什么

<!-- 1-3 句:这个 PR 做了什么,以及为什么要做(说清 why,不只是 what)。 -->



**关联任务**:REFACTOR-<task-id>  <!-- 整顿期 commit / PR 必含 task ID(铁律 #20)。紧急 BUG 用 hotfix: · 纯文档用 docs: -->

---

## 5 道守门(本机全绿才提交 · CI 也跑)

- [ ] `python scripts/check_imports.py --quiet` → EXIT 0
- [ ] `python scripts/check_i18n.py --strict` → 0 missing 0 extra(4 语完整)
- [ ] `python -m unittest discover -s tests/unit -p "test_*.py"` → all OK
- [ ] `npx playwright test` → all passed(改了 login.html / 顶栏 / 4 语切换时必跑)
- [ ] `node --check <changed.js>` → 各改动 JS 都过(改了 JS 时)

---

## 巨石 / 敏感路径自检(铁律 #16 / #17 / #21 / #23)

- [ ] **没往巨石加新东西**:新路由进 `*_routes.py`(不进 `app.py`)· 新前端业务逻辑进 `src/home/*`(不进 `home.js`)· 新 CSS 独立(不进 `home.css`)· 新业务 SQL 进 `services/`、新 schema 走 Alembic(不进 `db.py` / 不加 `ensure_*`)
  - [ ] 若**确实暂塞**了巨石 → 已在 commit message 透明说明原因 + 迁出 deadline,并登记 `TECH_DEBT.md`
- [ ] **是否触碰敏感 / 高敏路径**(登录 / 注册 / 计费 / 配额 / OCR 热路径 / auth / RLS / DB schema / git-deploy):
  - [ ] 否
  - [ ] 是 → 已先口头跟 Zihao 汇报方案 · 由 Zihao 在场 review(不进自动并行批处理)
- [ ] **删/改了后端返回字段** → 已同步改对应 Pydantic `response_model`,删字段先 `Optional + default None`(铁律 #15)
- [ ] **每拆一个模块 / 每修一个真 bug** → 已带一个守门测试(铁律 #21.7 / 硬门槛 #4)
- [ ] 改动文件数 > 30(重构级)→ 已请 Zihao 先 review(铁律 #16 红线)

---

## 测试 / 验证

<!-- 怎么验证这个改动是对的(本机 / curl / 真站点 / 截图)。整顿期改 bug 须端到端测到 PASS(铁律 #25)。 -->


