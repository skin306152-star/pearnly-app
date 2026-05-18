# Pearnly 启动检查报告

> **生成日期**:2026-05-18
> **生成会话**:屎山清理会话 阶段 1.5(阶段 2 之前的前置准备)
> **方法**:`importlib.util.find_spec` 静态查 35 个根目录 .py 的 import 能否解析(**不执行任何模块代码**)
> **本机环境**:Windows · Python 3.10.11(D:\Python310\) · pip 26.0.1

---

## 0. 结论速览

| 检查项 | 结果 |
|---|---|
| AST 语法解析(全部 .py) | ✅ 35/35 全过 |
| import 全部能解析的文件 | 27/35 |
| 有 import 失败的文件 | **8/35** |
| 缺失 import 总数 | **11 个** |
| 本机能直接 `python app.py` 启动? | ❌ **不能** — 缺 7 个第三方包 + 4 个幽灵模块 |
| 服务器(生产 v118.33.13.6)能跑? | ✅ 在线,所以服务器肯定有这 11 个 |

**关键判定**:**本地仓库与生产服务器代码不同步** — 4 个 `pdf_storage` / `pdf_searchable` / `excel_template_th` / `xero_pusher` 模块**从未在 git 历史里出现过**(`git log --all --diff-filter=AD` 零结果),但生产服务器在用。这是阶段 2 必须先解决的问题,否则永远没法在本机搭测试环境。

---

## 1. 35 个 Python 模块的 import 状态

### 1.1 ✅ 27 个全部 import 能解析

```
archive.py · bank_reconcile.py · email_ingest.py · engine_chain.py · erp_push.py
excel_export.py · excel_export_v108_backup.py · field_comparator.py
gemini_engine.py · gl_vat_reconciler.py · i18n_reports.py · invoice_grouper.py
line_client.py · nvidia_engine.py · ocr_engine.py · pdf_text_extractor.py
quality_check.py · rd_api.py · reconciliation_matcher.py · report_engine.py
typhoon_engine.py · vat_ai_analyzer.py · vat_excel_export.py · vat_excel_exporter.py
vat_file_classifier.py · vat_report_parser.py · vision_engine.py
```

> ⚠️ 注意:"import 能解析" ≠ "运行不会出错"。这些文件的所有顶级 import 都能找到,但函数体内可能有运行时错误、数据库依赖等。

### 1.2 ❌ 8 个文件 import 失败

| 文件 | 缺失的 import |
|---|---|
| `app.py` | excel_template_th · fastapi · pdf_searchable · pdf_storage · uvicorn · xero_pusher |
| `auth.py` | bcrypt · fastapi · jwt |
| `auth_signup.py` | fastapi · passlib |
| `db.py` | bcrypt · psycopg2 |
| `recon_routes.py` | fastapi |
| `report_routes.py` | fastapi |
| `vat_excel_routes.py` | fastapi · psycopg2 |
| `bank_recon_v2.py` | xlrd |

### 1.3 ❌ 11 个缺失 import 的全清单

#### 1.3.1 标准第三方包 — 7 个(本机装上就好,服务器肯定都有)

| import 名 | pip 包名 | 用于 | 被几个文件 import |
|---|---|---|---|
| `fastapi` | `fastapi` | Web 框架 | 6 |
| `uvicorn` | `uvicorn` | ASGI 服务器 | 1 (app.py:8094) |
| `psycopg2` | `psycopg2-binary` | PostgreSQL 驱动 | 2 |
| `bcrypt` | `bcrypt` | 密码哈希 | 2 |
| `passlib` | `passlib` | 密码工具 | 1 |
| `jwt` | `PyJWT` | JWT 编解码 | 1 |
| `xlrd` | `xlrd` | Excel(旧版 .xls)读 | 1 |

→ 已写到 `requirements.txt`。本机跑 `pip install -r requirements.txt` 即可补齐。

#### 1.3.2 🚨 项目内"幽灵模块" — 4 个

这 4 个**既不是 stdlib · 不是 pip 包 · 也不在本仓库的 .py 文件列表里**,但被代码 import:

| import 名 | 引用位置 | 是否有 ImportError 保护 | 用途推断 |
|---|---|---|---|
| **`pdf_storage`** | `app.py:48`(**顶级** · 无保护)<br>`app.py:1927, 2971, 2986, 3022`(调用 `.save_pdf` / `.delete_pdf` / `.get_pdf_abs_path`) | ❌ **无** | PDF 留底存储(v114 加) |
| `pdf_searchable` | `app.py:1916-1921`(try/except 内) | ✅ 有 | 把 OCR 结果叠回 PDF 做可搜索 PDF(v115 加) |
| `excel_template_th` | `app.py:2223, 2322`(try 块内 · **无 ImportError 守护**,外层 try except Exception 会兜) | ⚠️ 部分(被外层 try 吃) | 泰国销售明细 Excel 模板(v118.27.7) |
| `xero_pusher` | `app.py:3370, 7803, 7837, 7882, 7949, 8016`(多处都在 try/except ImportError 里)<br>抛 HTTP 500 `xero.module_missing` | ✅ 有 | Xero 集成(认证 / 推送发票) |

**git 历史核查**:
```bash
git log --all --diff-filter=AD -- pdf_storage.py pdf_searchable.py excel_template_th.py xero_pusher.py
# → 零结果(从未在 git add/delete 历史里)
```

**部署包核查**:
- 最新 `deploy_v118.32.5.5.36.tar.gz`:仅含 `home.js`, `home.html`, `app.py`(增量包)
- 最新 `deploy_v11841137.zip`:仅含 3 个前端文件
- 都不含这 4 个模块

**含义**:
1. 这 4 个文件**必定单独存在于服务器 `/opt/mrpilot/`**(生产线在跑,必须有)
2. 但**从未被纳入版本控制**,部署流程没覆盖它们
3. 本地仓库做任何代码动作都**无法在本机验证**(根本 import 不通)
4. 阶段 2 想建冒烟测试,必须先把这 4 个模块从服务器**同步回本地** + 纳入 git

---

## 2. 启动入口

```
# 开发模式(reload 开)
python app.py
# → 等价于 uvicorn.run("app:app", host="0.0.0.0", port=$PORT 或 7860, reload=True)

# 生产模式(systemd 拉起)
systemctl restart mrpilot  # 服务器 root@45.76.53.194
```

> 入口在 `app.py:8092-8094`。`app = FastAPI(...)` 在 `app.py:514`。

---

## 3. 环境变量配置需求

按"必要 vs 可选"分,从所有 `os.environ.get / os.getenv` 调用抽取:

### 3.1 🔴 必要(没设就跑不起来 / 没意义)

| 变量 | 默认 | 影响模块 | 说明 |
|---|---|---|---|
| `DATABASE_URL` | 无 | `db.py:30` | Supabase PostgreSQL 连接串 |
| `JWT_SECRET` | 空 | `auth.py:26` | JWT 签名密钥 · 空 = JWT 签发失败 |
| `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` | 空 | 9 个文件 | Gemini OCR · 空 = OCR 全挂 |

### 3.2 🟡 半必要(功能开关,不开就这功能用不了)

| 变量 | 默认 | 影响功能 |
|---|---|---|
| `EMAIL_INGEST_ENABLED` | "0" | 邮件收件自动化 |
| `EMAIL_ENCRYPTION_KEY` | 空 | 邮件密码加密 |
| `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` | 空 | LINE Bot |
| `LINE_LOGIN_CHANNEL_ID` / `LINE_LOGIN_CHANNEL_SECRET` | 空 | LINE 登录 |
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` / `_REDIRECT_URI` | 空 | Google 登录 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | `smtp.gmail.com:587` / 空 | 系统邮件 |
| `RESEND_API_KEY` | 空 | Resend 邮件后端 |
| `GITHUB_WEBHOOK_SECRET` | 空 | Git push 部署 webhook 验签 |
| `NVIDIA_API_KEY` | 空 | NVIDIA OCR 引擎(备路) |
| `TYPHOON_API_KEY` | 空 | Typhoon OCR 引擎(备路 · 已标 v105 废弃) |
| `GOOGLE_VISION_API_KEY` | 空 | Vision OCR 引擎 |

### 3.3 ⚪ 调参类(有合理默认,通常不动)

| 变量 | 默认 | 用途 |
|---|---|---|
| `PORT` | 7860 | uvicorn 端口 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `DEMO_IP_DAILY_LIMIT` | 20 | demo 账号 IP 限流 |
| `OCR_MAX_PAGES_PER_UPLOAD` | 5 | OCR 单次最大页数 |
| `OCR_MAX_FILE_SIZE_MB` | 20 | OCR 单文件最大 MB |
| `ERP_RETRY_TICK_SEC` | 30 | ERP 重试轮询周期(秒) |
| `EMAIL_INGEST_TICK_SEC` | 300 | 邮件收件轮询周期 |
| `ERP_PUSH_TIMEOUT_SEC` | 30 | ERP 推送超时 |
| `GEMINI_MODEL` | gemini-2.5-flash | Gemini 模型选择 |
| `NVIDIA_RATE_LIMIT_RPM` | 30 | NVIDIA 每分钟请求数 |
| `TYPHOON_RATE_LIMIT_RPM` | 8 | Typhoon RPM |
| `CONTACT_PHONE` / `CONTACT_LINE` / `CONTACT_EMAIL` / `CONTACT_ADDRESS` | 写死的官方联系方式 | 前端展示 |
| `ENABLE_RLS` | "0" | 数据库行级安全开关 |
| `PEARNLY_BASE_URL` | https://pearnly.com | OAuth 回调拼接基址 |

### 3.4 ⚠️ 有"安全相关默认值"的(不是 bug 但值得知道)

| 位置 | 变量 | 默认值 | 说明 |
|---|---|---|---|
| `db.py:72-73` | `DEMO_USERNAME` / `DEMO_PASSWORD` | `demo` / `demo2026` | 演示账号默认密码 — **如果生产 `.env` 没覆盖,这俩是公开可登的 demo 账号** |
| `db.py:91-92` | `DEMO_PLUS_USERNAME` / `DEMO_PLUS_PASSWORD` | `demo_plus` / `demoplus2026` | 同上,Plus 版 demo 账号 |

> 不在本审计的清理范围,只是顺便记录(超出本会话,记给后续)。

---

## 4. 配置文件状况

| 文件 | 状态 |
|---|---|
| `.env` | 不存在(.gitignore 已忽略,本地无 · 服务器肯定有) |
| `requirements.txt` | 本次新建(原本不存在) |
| `pyproject.toml` | 不存在 |
| `Pipfile` | 不存在 |
| `Dockerfile` | 不存在(部署用 systemd · 不走 Docker) |
| `*.service`(systemd) | 不存在于本仓库(在服务器 `/etc/systemd/system/mrpilot.service`) |
| `deploy.sh` | 存在 · `/opt/mrpilot/deploy.sh` 的本地副本 |
| `migration_v0.17.sql` / `migration_v0.4.0.sql` | 存在(2 个 SQL 迁移文件,服务器手动跑) |

---

## 5. 阶段 2 前置 TODO(供用户决策)

> **本节是观察 + 建议,不是要求**。本会话只产报告,不做这些动作。

### 必须解决(否则阶段 2 没法搭测试环境)
- [ ] 从生产服务器同步 4 个幽灵模块到本地 + 纳入 git
  ```bash
  ssh root@45.76.53.194 "ls -la /opt/mrpilot/{pdf_storage.py,pdf_searchable.py,excel_template_th.py,xero_pusher.py}"
  scp root@45.76.53.194:/opt/mrpilot/{pdf_storage.py,pdf_searchable.py,excel_template_th.py,xero_pusher.py} D:/Users/Skin/Desktop/pearnly_project/
  git add pdf_storage.py pdf_searchable.py excel_template_th.py xero_pusher.py
  git commit -m "sync: 补全服务器单独存在的 4 个模块到 git"
  git push
  ```
- [ ] 本机装依赖:`cd D:\Users\Skin\Desktop\pearnly_project && pip install -r requirements.txt`
- [ ] 准备一份本机 `.env`(可从生产 .env 拉副本 + 替换 DB 为测试库)
- [ ] 装好后再跑一次本报告的检查脚本,确认全 OK

### 建议解决(阶段 2 测试质量更高)
- [ ] 服务器 `pip freeze` 一份发回本地比对(`requirements.txt` 当前版本号是本机的,可能与服务器漂移)
- [ ] 考虑加 `.env.example` 列出所有环境变量名(不带值),让新接手 agent 一眼看见配置需求

### 单独动作(不必本会话做)
- [ ] 把 4 个幽灵模块**永久纳入 git** + 部署脚本同步(否则下次 git push 部署还是只覆盖根 .py,这 4 个模块依旧是服务器孤本)

---

## 6. 本次没做的事 / 局限

- ❌ **没真启动 app.py**:用户明确"不要真运行",且本机缺依赖也起不来
- ❌ **没 SSH 服务器核查**:超出本会话范围(清理专线 · 不做运维)
- ❌ **没检查动态 import**:`getattr(...)` / `importlib.import_module(<string>)` 等运行时反射方式未扫
- ❌ **没跑实际网络请求**:Supabase / Gemini API 等外部依赖未验证可达性

---

---

## 7. 修复后复测(2026-05-18 · 阶段 1.5+)

用户从生产服务器 scp 回 4 个幽灵模块 + git commit `90c1271` "rescue: pull production-only modules into git" + push GitHub 完成。

### 7.1 复测命令

```
PYTHONIOENCODING=utf-8 D:\Python310\python C:\Users\skin3\_audit_pearnly_imports_check.py
```

### 7.2 复测结果

| 指标 | 修复前 | 修复后 | 变化 |
|---|---|---|---|
| 项目本地 .py 总数 | 35 | **39** | +4(新加 4 个孤本) |
| 全部 import 能解析 | 27 | **31** | +4 |
| 有 import 失败的文件 | 8 | 8 | 不变(剩下都缺标准第三方包) |
| 不同的缺失 import 数 | 11 | **7** | -4(4 个幽灵全部消失) |
| "命名像本地模块但不存在" | 4 | **0** | ✅ 清零 |

### 7.3 修复后 import 状态

✅ **全部 31 个文件 import OK** 包含 4 个新加入的孤本:
- `excel_template_th.py`(8221 字节)
- `pdf_searchable.py`(6617 字节)
- `pdf_storage.py`(3432 字节)
- `xero_pusher.py`(14874 字节)

❌ **8 个文件仍 import 失败**,但**只**因为本机没装这 7 个标准 pip 包:
`bcrypt` · `fastapi` · `jwt` · `passlib` · `psycopg2` · `uvicorn` · `xlrd`

→ `pip install -r requirements.txt` 即可解决。

### 7.4 阻塞项状态

| 原阶段 2 前置 TODO | 状态 |
|---|---|
| 从生产服务器同步 4 个幽灵模块到本地 + 纳入 git | ✅ 已完成(commit 90c1271) |
| 本机装依赖 `pip install -r requirements.txt` | ⏳ 待用户决定何时做 |
| 准备本机 `.env` | ⏳ 待用户处理 |
| 部署脚本同步 4 个模块(防再失同步) | ⏳ 阶段 2 前需确认 deploy.sh / git-deploy 流程包含 |

### 7.5 后续观察

- demo 密码硬编码问题(§3.4):用户已确认 .env 值与硬编码相同,会单独处理(不在本会话)
- `pdf_storage` 顶级无守护 import 的风险已自动解除(现在 git 里有该文件)

---

*生成于 2026-05-18 · 本会话 阶段 1.5 / 1.5+*
