# 集成测试 · tests/integration

窗口 C 维护(REFACTOR-WC)· 只加测试,不碰业务代码。本目录有两类测试,运行条件不同。

## 两类测试

### 1. 纯函数安全网(无条件跑 · CI 真跑不 skip)

直接调用纯计算函数,不连 DB、不打网络、不烧 Gemini。CI 每次都跑,是真正能拦回归的硬闸。
给窗口 A 拆高敏 OCR/billing/VAT/ERP 热路径当保险:任一不变量被改坏就立刻红。
命名 `test_*_safety_net.py` · 当前 11 文件 / 157 测。

**扣费 + 对账链**(文件 → units → cost → charge → 配对 → 退款 → 充值,全程纯函数闸):

| 文件 | 测数 | 锁什么 |
|---|---|---|
| `test_billing_correctness_safety_net.py` | 23 | PDF 阶梯价跨界 200 / Excel 字符向上取整 / 估价幂等 / usage↔退款冲销 / `_ocr_validate_invoice` 7% VAT 公式 |
| `test_excel_charge_units_safety_net.py` | 14 | `_excel_char_count_estimate` 计费 units:文本按 utf-8 字符数(非字节,防多字节多收 3 倍)+ 文件→units→cost 闭合 |
| `test_topup_contract_safety_net.py` | 10 | 充值金额边界契约:`amount_thb` gt=0/le=500000 + 超管审批 `actual_amount_thb` gt=0 |
| `test_recon_matching_safety_net.py` | 12 | `_build_recon_pairs` 一对一配对:partition 不变量(不重复计入 / 不静默丢)+ 不误配 + 散客/OCR 漏税号分类 |
| `test_recon_primitives_safety_net.py` | 17 | 配对原语:总额求和 / `_eq_amount` 容差 / `normalize_invoice_no`+`normalize_tax_id` / `tax_id_fuzzy_distance` |
| `test_recon_field_override_safety_net.py` | 8 | `ALLOWED_FIELDS` 用户可校正 7 字段白名单(含金额 · 不含派生 total)+ `parse_overrides` JSONB→dict 副本归一 |

**ERP 客户/商品同步**(归一写坏 → 匹配错买方/错商品码 = 红线 · 现有 mrerp 测要真 sandbox + 浏览器,CI skip):

| 文件 | 测数 | 锁什么 |
|---|---|---|
| `test_erp_matching_safety_net.py` | 20 | `_matching` 地基:`normalize_company_name`(去法人后缀)vs `normalize_item_name`(保后缀)/ `levenshtein`+`ratio` / `fuzzy_match` 阈值/平局/跳 None |
| `test_mrerp_customer_parse_safety_net.py` | 15 | `parse_armas_listing`(行/表头/限域/缺码)+ `_norm_tax`(仅 13 位可比)+ `_strip_tags` + `to_dict` 契约 |
| `test_mrerp_product_parse_safety_net.py` | 17 | `parse_stkmas_listing` + `suggest_generic_product_code`(多语种命中 · 名字优先分类)+ `to_dict` 契约 |

**OCR 非图像路径**:

| 文件 | 测数 | 锁什么 |
|---|---|---|
| `test_table_path_safety_net.py` | 16 | `table_path`:CSV→`Layer1Result` 契约(engine / `table_rows` 按表头键 dict / 空与不支持扩展名抛 `ValueError`)+ `_decode_bytes` 多编码(泰文 cp874)|

**跨域 facade / 路由**(防 A 拆 db.py/app.py 时静默丢桥/丢路由):

| 文件 | 测数 | 锁什么 |
|---|---|---|
| `test_dal_facade_completeness_safety_net.py` | 5 | 数据驱动遍历 `dal_reexports._REEXPORTS`(~286 名 / 36 域):每个 re-export 都桥到 `db` 上 + 对象身份一致 + 钱路径名锚定 |

> 另有 `test_core_routes_presence.py`(app 名册守门 · 31 条用户可见 path · 非 `_safety_net` 命名但同属拆分守门)。

### 2. env-gated 真集成(默认 skip · 配齐 env 才跑)

走真 FastAPI app + 真路由 + 真 DB,只 mock 外部(Gemini / LINE / Gmail)。
CI 默认没 DB → 干净 skip(不让 CI 红)。本地 / staging 配齐 env 才真跑。

骨架在 `_helpers.py`:

| 闸 | 条件 | 缺了的行为 |
|---|---|---|
| `require_db()` | `PEARNLY_INTEGRATION_DB=1` + `DATABASE_URL` | SkipTest |
| `require_test_user()` | `PEARNLY_E2E_USER` + `PEARNLY_E2E_PASS` | SkipTest |
| `require_admin_user()` | `PEARNLY_ADMIN_USER` + `PEARNLY_ADMIN_PASS` | SkipTest |
| `get_test_client()` | `app` 可 import(DB 连得上) | SkipTest |

覆盖域:billing / recon / vat_excel / ocr / erp(mrerp 适配器与同步)/ auth / signup / clients / team / archive / importer mapping / 健康与版本契约。

## 跑法

```bash
# 只跑纯函数安全网(无需任何 env · CI 跑的就是这批)
python -m unittest discover -s tests/integration

# 跑真集成(需本地/staging DB + 测试账号)
export PEARNLY_INTEGRATION_DB=1
export DATABASE_URL=postgresql://...
export PEARNLY_E2E_USER=...   PEARNLY_E2E_PASS=...
python -m unittest discover -s tests/integration
```

无 env 时纯函数安全网照常跑、真集成自动 skip,退出码仍为 0。

## 约定

- 纯加测试,不改任何业务代码(铁律 #17/#21/#23/#27)。
- 不假设 CI 有真 DB:真集成一律 env-gated,缺 env clean skip,绝不红 CI。
- 安全网文件命名 `test_*_safety_net.py`,与 env-gated 的 `test_*_integration.py` 区分。
- 单元测试在 `tests/unit/`(窗口 A 维护),端到端在 `tests/e2e/`,视觉回归在 `tests/visual/`。
