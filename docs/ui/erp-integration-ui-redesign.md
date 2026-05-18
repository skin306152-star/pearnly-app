# ERP Integration UI · Redesign Design

> **Status**: design only. **Implementation gated behind Zihao's review.**
> **Scope**: the "自动化 → ERP 对接" panel in `home.html` / `home.js` —
> what to keep, what to delete, what to replace with the new flow now
> that MRERPAdapter (and the Customer-Sync preflight from P1-B) is live.
>
> Companion docs:
> [MRERPAdapter README](../integrations/mrerp-adapter-readme.md) ·
> [Master-data sync design](../integrations/mrerp-master-data-sync-design.md) ·
> [Exception rules audit](../audits/exception-rules-audit.md)
>
> Generated 2026-05-18 by Task C of the P1 push.

---

## TL;DR

The legacy ERP UI was built when the only adapter was a generic
"Webhook URL + Secret Token" endpoint. Three things changed since:

1. **CLAUDE.md §7** retired HTTP reverse-engineering — Webhook was the
   manifestation of that approach for ERPs without a public API.
   Webhook endpoints will be deprecated for MR.ERP-style adapters.
2. **MRERPAdapter** (P0) replaces the Webhook plumbing for MR.ERP.
3. **Customer-Sync preflight** (P1-B Phase 5) makes the "字段映射 →
   客户映射" tab redundant for MR.ERP — the adapter resolves the
   customer code itself from the OCR buyer fields.

The new UX:
- Single screen with **ERP system cards** (MR.ERP, Xero, FlowAccount-soon).
- Per-card "Connect" CTA → full-screen modal with **3-step wizard**:
  client → credentials → company + push mode.
- Push logs become a **sidebar tab** with multiselect / batch retry /
  batch delete.
- The whole **"字段映射" tab disappears for MR.ERP** (kept for Xero
  until Xero gets the same sync treatment).
- Configured ERPs show **at-a-glance health**: last push time, total
  pushed, failure count, "test connection" pill.
- Empty state has prominent onboarding copy + the relevant card.

**Goal**: a user who's never seen the page can pick an ERP, enter
credentials, and be pushing invoices in **under 3 minutes** without
ever touching a "Webhook URL" field.

---

## 1 · Current state audit (read-only inventory)

### 1.1 The legacy ERP panel (home.html · home.js)

**Container**: [home.html:2680-2768](../../home.html) — the "自动化 → ERP
对接" panel inside `.auto-tabs`.

```
.auto-panel[data-auto-panel="erp"]
├── .auto-panel-head (title + status pill)
├── .erp-subtabs                                  ← 2 subtabs ⚠️
│   ├── data-erp-subtab="connect"   "连接 & 推送日志"
│   └── data-erp-subtab="mappings"  "字段映射"     ← deletes for MR.ERP
├── .erp-subpanel[data-erp-subpanel="connect"]
│   ├── #erp-connect-cards          (Xero card via IIFE)
│   ├── #erp-today-stats            (今日推送统计)
│   ├── #erp-endpoints-list         (legacy webhook endpoint cards) ⚠️
│   ├── #btn-add-endpoint           "+ 新增端点" button             ⚠️ DELETE
│   └── .erp-logs-section (collapsed) — filter chips + batch bar +
│                                         #erp-logs-list
└── .erp-subpanel[data-erp-subpanel="mappings"]
    └── .erp-map-subtabs
        ├── clients   ← P1-B sync makes this redundant for MR.ERP
        ├── accounts  (advanced)
        ├── taxes     (advanced)
        └── products  (advanced)
```

**Modal**: [home.html:3433-3510](../../home.html) — `#endpoint-modal`.

```
#endpoint-modal
├── modal-head ("新增 ERP 端点" / "编辑 ERP 端点")
└── modal-body
    ├── #ep-adapter-picker (webhook | flowaccount-soon)
    ├── #ep-name        (端点名称)
    ├── #ep-fields-webhook (#ep-url + #ep-token)         ⚠️ Webhook fields
    ├── #ep-is-default switch
    ├── #ep-auto-push switch
    ├── #ep-test-result
└── modal-foot (test / cancel / save)
```

### 1.2 JS handlers (home.js)

| function | line | role |
|---|---|---|
| `openEndpointModal(editingId)` | [home.js:15520](../../home.js) | reset + show endpoint-modal |
| `saveEndpoint()` | [home.js:15644](../../home.js) | POST /api/erp/endpoints |
| `deleteEndpoint(endpointId)` | [home.js:15760](../../home.js) | DELETE /api/erp/endpoints/:id |
| `btn-add-endpoint` click | [home.js:15781](../../home.js) | opens modal in "new" mode |
| `endpoint-modal-close` click | [home.js:15784](../../home.js) | close modal |

Other components in the same panel (Xero card render, today stats,
push-logs filter chips + batch bar) are independent IIFEs and stay
mostly as-is — they just move into the new layout.

### 1.3 i18n keys (home.js translations)

Keys that disappear when the legacy flow is gone:
`auto-erp-add`, `ep-modal-title-new`, `ep-modal-title-edit`,
`ep-adapter`, `ep-adapter-webhook`, `ep-adapter-webhook-desc`,
`ep-name`, `ep-name-ph`, `ep-url`, `ep-url-hint`, `ep-token`,
`ep-token-ph`, `ep-token-hint`, `ep-is-default`, `ep-auto-push`,
`ep-test-btn`, `ep-list-empty`, `ep-adapter-flow-desc`, `tag-soon`.

Per CLAUDE.md i18n iron rule: removal goes through all 4 lang blocks
(zh/en/th/ja) atomically — same single commit.

### 1.4 Backend (kept · not touched)

- `app.py` routes for `/api/erp/endpoints` (CRUD) and
  `/api/erp/endpoints/:id/push` — the **endpoints table is reused**,
  rebranded as "configured ERP connections" rather than "Webhook
  endpoints". `adapter` column already accommodates `mrerp`.
- `erp_push.py` keeps `push_webhook` as the fallback adapter for
  Webhook-style ERPs (some tenants still need it for custom systems).
- `services/erp/mrerp_adapter.py` is the new path for `adapter="mrerp"`.

### 1.5 Routes affected

| route | change |
|---|---|
| `GET /api/erp/endpoints` | response stays; UI consumes it differently |
| `POST /api/erp/endpoints` | gets new `config` shape for `adapter="mrerp"` |
| `PATCH /api/erp/endpoints/:id` | same |
| `DELETE /api/erp/endpoints/:id` | unchanged |
| `POST /api/erp/endpoints/:id/test-connection` | new endpoint — drives MRERPAdapter.login + select_company + dialog_log |
| `POST /api/erp/endpoints/:id/push` | adapter dispatcher; `adapter="mrerp"` routes to MRERPAdapter.upload_invoice_batch |

The "test-connection" route is the only NEW backend surface in scope
for this redesign. Everything else is UI repaint.

### 1.6 Where the leftover "字段映射" tab still adds value

For Xero today (and for FlowAccount when it ships), the field-mapping
tab is still necessary — those adapters don't have an OCR-driven sync
preflight yet. The plan is **conditional hide**:

- adapter list contains only `mrerp` → 字段映射 tab hidden
- adapter list contains anything else → tab shown, but the "客户映射"
  sub-tab inside is hidden if every mapped client's `erp_type` is `mrerp`

This keeps the surface honest while preserving Xero workflow.

---

## 2 · New design

### 2.1 Top-level layout

```
┌─────────────────────────────────────────────────────────────┐
│ 自动化 → ERP 对接                              加载中 / 已配置  │ status pill (existing)
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│ │  MR.ERP      │ │   Xero       │ │ FlowAccount  │  ← ERP cards
│ │  Pearnly 客户 │ │  Pearnly 客户 │ │  即将上线     │
│ │  上次推送 2h  │ │  尚未连接    │ │              │
│ │  [连接]      │ │  [连接]      │ │  [即将]      │
│ └──────────────┘ └──────────────┘ └──────────────┘         │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │  推送日志                          [全部] [✓成功] [✗失败]  │ ← sidebar tab
│ │  • Pearnly Test Co 2026-05-18 12:30 ✓                  │
│ │  • Skin Trading 2026-05-18 09:15 ✓                     │
│ │  ...                                                    │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Card states:
- **未配置**: gray with prominent "[连接]" CTA
- **已配置 + 健康**: white + green pill "上次推送 N 分钟前 · 共 Y 张 · 0 失败"
- **已配置 + 警告**: white + amber pill "上次推送失败 · 点击查看"
- **测试连接中**: white + spinner

### 2.2 The 3-step connect wizard (per-ERP modal)

Click on an ERP card → full-screen modal (≥ 800px wide; on mobile,
full-screen sheet).

```
┌─────────────────────────────────────────────────────────┐
│ ● ─── ○ ─── ○        连接 MR.ERP                  [×]   │
│ Step 1 of 3                                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  这个连接用于哪些客户?                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │ ☐ Skin Trading Co., Ltd.                      │    │
│  │ ☐ 大象贸易有限公司                              │    │
│  │ ☐ Bake Lab Bakery Supplier                    │    │
│  │ ☑ TIPCO Foods                                 │    │
│  │ ☐ 全选                                        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  💡 这些客户的发票将被推送到 MR.ERP                       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                              [取消]   [下一步 →]         │
└─────────────────────────────────────────────────────────┘
```

**Step 1 — 选客户**: which Pearnly clients route to this MR.ERP
connection. Multi-select, defaults to none (forces an explicit pick).
On the rare tenant who pushes everyone to the same MR.ERP, a "全选"
shortcut covers it. Backend stores this as a `client_ids: int[]`
column on `erp_endpoints` (today the column is per-tenant; design
keeps it backwards-compatible).

```
Step 2 of 3
┌─────────────────────────────────────────────────────────┐
│  填入 MR.ERP 登录信息                                    │
│                                                          │
│  系统地址                                                │
│  ┌────────────────────────────────────────────────┐    │
│  │ https://www.mrerp4sme.com                     │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  用户名 / 密码                                           │
│  ┌────────────────────────┐  ┌────────────────────┐    │
│  │ test01                │  │ ••••••              │    │
│  └────────────────────────┘  └────────────────────┘    │
│  💡 密码会用我们的密钥加密 · 数据库里不存明文              │
│                                                          │
│  [🔍 测试连接]    ✓ 已连接 · 看到 1 个公司                │
│                                                          │
├─────────────────────────────────────────────────────────┤
│            [← 上一步]    [取消]    [下一步 →]            │
└─────────────────────────────────────────────────────────┘
```

**Step 2 — 凭据 + 测试连接**:
- `system_url` — pre-filled to `https://www.mrerp4sme.com` for now;
  editable when MR.ERP runs on a tenant's own host.
- `username` / `password`.
- "测试连接" button calls the new backend `POST /api/erp/endpoints/:id/test-connection`
  which spins up MRERPAdapter.login + select_company, returns
  `{ ok, companies_seen, dialog_log }`.
- On success, show ✓ pill with company count + auto-advance hint.
- On failure, show the **friendly message** from
  `services.erp.mrerp_business_friendly.get_friendly(reason, lang)`.

Never disable "下一步" entirely — let the user proceed even without a
successful test (some tenants have flaky networks). But warn them.

```
Step 3 of 3
┌─────────────────────────────────────────────────────────┐
│  选公司 + 推送模式                                        │
│                                                          │
│  公司                                                    │
│  ┌────────────────────────────────────────────────┐    │
│  │ ▼ TEST2019 (Database: TEST2019)               │    │
│  └────────────────────────────────────────────────┘    │
│  💡 你这个 MR.ERP 帐号里看到的公司                        │
│                                                          │
│  推送模式                                                │
│  ◉ 识别后自动推送(不需要手动)                            │
│  ○ 我手动点「推送」才推                                  │
│                                                          │
│  字段值需要 Pearnly 自动建客户码吗?                       │
│  ◉ 自动建(推荐 · 1 个客户大约 30 秒)                    │
│  ○ 不要 · 等我自己在 MR.ERP 建好再来推                   │
│                                                          │
├─────────────────────────────────────────────────────────┤
│            [← 上一步]    [取消]    [完成 ✓]              │
└─────────────────────────────────────────────────────────┘
```

**Step 3 — 公司 + 推送模式**:
- Company dropdown — populated from the test-connection response
  (`companies_seen`).
- 自动推送 yes/no → maps to existing `ep-auto-push` flag.
- 自动建客户码 yes/no → maps to MRERPAdapter constructor
  `master_data_auto_create`. Note: while the auto-create blocker
  documented in [the customer-sync code](../../services/erp/mrerp_customer_sync.py)
  is unresolved, this toggle is hidden (or visible with a "暂未上线"
  badge).

Save: `POST /api/erp/endpoints` with `adapter="mrerp"` and
`config={system_url, username_enc, password_enc, comidyear, seldb,
auto_create_customer}`. The encryption happens server-side via
`kms_helper.encrypt_str`.

### 2.3 Push-log sidebar tab

Today the log lives inside a `<details>` collapsible. New UX promotes
it to a **first-class sidebar tab** alongside the ERP cards.

```
┌─ Cards ──────────────────────────┐ ┌─ Logs ───────────┐
│ MR.ERP    Xero    FlowAccount    │ │ [全部][✓][✗][↻] │
│                                  │ │                  │
│                                  │ │  ☐ 2026-05-18    │
│                                  │ │     Skin Trading │
│                                  │ │     ✓ 12:30      │
│                                  │ │  ☐ 2026-05-18    │
│                                  │ │     TIPCO Foods  │
│                                  │ │     ✓ 11:55      │
│                                  │ │  ...             │
│                                  │ │                  │
│                                  │ │ ─────────────────│
│                                  │ │ [批量重推][清空选]│
└──────────────────────────────────┘ └──────────────────┘
```

- 多选 checkbox per row → batch retry / batch delete (existing code
  preserved).
- Row-level click expands to show: invoice details + raw response +
  the friendly message from `mrerp_business_friendly` for failures.
- Filter chips kept (success / failure / retrying / auto / manual).
- "今日推送统计" (`#erp-today-stats`) moves into the cards as a per-
  card mini-stat (last-push time, success count, failure count). The
  panel-level today-stats is removed to save vertical space.

### 2.4 Empty state

For tenants with zero configured ERPs, the cards section is replaced
with a single onboarding banner:

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│     还没有连接任何 ERP · 点下面的卡片开始连接              │
│                                                          │
│     ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│     │  MR.ERP    │ │   Xero     │ │ FlowAccount │       │
│     │   [连接]   │ │   [连接]    │ │  即将上线   │       │
│     └────────────┘ └────────────┘ └────────────┘       │
│                                                          │
│     💡 推送是自动的 · 设置一次,日常使用不再来这页          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3 · UX iron rules (compiled from CLAUDE.md + Task C brief)

1. **用户只回答业务问题,不接触技术参数.**
   - 不出现 "Webhook URL" / "Secret Token" / "Adapter" 类词汇
   - "comidyear / seldb" 这种字段隐藏 — UI 显示 "公司" 让用户从下拉选
   - 加密 / Fernet / kms_helper 一律不暴露给用户

2. **错误信息说人话.** 全路径走
   `services.erp.mrerp_business_friendly.get_friendly(reason, lang)` —
   把 `ไม่พบข้อมูลรหัสลูกค้า` 翻成"客户码不存在,需先创建" / 英 /
   繁中。Push 日志里展开 row 时,raw text 折叠在 "查看原文" 里。

3. **测试连接 必须有 ·** 不依赖用户手动验证。Step 2 + 卡片每次刷新都
   后台跑一次 health-check (10s 缓存避免风暴)。

4. **配置后状态可视化.** 卡片上显示:
   - 上次推送时间(相对时间 "5 分钟前" / "2 小时前")
   - 累计推送数(本月)
   - 失败数(本月,>0 时变 amber)
   - 当前模式(自动 / 手动)

5. **配好后用户不用再来这页 ·** 除非:
   - 改密码 / 凭据失效
   - 加新客户
   - 切换推送模式
   - 看日志
   首页 dashboard 显示推送状态,异常时主动浮窗提示,把用户拉回来。

6. **4 语 i18n 完整覆盖** (CLAUDE.md "对外功能" 规则) — th/en/zh/ja
   每个新字段 4 语并写,缺一个不许部署。

7. **手机端必须适配** (CLAUDE.md 手机端铁律) — 卡片在 ≤800px 改竖向
   堆叠,modal 全屏,wizard 3 步保留,sidebar 日志改 tab 切换。

8. **铁律 §7** — 浏览器内 only;UI 只通过 backend 调 MRERPAdapter,
   永远不直接发 HTTP 到 mrerp4sme.com。

---

## 4 · Delete list (when the new UI ships)

### 4.1 HTML

Delete from [home.html](../../home.html):

| line(approx) | what |
|---|---|
| 2703-2706 | `<button id="btn-add-endpoint">` "+ 新增端点" |
| 2702 | `<div id="erp-endpoints-list"></div>` (legacy webhook endpoint cards) |
| 3433-3510 | entire `#endpoint-modal` block |
| 2750-2767 | the whole `data-erp-subpanel="mappings"` panel — **conditionally**: keep when adapter list includes Xero |
| 2687-2690 | the `.erp-subtabs` row — collapses to 1 panel when mappings is hidden |

### 4.2 JS

Delete from [home.js](../../home.js):

| line(approx) | what |
|---|---|
| 15425 | `btn-add-endpoint` listener setup block |
| 15520-15643 | `openEndpointModal` function |
| 15644-15759 | `saveEndpoint` function |
| 15760-... | `deleteEndpoint` function (keep — repurposed for new cards) |
| 15781-15784 | event handlers for the old modal open/close |
| 29125 | secondary reference to `#btn-add-endpoint` |

i18n key removal: `auto-erp-add`, all `ep-*` keys for the old modal,
`ep-list-empty` (the empty state belongs to the new card layout's
empty banner instead).

### 4.3 CSS

Delete from [home.css](../../home.css):

| line(approx) | what |
|---|---|
| 1903-1909 | `.btn-add-endpoint` + sub-selectors |

Plus any classes scoped to `#endpoint-modal` (search-and-destroy when
the modal goes).

### 4.4 What stays untouched

- `erp_push.py` — `push_webhook` is the fallback for non-MRERP /
  non-Xero adapters; keep
- `app.py` `/api/erp/endpoints` CRUD routes — reused with new config
  shape
- `erp_today_stats` IIFE — content moves into cards but logic stays
- Push-log batch bar + filter chips — UX promoted to sidebar, code
  largely unchanged
- 4-language i18n dict block — only ADD new keys; never reorder
  existing keys (CLAUDE.md "i18n 字典顺序" 工程备注)

---

## 5 · Implementation order (when greenlit)

Suggested cuts so each phase is independently shippable:

| phase | scope | risk |
|---|---|---|
| C-1 (½ d) | Backend `POST /api/erp/endpoints/:id/test-connection` route + wire MRERPAdapter.login/select_company | low — adapter is already proven |
| C-2 (1 d) | New ERP card row component + render existing Xero/MR.ERP rows; legacy endpoints list co-exists in a "高级" collapsible | low — purely additive |
| C-3 (1 d) | 3-step wizard modal — new file `static/erp-connect-wizard.html` injected via JS so it's separable from `home.html` (TECH_DEBT pattern) | medium — touches form save flow |
| C-4 (½ d) | Sidebar push-log tab promotion + move today-stats into cards | low |
| C-5 (½ d) | Conditional 字段映射 tab hide (only when adapter list is all-MR.ERP) | low |
| C-6 (1 d) | Delete legacy endpoint modal HTML/JS/CSS + i18n keys; release notes 4 lang | medium — risk of breaking the Xero flow which still uses some shared selectors |
| C-7 (½ d) | Mobile pass — verify cards stack, modal full-screen, wizard usable in ≤800px viewport | medium |

**Total**: ~5 days. Order: C-1 → C-2 → C-3 → C-4 → C-5 → C-6 → C-7.
Each lands as its own commit/version bump.

Gate before C-6 (legacy deletion): Zihao confirms no tenant still
relies on a Webhook endpoint they configured pre-MR.ERP. If any exist,
keep them in a "其他 ERP" advanced section instead of deleting outright.

---

## 6 · Open questions for Zihao

1. **Webhook coexistence** · Some tenants might already have Webhook
   endpoints set up for custom in-house ERPs. Plan says delete the
   "+ 新增端点" button. Do we keep an "高级 → 添加 Webhook" escape
   hatch, or hard-deprecate? Recommendation: hard-deprecate. If any
   tenant complains, restore via per-tenant flag.

2. **`config.system_url` editable?** · Today the URL is fixed at
   `https://www.mrerp4sme.com`. Tenants with self-hosted MR.ERP
   instances need to override. Recommendation: show the field but
   disabled by default; require admin role to unlock.

3. **`master_data_auto_create` toggle visibility** · The auto-create
   path is currently blocked by tenant master-data validation (see
   the customer-sync code's known-limitation comment). Show the toggle
   greyed out with "等 Zihao 选定主数据策略" tooltip, or hide
   entirely? Recommendation: hide for v1; surface as `?advanced=1`
   query param for testing.

4. **Push log retention** · Logs are unlimited today. With the
   sidebar tab promoting visibility, do we trim to N days? Default
   recommendation: keep 90 days, archive older to S3 on a daily cron
   (out of scope for this redesign).

5. **Per-card "test connection" cache TTL** · Auto-testing every card
   on page load is expensive (each is a Playwright login ~5s). Cache
   for 10s? 60s? 5min? Recommendation: 60s; users explicitly clicking
   "重新测试" bypass the cache.

6. **First-time user empty state copy** · Need help wording the
   onboarding banner so it's punchy in all 4 languages. Recommendation:
   skip until the rest of the wizard is implemented; finalize during
   C-2.

---

## 7 · Out of scope

- Backend schema changes beyond `config` shape — handled by
  P1-B Stage 2 implementation, not this UI redesign.
- "Why is this push failing?" diagnostics — covered by the friendly-
  message catalog + raw-text fold-out; no new feature.
- Push retry/backoff configuration UI — keep server-side defaults
  (1s/5s/30s); admins who want overrides can edit `erp_endpoints.config.retry_*`
  via the existing JSON edit field.
- Xero-specific UI updates — Xero's flow still relies on OAuth (well-
  established pattern); only the conditional-hide of the 字段映射 tab
  is changed for Xero.
- FlowAccount adapter — still "即将上线"; card shows the tag,
  click is no-op until shipped.

---

## 8 · Approval gate

This document is **design-only**. No HTML / JS / CSS / Python is
touched until Zihao:

1. Confirms the 3-step wizard layout (or proposes changes)
2. Approves the delete list (especially the legacy endpoint modal)
3. Confirms the 6 open questions in §6
4. Greenlights the C-1..C-7 phasing in §5

When approved, each phase commits independently and Zihao re-verifies
after every visible UI change before the next phase starts.
