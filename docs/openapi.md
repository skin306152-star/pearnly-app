# 📡 Pearnly · OpenAPI 索引(REFACTOR-WC-G4)

> 整顿期 G 阶段 · 给前端 / 集成方 / 新 AI 窗口的 API 路由索引地图(2026-05-28 窗口 C · REFACTOR-WC-P2)。
>
> **不是手写 schema**(那是 FastAPI 自动生成)· **是路由分布 + 模块归属 + 接入点 + 已知 PRD 的索引**。
> 看本文 → 立刻找到"我要的接口在哪个 `*_routes.py`、归哪个 services 域、有什么契约测试兜底"。

---

## 0. 在线 OpenAPI

FastAPI 默认生成:

| 入口 | 用途 | 说明 |
|---|---|---|
| `https://pearnly.com/docs` | Swagger UI(交互) | 整顿期通常开放 · 真账号 login 后可试调 |
| `https://pearnly.com/redoc` | ReDoc(美观浏览) | 适合分发给会计师 / 集成方 |
| `https://pearnly.com/openapi.json` | 原始 schema | 可喂给 Postman / Insomnia / 各 SDK 生成器 |

> ⚠️ 如果上面 3 个 URL 在生产返 404 · 看 `app.py` `FastAPI(...)` 构造里有没有 `openapi_url=None` / `docs_url=None`(整顿期可能短暂关闭 · 等 G4 完善 schema 后默认开)。

---

## 1. 路由文件清单(整顿期 B 阶段产出 · 36 个 router)

> 历史巨石 `app.py`(原 10k 行)的路由已逐步拆出 · 每个 `*_routes.py` 单一职责。
> 新路由必须在这里加 router 文件(铁律 #17 / #21 / #23 / #27)· 不许塞 `app.py`。

### 🔐 Auth / Login(高敏 · Zihao 在场)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `login_routes.py` | `/api/auth` | `POST /login` · `POST /logout` | unit + spec 01-login | 主登录(JWT + jti) |
| `oauth_routes.py` | `/api/oauth` | `GET /google` · `GET /line` · `POST /callback` | unit | Google / LINE 第三方 |
| `auth_email_code_routes.py` | `/api/auth/email-code` | `POST /send` · `POST /verify` | unit + spec 17 | 6 位邮箱验证码 |
| `line_account_merge_routes.py` | `/api/auth/line-merge` | `POST /merge` | unit + spec 14 | LINE 账号合并到邮箱账号 |

### 💰 Billing / Credits(高敏 · 钱写入)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `billing_routes.py` | `/api/billing` | `GET /status` · `POST /topup-request` · `POST /charge-ocr`(内部)| unit + spec 11 + 16 | 充值申请 / 扣费 · 走 `services/billing/{charge,account_status,credits_schema,pricing}` |

### 👤 User / Me / Tenant(中敏)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `me_routes.py` | `/api/me` | `GET /` · `GET /lang` · `PUT /lang` · `PUT /password` | unit + spec 13 | 当前用户信息 / 改密 |
| `tenant_routes.py` | `/api/tenant` | `GET /companies` · `PUT /active` | unit | 多公司账套切换 |
| `workspace_routes.py` | `/api/workspace` | 工作区 / role 管理 | unit | 员工 / 老板 / 超管 |
| `console_team_routes.py` / `console_invite_routes.py` | `/api/team` | 成员/角色/邀请/转移(批5 后唯一团队管理面) | unit | 控制台管成员 |
| `settings_routes.py` | `/api/settings` | dup_check / ERP push mode / Gemini key | unit | 用户级设置 |

### 📸 OCR / 上传识别(高敏热路径)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `app.py` 内 | `/api/recognize` | `POST /(pdf/excel/image)` | spec 16 | **核心 OCR 入口 · 待 B1 抽** |
| `ocr_export_routes.py` | `/api/ocr` | `GET /history-quota` · `POST /export-*` | unit | OCR 历史 + 多种 Excel 导出 |
| `history_routes.py` | `/api/history` | `GET /list` · `GET /:id` · `DELETE /:id` · `PUT /:id/pages` | unit + spec 04-history | OCR 历史读 / 删 / 改 · 走 `services/ocr_history/store` |

### 📊 对账 / Recon(中敏)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `recon_routes.py` | `/api/recon` | 销项税核对 · GL 对账 · 银行(老)| unit + spec 06-reconcile | 2000 行 · 待拆(超 500) |
| `recon_jobs_routes.py` | `/api/recon-jobs` | 异步 job 提交 / 查询 | unit | A2.2 / Phase 4 后台异步 |
| `bank_recon_routes.py` | `/api/bank-recon` | 银行对账 v2 | unit | 走 `services/recon/bank_recon_v1_store` |
| `vat_excel_routes.py` | `/api/vat-excel` | 公式 Excel 对账 | unit | v4.9 公式 Excel |

### 🔌 ERP 集成(中敏)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `erp_routes.py` | `/api/erp` | endpoints CRUD · push · listing | unit + spec 08-erp-push | 1206 行 · 待拆 |
| `erp_mappings_routes.py` | `/api/erp/mappings` | 字段映射 | unit | 走 `services/erp/mappings_store` |
| `erp_xero_routes.py` | `/api/erp/xero` | Xero OAuth 推送 | unit | |
| `import_routes.py` | `/api/import` | 万能导入器(D4 / ADR-006)| unit | 走 `services/importer/template_learning` |

### 📥 客户 / 异常 / 通知 / 类目

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `clients_routes.py` | `/api/clients` | CRUD · 解析 | unit + spec 03-clients | 走 `services/clients/store` |
| `exceptions_routes.py` | `/api/exceptions` | 异常列表 · 处理 | unit + spec 05-exceptions | 走 `services/exceptions/store` |
| `notification_routes.py` | `/api/notifications` | 通知列表 / 已读 | unit | |
| `categories_routes.py` | `/api/categories` | 类目 CRUD | unit | |
| `rd_routes.py` | `/api/rd` | 国税局连接 | unit | |

### 📧 LINE / Email / 邮件抓取

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `line_binding_routes.py` | `/api/line/binding` | 绑定码 · 反查 · 解绑 | unit + spec 14-line-binding | 走 `services/line_binding/store` |
| `line_webhook_routes.py` | `/webhook/line` | LINE Bot 入消息 | unit | 不走 /api · 直 webhook |
| `email_ingest_routes.py` | `/api/email-ingest` | Gmail 自动抓发票 | unit | |
| `report_routes.py` | `/api/report` | 报表 / 周报 | unit | |
| `pages_routes.py` | `/` `/about` 等 | 公开 HTML 页 | unit | login.html / about.html 等 |

### 🛠️ Admin(Earn 超管 · 独立 SPA)

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `admin_users_routes.py` | `/api/admin/users` | 用户管理 | unit + spec 11(approve)| 669 行 · 待拆 |
| `admin_cost_routes.py` | `/api/admin/cost` | 成本追踪 | unit | |
| `admin_logs_routes.py` | `/api/admin/logs` | 操作日志 | unit | |
| `admin_diagnostics_routes.py` | `/api/admin/diagnostics` | 系统诊断 | unit | |
| `admin_migration_routes.py` | `/api/admin/migration` | 老数据迁移 | unit | |

### 🧪 Meta / Aliases / Version

| 文件 | 主路径 prefix | 关键 endpoint | 兜底测试 | 备注 |
|---|---|---|---|---|
| `meta_aliases_routes.py` | `/api/version` · `/v1/ocr/*` | 版本元数据 + 老 v1 OCR alias | unit | 给前端 version-banner 用 |

---

## 2. 响应模型 / Pydantic schema 索引

> 整顿期 G4 待办:**所有路由必须用 `response_model=`**(铁律 #15 踩坑 · v118.35.0.15 删字段没改 schema 导致 500)。
> 当前已用 schema 的路由(grep `response_model=` 抓出):

```bash
grep -r "response_model=" --include="*_routes.py" --include="app.py" | wc -l
```

**关键 Pydantic 模型分布**:

| Schema | 位置 | 用在哪 |
|---|---|---|
| `UserInfo` | `auth_signup.py` 或 `services/auth/` | `/api/me` · `/api/auth/login` |
| `TenantInfo` | `services/tenant/store.py` | `/api/tenant/companies` |
| `BillingStatus` | `services/billing/account_status.py` | `/api/billing/status` |
| `OcrHistoryItem` | `services/ocr_history/store.py` | `/api/history/list` |
| `ReconcileResult` | `services/recon/vat_recon_store.py` | `/api/recon/*` |

**G4 完善方向**(待 Zihao 在场处理 · 不在窗口 C 范围):
- 给所有 `*_routes.py` 路由加 `response_model=XxxOutput`
- 把现有 `dict` 返回 → Pydantic `BaseModel`
- 改字段先 `Optional + default None` 一个迭代后再真删(铁律 #15)
- `/docs` `/redoc` 在生产开放(目前可能 `openapi_url=None` 关闭)

---

## 3. 接入示例

### curl 调登录

```bash
# 1. 拿 JWT
TOKEN=$(curl -sS -X POST https://pearnly.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"你的邮箱","password":"你的密码"}' | jq -r .access_token)

# 2. 调 /api/me
curl -sS https://pearnly.com/api/me -H "Authorization: Bearer $TOKEN" | jq

# 3. 上传识别(假设 invoice.pdf 真发票)
curl -sS -X POST https://pearnly.com/api/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf" | jq
```

### Python SDK(没有官方 · 用 httpx)

```python
import httpx

client = httpx.Client(base_url="https://pearnly.com")
r = client.post("/api/auth/login", json={"username": "...", "password": "..."})
token = r.json()["access_token"]
client.headers["Authorization"] = f"Bearer {token}"

me = client.get("/api/me").json()
```

### TypeScript / JavaScript

```ts
const res = await fetch('https://pearnly.com/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: '...', password: '...' }),
});
const { access_token } = await res.json();
```

---

## 4. 集成方实务

- **CORS**:目前 `app.py` 配 allow_origins = `["*"]`(整顿期审查中)· 生产实际 LBs 加了 origin 白名单。
- **Rate limit**:OCR `/recognize` 走计费扣额度 · 没硬 rate limit。Auth 类有 IP-based 防爆破(铁律 PLG 反薅闸 · 24h 同 IP 3 邮箱)。
- **Idempotency**:幂等关键路径是充值审核 + OCR 去重(`services/ocr_history/store.py` find_ocr_by_hash)。OCR 上传文件指纹去重(同文件不二次扣费 · 命中缓存)。
- **错误格式**:统一 `{"detail": "..."}` 风格(FastAPI 默认)· 业务错误带 `body.ok = false`(铁律 #12 单一权威源)。HTTP 200 + `body.ok=false` 是合法失败响应 · 不要只看 HTTP code。

---

## 5. CI / 契约测试覆盖

| 类型 | 数量 | 路径 |
|---|---|---|
| 路由契约 unit test(每个 router 一个 `*_contract.py`)| ~30 | `tests/unit/test_*_routes_contract.py` |
| Service store contract test | ~20 | `tests/unit/test_*_store_contract.py` |
| 真账号 E2E spec(Playwright)| 17 | `tests/e2e/*.spec.js` |
| Integration tests(API + 真 DB + Mock 外部)| 21(20 是窗口 C 新加)| `tests/integration/*.py` |

跑法:
```bash
# 单测全量
python -m unittest discover -s tests/unit -p "test_*.py"

# 集成(需 docker-compose 起测试 DB + Mock)
python -m unittest discover -s tests/integration -p "test_*.py"

# E2E(需真账号 env)
$env:PEARNLY_E2E_USER = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_USER','User')
$env:PEARNLY_E2E_PASS = [Environment]::GetEnvironmentVariable('PEARNLY_E2E_PASS','User')
npx playwright test
```

---

## 6. 待办(本文未尽 · 留给后续窗口)

- [ ] 自动从 `openapi.json` 抓所有路由生成 markdown(脚本 · 不再手维护本文)
- [ ] 给每个 router 加 `summary` + `description` + `tags`(FastAPI native · `@router.get(..., tags=["billing"])`)
- [ ] 给所有路由统一加 `response_model=`(铁律 #15 防 500)
- [ ] 生产 `/docs` `/redoc` 开放策略明确(整顿期决策 · 默认开 vs 默认关 token-gated)
- [ ] 推到 readme.io / Stoplight Studio / Postman Public Workspace(让会计师 / 集成方上手)

---

## 7. 参考

- 项目宪法:`CLAUDE.md/CLAUDE.md`(铁律 #15 改返回字段必同步改 Pydantic)
- 整顿主计划:`CLAUDE.md/REFACTOR_MASTER_PLAN.md`(B 阶段路由拆分 / G4 OpenAPI 完善)
- ADR:`docs/refactor/adr-007-services-extraction.md`(services 拆分思路)· `adr-010-anti-bigfile-mechanism.md`(防屎山 4 件套)
- 入门:`docs/ONBOARDING.md`(新协作者 / 新 AI 窗口)
