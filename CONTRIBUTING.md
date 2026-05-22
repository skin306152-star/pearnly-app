# Contributing to Pearnly

> 这份文档是 Pearnly 项目的协作守则(对人 + 对 AI / Claude 窗口都适用)。完整的项目宪法见 `CLAUDE.md/CLAUDE.md`(450+ 行)· 本文件是它的"快速参考卡"。

---

## 🚫 4 不许 · 新功能禁止塞巨石文件(铁律 #17 · 2026-05-22 拍板)

Pearnly 当前有 4 个屎山文件 · 改一处容易牵连其他:

| 文件 | 行数 | 状态 |
|---|---|---|
| `app.py` | ~9450 | 渐进瘦身中(阶段 5 Task 5.1 抽走 11 个 billing 路由) |
| `home.js` | ~30000 | 单函数 12,694 行 · 渐进翻新中(独立 `static/*.js` 替代) |
| `home.css` | ~7000 | 视觉精修期 · 不再扩 |
| `db.py` | ~4000 | 包装层 · 复杂业务搬 `services/` |

**新功能 = 必须独立模块**:

1. **新后端路由 → 独立 `xxx_routes.py`**
   ```python
   # 新建 my_feature_routes.py
   from fastapi import APIRouter
   router = APIRouter()

   @router.get("/api/my-feature")
   async def my_feature():
       ...
   ```
   ```python
   # app.py 顶部
   from my_feature_routes import router as my_feature_router
   app.include_router(my_feature_router)
   ```
   现成参考:`billing_routes.py` · `report_routes.py` · `auth_signup.py` · `recon_routes.py` · `vat_excel_routes.py`

2. **新前端 JS → 独立 `static/xxx.js`**(IIFE 模式)
   ```js
   // static/my-feature.js
   (function () {
       const STATE = {};
       function init() { ... }
       document.addEventListener('DOMContentLoaded', init);
   })();
   ```
   现成参考:`static/version-banner.js` · `static/admin/admin.js` · `static/admin/admin-i18n.js`

3. **新 CSS → 独立 `static/xxx.css` 或 scoped 到组件 `.html`**
   - 不再往 `home.css` 加新 class
   - 独立 page(`/admin`)用独立 stylesheet

4. **新业务 SQL → `services/<domain>/<feature>.py`**
   - 简单 CRUD(数行)可以加 `db.py`
   - 复杂业务逻辑(数十行 + 多次查询)封装 service
   - 现成参考:`services/erp/mrerp_product_sync.py` · `services/monitoring.py`

---

## 🟡 例外条款 · 暂塞必须留迁出计划

如果**真的**必须暂时塞老文件(罕见 · 比如 90% 改动在老模块上 · 抽出来工作量大于本身改动):

1. **commit message 显式说**:
   ```
   feat(quick-fix): 临时在 home.js 加 X 函数

   暂存原因:本次只改 5 行 · 抽独立 .js 要重写 100 行 IIFE
   迁出 deadline: v118.40 OCR 模块重构时一并搬出
   ```

2. **必须建 entry**:`CLAUDE.md/TECH_DEBT.md` 或 `CLAUDE.md/EXECUTION_PLAN.md`

3. **超过 deadline 没迁** = 下个窗口接力时**先迁再做新事**

---

## ✅ 写代码前自检清单

每开始一个新功能前 · 内心走一遍:

- [ ] 这是后端 API?→ 不许加在 `app.py` · 建 `xxx_routes.py`
- [ ] 这是前端 module?→ 不许加在 `home.js` · 建 `static/xxx.js` 或独立 `.html`
- [ ] 这是 CSS?→ 不许加在 `home.css` · 独立 `.css` 或 scoped 组件
- [ ] 这是 db helper?→ 简单 CRUD 可以塞 `db.py`,复杂业务建 `services/`
- [ ] 触发例外条款?→ commit message + TECH_DEBT 入档 + 写 deadline
- 全过 → 开始写

---

## 🧪 提交前必跑(本机)

```bash
# 1) Python 静态 import check(防新加 import 没装包)
python scripts/check_imports.py --quiet

# 2) i18n 4 语完整性(防新文案漏 zh/en/th/ja 任一)
python scripts/check_i18n.py --strict --quiet

# 3) Unit tests(防回归)
python -m unittest discover -s tests/unit -p "test_*.py"

# 4) E2E smoke(可选 · 改了 login.html / home.js 顶栏 / 4 语切换才必须)
npx playwright test
```

全过 → push。任何一个红 → 修了再 push。

---

## 🚀 部署(自动)

- Pearnly 用 git webhook 自动部署:`git push origin master` → GitHub webhook → 服务器 git pull + restart mrpilot → 15 秒后 prod 生效
- **每次 push 即上线** · 没有 staging 环境
- 改动前问自己:这 push 上去能不能马上让所有用户用?

---

## 📁 项目文件地图

```
pearnly_project/
├── CLAUDE.md/                       # 项目宪法 + 状态(优先级最高)
│   ├── CLAUDE.md                    # 主宪法
│   ├── STATE_PEARNLY.md             # 当前状态(每窗口更新)
│   ├── EXECUTION_PLAN.md            # 8 阶段执行清单
│   ├── BACKLOG.md / MODULE_*.md     # 任务 + 模块路线
│   └── TECH_DEBT.md                 # 屎山治理待修清单
├── CONTRIBUTING.md                  # 本文件
│
├── app.py                           # FastAPI 主入口(渐进瘦身中)
├── db.py                            # DB 包装层
├── auth.py · auth_signup.py         # 鉴权
├── billing_routes.py                # billing 路由(2026-05-22 抽出)
├── report_routes.py                 # 报告导出路由
├── recon_routes.py · vat_excel_*    # 对账模块路由
├── services/                        # 业务 service 层
│   ├── erp/                         # ERP 集成(MR.ERP/Xero/FlowAccount)
│   └── monitoring.py
├── static/                          # 前端
│   ├── home.html · home.js · home.css   # 主 SPA(渐进翻新中)
│   ├── version-banner.js            # 独立 IIFE 模块示范
│   └── admin/                       # admin SPA(独立 layout)
│       ├── admin.js · admin-i18n.js
├── tests/
│   ├── unit/                        # contract tests(mock cursor · 不连真 DB)
│   ├── e2e/                         # Playwright smoke(测 prod 着陆页)
│   └── integration/                 # 跨模块集成
├── scripts/
│   ├── check_imports.py             # 静态 import 检查(CI 必跑)
│   └── check_i18n.py                # 4 语完整性(CI 必跑)
└── .github/workflows/ci.yml         # CI 配置(4 step · import/i18n/unit/e2e)
```

---

## 🌐 i18n(4 语并重铁律)

任何用户可见文字必须有 zh / en / th / ja 4 语 · 一个都不能漏。

- HTML:`<button data-i18n="btn-save">保存</button>`
- JS 字典:`'btn-save': { zh: '保存', th: 'บันทึก', en: 'Save', ja: '保存' }`
- 动态内容:必须 `window.subscribeI18n('module-key', _rerenderAll)`
- 提交前必跑:`python scripts/check_i18n.py --strict`(CI 也跑 · 不过不绿)

例外:`adm-*` key 是超管后台 · 只给 Zihao + 泰国合作伙伴 · zh + th 即可。

---

## 📦 依赖管理(REFACTOR-A7 · 2026-05-22 落地)

整顿期把 Python 依赖锁到具体版本 · 防"同样代码不同时间装出不同结果"。

**两层文件**:

| 文件 | 角色 | 谁改 |
|---|---|---|
| `requirements.txt` | **源** · 顶层依赖 + 大版本约束(`alembic>=1.13,<2.0`)· 人读 | 人 / Dependabot |
| `requirements.lock.txt` | **产物** · pip-compile 出 · 所有传递依赖钉死(`urllib3==2.5.0`)· 给 CI / prod 装 | pip-compile 自动 · 不手改 |

**CI 装包**用 `requirements.lock.txt`(确定性)· **本机开发**装哪个都行(锁文件更稳)。

**改依赖流程**:

```bash
# 1) 改源(加 / 删 / 升级)
vim requirements.txt

# 2) 重新编译 lock
python -m piptools compile requirements.txt -o requirements.lock.txt \
    --resolver=backtracking --strip-extras --no-emit-index-url \
    --no-emit-options --no-emit-trusted-host --allow-unsafe --newline lf

# 3) 同时 commit 两个文件
git add requirements.txt requirements.lock.txt
git commit -m "chore(deps): bump alembic to 2.x · REFACTOR-A7"
```

**Dependabot PR 处理**:Dependabot 改的是 `requirements.txt`,合并前**必须**在分支上跑一次 `pip-compile` 同步 `requirements.lock.txt` · 不然 CI 红。

**没装 pip-tools**:`python -m pip install pip-tools`(本机一次性 · 不进 requirements.txt)。

---

## 🚫 不要做的

- `git push --force` 到 master(可能擦掉别人未推 commit)
- `git commit --amend` 已 push 的 commit
- `git push --no-verify` 跳过 hook
- 改 `db.py` schema migration(删表 / 删字段 / DROP)未跟 Zihao 商量
- 在 feature branch 上叠新工作(永远从 master 开 · 或者直接在 master)

---

## 💬 沟通

- Issues / 决策记录:`CLAUDE.md/STATE_PEARNLY.md` 每窗口结尾更新
- 新铁律 / 架构决策:追加到 `CLAUDE.md/CLAUDE.md` 顶部
- Bug / 用户反馈:开 GitHub issue 或直接进 `CLAUDE.md/BACKLOG.md`

---

*最后更新:2026-05-22 · 由 Task 5.3 铁律 #17 落地一并产出*
