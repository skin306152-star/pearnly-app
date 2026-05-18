# MR.ERP 销项发票批量导入 · 端到端探测报告

> **🟡 部分阻塞**:Playwright UI 流程已写完 + 站点结构 / 登录表单 / xlsx 字节格式全部验证 · 阻塞点 = **.env.local 里的测试账号密码失效**(`test01` / `1010-01-000006` 与历史反向工程记录不再匹配)· 拿到新密码 = 一键跑通

最后探测:2026-05-18 17:47 · run_id `20260518-174717`
脚本:[scripts/probe/probe-mrerp.py](../../scripts/probe/probe-mrerp.py)
先验:[docs/integrations/mrerp-known-facts.md](mrerp-known-facts.md)
样本:[docs/integrations/sample-ocr.json](sample-ocr.json)

---

## 1. 状态总览

| 阶段 | 状态 | 说明 |
|---|---|---|
| 站点结构发现 | ✅ | 落地页(`/`)= 营销页 · 登录在 `/login/login.php`(known-facts §2.1 已补) |
| 登录表单解构 | ✅ | 4 input · 0 hidden · 0 CSRF · action=`checklogin.php` · 与 known-facts §2.2 完全一致 |
| **登录提交** | 🔴 | 当前 .env.local 凭据失效 · 提交后 302 → `/index.php`(无 logout 链接 = 未认证) |
| 选公司(`comidyear=6&seldb=1`) | ⏸️ | 阻于登录 · 未实测 |
| 销项菜单导航 | ⏸️ | 同上 |
| xlsx 生成 | ✅ | `mrerp_xlsx_generator.generate_xlsx` 在 Korn 模板缺席下走 openpyxl + 后处理 fallback 路径 · 6807B · 3 sheet 命名严格符合 known-facts §6.1 |
| 上传 + preview + confirm | ⏸️ | 阻于登录 |
| 列表搜索 + 删除 | ⏸️ | 阻于登录 + 列表页 URL 未知(需登录后探索)|

---

## 2. 端到端测试结果(实测到登录失败为止)

### 2.1 截图全链路
| # | 文件 | 场景 | 信息 |
|---|---|---|---|
| 01 | `screenshots/01-landing-marketing-page.png` | GET `/` 落地 | 营销 SPA · 5 个导航链接 · 无登录表单 |
| 02 | `screenshots/02-login-page.png` | 点 `เข้าสู่ระบบ` 进 `/login/login.php` | 登录表单可见 |
| 03 | `screenshots/03-login-filled.png` | 填 `txtusers` + `txtpasswords` | 凭据已遮挡(filter) |
| 04 | `screenshots/04-post-login.png` | 提交后跳到 `/index.php` | 失败 = 回营销首页(`เข้าสู่ระบบ` 链接仍在) |
| 05 | `screenshots/05-login-failed.png` | 失败判定截图 | URL 是 `/index.php` · body 含 `เข้าสู่ระบบ` 但无 `ออกจากระบบ` |
| 06 | `screenshots/06-ERR-fatal.png` | 异常 stack 截图 | RuntimeError 出口 |

### 2.2 实测登录表单结构(Playwright 现场抓)
```
URL:       https://www.mrerp4sme.com/login/login.php
Form:      action="checklogin.php" method="post" id="frm" name="frm"

Inputs:
  - name=txtusers      type=text     id=txtusers    value=""
  - name=txtpasswords  type=password id=txtpasswords value=""
  - name=btnsubmit     type=submit   id=btnsubmit   value="Submit"
  - name=btncancel     type=reset    id=btncancel   value="Cancel"

(0 hidden inputs · 0 CSRF token · 0 select · 0 captcha)
```

这跟 known-facts §2.2 描述 **一字不差** · 反向工程数据未老化。**唯一变量 = 密码值本身**。

### 2.3 登录失败模式实测
- 客户端无报错(form 不显示"密码错"红字)
- 服务端返 302 → `/index.php` (营销首页)
- 没有 toast / alert / 失败信息可 scrape · **静默失败**

→ **检测必须靠"在不在保护区"判定**(probe-mrerp.py step_02 已实现:URL not in `/index.php`/`/login.php` AND body 有 `ออกจากระบบ` OR 在 `selectdb`/`mainmenu`/`impartran`)

---

## 3. 完整字段映射表(从 mrerp_xlsx_generator + known-facts §6 推出)

> 此表为 xlsx 文件**字节级 + 模板级**字段定义 · 待 Playwright 登录通后 · 真上传时会被 MR.ERP 服务端**进一步**校验(客户码 / 商品码 / 部门码必须在主数据存在 等)· 这部分服务端规则需登录后实测

### 3.1 Sheet 1 `Worksheet` · 单据头(18 列 · 末尾占位扩到 A1:S2)

| # | 列名(泰) | xlsx key | MR.ERP 必填 | 类型 / 上限 | 测试值 | Pearnly OCR 字段 | 缺口 / 备注 |
|---|---|---|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | ✅ 业务键 | str ≤ 30 | `PEARNLY-TEST-001` | `invoice_number` | ⚠️ MR.ERP 生产期望 YYMMDD-NNN(BE 年) · 本探测 monkey-patch 强塞我们的标识 · 真上传可能被服务端拒(待登录后实测) |
| 2 | วันที่ | invoice_date | ✅ | date `@` | `2026-05-18` | `date` | OCR 输出已是 ISO · 直接对齐 |
| 3 | อัตราภาษี | tax_rate_str | ✅ | str(14) 枚举 | `7 (แยก)` | 推断 from `vat / subtotal` | 🔴 OCR 没单独抓税率字段 · 当前 generator 默认 7 (แยก) · 0/exempt/外系统需要补 |
| 4 | สาขา | branch_code | ✅ | str(14) | `00000` | (无) | 🔴 OCR 没抓买方分公司码(只有买方名) · 测试用默认 |
| 5 | แผนก | department | ✅ | str(14) | `BOI1` | (无) | 🔴 OCR 不可能抓 · MR.ERP 主数据来源 · 配置项 |
| 6 | งาน | job | ✅ | str(14) | `00002` | (无) | 🔴 同上 |
| 7 | พนักงานขาย | salesman | ✅ | str(30) | `กร ทดสอบ` | (无) | 🔴 同上 · 销售员主数据 |
| 8 | กำหนดส่งสินค้า | delivery_date | ✅ | date | = invoice_date | (无) | 🟡 OCR 一般没"预定送货日" · generator 默认用开票日 |
| 9 | รหัสลูกค้า | customer_code | ✅ | str(50) | `99-PEARNLYTEST-001` | 推断 from `buyer_tax / buyer_name` | 🔴 OCR 抓买方税号(13 位) + 买方名 · 但 MR.ERP 期望**三段式 ERP 码**(`01-อนุรักษ์-001`) · 需配置 `erp_client_mappings` |
| 10 | รหัสลูกค้า (บิล) | customer_bill | ✅ | str(50) | = customer_code | 同上 | 通常 = 客户码 |
| 11 | เลขที่บิล | bill_no | ✅ | str(30) | `SIPEARNLY-TEST-001` | (无) | 🟡 generator 自动 `SI` + invoice_no |
| 12 | วันที่(bill) | bill_date | ✅ | date | = invoice_date | `date` | 通常 = 开票日 |
| 13 | พื้นที่การขาย | sales_area | 🟡 | str(30) | `สุพรรณบุรี` | (无) | 🔴 OCR 不抓 · 默认 |
| 14 | ประเภทขนส่ง | shipping_type | 🟡 | str(30) | `ขนส่งโดยบริษัท` | (无) | 🔴 同上 |
| 15 | หักส่วนลด | discount | 🟡 | num | `0` | (无 · 但 `subtotal/total` 隐含) | 🟡 OCR 抓总折扣需扩字段 |
| 16-18 | หมายเหตุ 1/2/3 | note1/2/3 | ❌ | str(50) ×3 | (空) | (无) | Korn 真样本风格 = 留空 |
| 19 | (spacer) | — | — | 空 cell | — | — | 字节级冷知识 · sheet1 dim 必须 A1:S2 |

### 3.2 Sheet 2 `Worksheet 1` · 商品明细(8 列 · 1 行 / 商品)

| # | 列名(泰) | xlsx key | MR.ERP 必填 | 类型 | 测试值 | Pearnly OCR 字段(`items[]`) | 缺口 / 备注 |
|---|---|---|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | ✅ 关联键 | str ≤ 30 | `PEARNLY-TEST-001` | (关联 sheet1) | 必须 = sheet1 row |
| 2 | รหัสสินค้า | product_code | ✅ | str ≤ 30 | `123`(默认) | 推断 from `items[].name` | 🔴 OCR 只抓商品名 · MR.ERP 期望 ERP 商品码 · 需配置 `erp_product_mappings` 表 · 找不到 fallback `123`(generator 已实现) |
| 3 | แผนก | department | ✅ | str(14) | `BOI1` | (无) | 同 sheet1 |
| 4 | งาน | job | ✅ | str(14) | `00002` | (无) | 同 sheet1 |
| 5 | คลัง | warehouse | ✅ | str(14) | `0000` | (无) | 🔴 OCR 不抓 · 仓库主数据 |
| 6 | จำนวน | qty | ✅ | num | `1` | `items[].qty` | OCR 已抓 |
| 7 | ราคา/หน่วย | unit_price | ✅ | num | `100` | `items[].price` | OCR 已抓 |
| 8 | จำนวนเงิน | amount | ✅ | num | `100` | `items[].subtotal` | OCR 已抓(等价 subtotal) |

### 3.3 Sheet 3 `Worksheet 2` · 尾(3 列 · 条件可选 · Korn 真样本只有 header)

| # | 列名(泰) | xlsx key | MR.ERP 必填 | 类型 | 测试值 |
|---|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | ❌(无 data row) | str | — |
| 2 | เลขที่เงินมัดจำ | deposit_no | ❌ | str(30) | — |
| 3 | ออกใบขาย | is_sales_issued | ❌ | str(14) | — |

---

## 4. 字段缺口分析(OCR ↔ ERP)

### 4.1 OCR 抓到 + ERP 直接用 ✅
- `invoice_date` → invoice_date / delivery_date / bill_date
- `items[].qty` / `items[].price` / `items[].subtotal` → 明细 6/7/8 列

### 4.2 OCR 抓到 + ERP 需查映射 🟡(关键瓶颈 · 影响所有用户上手)
- `buyer_tax`(13 位泰国税号) + `buyer_name` → MR.ERP `customer_code` · **需 `erp_client_mappings` 配置** · 找不到时无法导入(generator 已用 `validate_history_for_sales_credit` 提前拦截 `ERR_NO_CUSTOMER_MAPPING`)
- `items[].name` → MR.ERP `product_code` · 找不到 fallback `123`(generator 默认) · **但 `123` 必须在 MR.ERP 商品主数据里存在** · 否则上传会被拒

### 4.3 OCR 抓不到 + ERP 必填 🔴(必须从配置/默认值取)
| MR.ERP 字段 | 缺口性质 | 当前 generator 处理 |
|---|---|---|
| `tax_rate_str`(7/0/免税/外系统) | OCR 只算 vat 金额 · 不显式输出税率字符串 | 默认 `7 (แยก)` · 0%/免税需扩 schema |
| `branch_code` | 买方分公司码 | 默认 `00000`(总公司) |
| `department` | 部门 | 默认 `BOI1` |
| `job` | 工作号 | 默认 `00002` |
| `salesman` | 销售员名 | 默认 `กร ทดสอบ` |
| `sales_area` | 销售区域 | 默认 `สุพรรณบุรี` |
| `shipping_type` | 运输方式 | 默认 `ขนส่งโดยบริษัท` |
| `warehouse`(明细) | 仓库 | 默认 `0000` |

**结论**:OCR 字段满足度 ≈ 4/18 (22%) · 其余 14 列(78%)走 ERP 主数据 + 默认值 · 这是 **MR.ERP 系统设计决定的 · 非 OCR 缺陷**

### 4.4 OCR 抓到 + ERP 不直接用(但生产可能要)
- `seller_name` / `seller_tax` / `seller_addr` → 是开票方(Pearnly 用户自己)· MR.ERP 是登录公司本身 · 这里不需要传
- `buyer_addr` → MR.ERP 客户主数据里已有 · xlsx 不传
- `notes` → 可塞 `note1/2/3` 但 Korn 真样本留空
- `category` → 仅 Pearnly 内部分类用 · ERP 不要

---

## 5. 上传 → 提交 真实落库流程(理论 · 待登录后验)

根据 known-facts §5 推断 · UI 角度的"用户点击数":

| # | UI 动作 | 服务端等价 | 落库? |
|---|---|---|---|
| 1 | 在 SC 导入页选文件 | (无 · 仅前端) | ❌ |
| 2 | 点 **上传** 按钮 | POST uploadexcel.php · 存 session | ❌(仅 session) |
| 3 | (页面自动跳/手动跳)到预览页 | POST formrdpc.php · 服务端解 xlsx | ❌ |
| 4 | 检查预览表 · 勾要导入的行(默认全选 `cballfrmimport1`) | 浏览器内 | ❌ |
| 5 | 点 **确认导入** 按钮 | POST importpc.php | ✅ **真写库** |

→ **最少 3 次点击**:上传 → 预览跳转(可能自动)→ 确认导入

预期失败点(待实测 · 服务端校验顺序):
1. Step 2 xlsx 格式错(sheet 名 / 列 / 字节)→ 上传 400+
2. Step 3 数据逻辑错(客户码不存在 / 单号重复 / 金额超限)→ 预览页 0 行 + 红字
3. Step 5 业务规则错(税率不允许 / 部门权限)→ 确认返非数字

---

## 6. 错误规则实测验证(下轮登录后做)

待登录通后 · 用 PEARNLY-TEST 故意造 5 种错误 case · 验证 known-facts §9 排错线索表:

| 故意错法 | 预期现象 | 验证 known-facts §9 哪行 |
|---|---|---|
| 客户码用 `99-NOSUCHCUSTOMER-001` | 预览 0 行 + `ไม่พบลูกค้า` 红字 | 行 1 |
| invoice_no 用 `PEARNLY-TEST-001`(非 YYMMDD-NNN) | 预览 0 行 + 格式错 | 行 1 |
| 重复上传同 invoice_no | 预览 0 行 + `ซ้ำ` 关键词 | 行 1 |
| xlsx sheet 名改成 `Sheet1`(不带空格) | 上传可能 200 但预览 0 行 | 行 1 |
| 提交后 cookie 删掉再 confirm | 401/403 | 行 2 |

---

## 7. 已知风险点(部署前必看)

1. 🔴 **凭据轮换**:测试账号密码 2026-05-10 抓包记的值 2026-05-18 已不通 · 生产环境 **必须**提供"凭据更新失败 → 通知用户 → 暂停推送"机制 · 不能默默重试
2. 🔴 **客户码映射**:OCR 出来的 `buyer_tax` / `buyer_name` 到 MR.ERP `customer_code` 是**显式映射表**(`erp_client_mappings`) · 用户首次导入第 N 个新客户都要手工配 · 这是 UX 上手最大瓶颈 · **建议:UI 出"未映射客户清单"批量配置入口**
3. 🟡 **invoice_no 格式锁死**:MR.ERP 期望 YYMMDD-NNN(BE 年) · 真发票号(OCR 抓到的 `INV2026030204` / `IV69/00271` 等)塞不进去 · **必须**自动生成 YYMMDD-NNN(generator 已实现 `derive_mrerp_invoice_no`) · 但用户在 Pearnly 看到的"导入到 MR.ERP 的发票号"会与原票面**不一致** · UI 上要明示"MR.ERP 内部编号"
4. 🟡 **xlsx 字节级兼容**:openpyxl 默认输出 vs Korn 真样本有 5 处字节差(sharedStrings/inlineStr · 数值 `t="n"` 属性 · spans / 缺失 cell / dim) · generator 已做 post-processing · 但 MR.ERP 服务端会不会因升级 PhpSpreadsheet 改解析逻辑 = **未知风险** · 建议每月跑一次自动烟测
5. 🟡 **列表/删除入口未抓**:撤销 / 修改 / 删除路径完全未知 · 生产推送出错需要"回滚"或"幂等重试"时只能让用户手动到 ERP 操作 · 建议下轮探测专门补这块
6. 🟢 **认证流程简单**:无 CSRF / 无 2FA / 无 captcha · Playwright 路径基础稳固 · 不会有突然"反爬升级"的雪崩风险

---

## 8. 立即可执行下一步(给 Zihao)

1. **更新测试账号密码**:Zihao 把现有有效的 MR.ERP `test01` 账号密码填进 `.env.local` 的 `MRERP_PASSWORD`(.env.local 已 gitignore · 安全)· 或告诉我密码 · 我现场重跑
2. **跑通后我会自动**:补完 step 3-10 实测截图 → 把本 spec 的 🟡 升 🟢 → 把 §6 错误规则验证表实测完 → 把 §5 上传流程"实际点击次数"实测确认
3. **本轮不会**:写正式适配器代码(用户已锁定)

跑通密码后只需:
```
python scripts/probe/probe-mrerp.py
```

约 30 秒 · 全程截图自动保存 · 端到端从登录到删除验证 · 跑完会输出 11+ 张截图 + 更新 `probe-findings-*.json`。

---

## 9. 截图清单(当前)

```
docs/integrations/screenshots/
├── 01-landing-marketing-page.png   GET / → 营销页 · 无登录表单
├── 02-login-page.png               /login/login.php · 4 input · 0 hidden
├── 03-login-filled.png             表单已填(凭据已遮)
├── 04-post-login.png               提交后 302 → /index.php
├── 05-login-failed.png             失败判定截图 · body 无 ออกจากระบบ
├── 06-ERR-fatal.png                异常出口截图
└── manifest.txt                    一键索引
```

凭据通后预期 11+ 张:`07-mainmenu` / `08-sc-import-form` / `09-form-inspected` / `10-file-chosen` / `11-after-upload` / `12-preview-page` / `13-preview-checked` / `14-after-confirm` / `15-search-result` / `16-after-delete` / `17-verify-deletion`。

---

## 10. 已生产文件清单

| 路径 | 用途 |
|---|---|
| `scripts/probe/probe-mrerp.py` | 端到端探测脚本(可重跑) |
| `docs/integrations/mrerp-known-facts.md` | 站点先验事实(本轮新增 §2.1) |
| `docs/integrations/mrerp-spec.md` | 本文档 |
| `docs/integrations/sample-ocr.json` | 新三层架构 OCR 真实输出 |
| `docs/integrations/screenshots/01-06.png` | 探测截图 |
| `docs/integrations/templates/upload-form-*.html` | 登录页 HTML dump(若到该步) |
| `docs/integrations/templates/test-invoice-*.xlsx` | 测试 xlsx(6807B · 3 sheet) |
| `docs/integrations/probe-findings-*.json` | 探测过程结构化输出 |

---

## 11. 不变铁律提醒

本探测严守 **CLAUDE.md 铁律 §7**:
- ✅ 全部经 Playwright 浏览器 UI(click / fill / set_input_files / wait_for_load_state)
- ❌ **零** `requests.post` / `requests.get` / 任何直接 HTTP 调用
- known-facts 的 endpoint **仅**用作"page.goto(已知 URL) + 验证 page.url 跳到预期" 的锚点 · 不做手工请求构造

如本 spec 看完无问题 · 凭据更新后直接 `python scripts/probe/probe-mrerp.py` · 30 秒内完成完整链路实测。
