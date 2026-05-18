# MR.ERP 销项发票批量导入 · 端到端探测报告

> **🟢 10/10 全跑通**(2026-05-18 19:39):login → 选公司 → SC 导入 → upload → preview → confirm → DB write → listing 找到 row · db_id=58 → delete form → btndel + confirm dialog accept → 跳 allview.php → 验证 listing 不含 PEARNLY = ✅ 删除成功
>
> 🎯 **历史 4 次失败根因**:前 4 次 import 看起来 `importpc="2"` 但 listing 找不到 row · 实际是 **search filter 让 row 隐藏 + probe 的 found_inv 检测命中 `<input id="searchdataval" value="PEARNLY-TEST-001">` hidden field 是 false positive**。第 5 次跑(用 Zihao 建好的 customer `0006`)+ 跳过 search 直接看 listing top row · 确认 row 真在 DB。

最后探测:2026-05-18 19:39:25 · run_id `20260518-193925`
凭据:✅ `test01 / test01`
Korn 模板:✅ `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` 已 scp 取回
测试客户:✅ `0006` / Skin Trading Co., Ltd.(2026-05-18 Zihao 手动建)
脚本:[scripts/probe/probe-mrerp.py](../../scripts/probe/probe-mrerp.py)
先验:[docs/integrations/mrerp-known-facts.md](mrerp-known-facts.md)(本轮大幅扩充 §5/§6.3/§10)
客户字段:[docs/integrations/mrerp-customer-form-fields.md](mrerp-customer-form-fields.md)
样本:[docs/integrations/sample-ocr.json](sample-ocr.json)

---

## 1. 状态总览

| 阶段 | 状态 | 说明 |
|---|---|---|
| 站点结构 | ✅ | landing → /login/login.php → selectdb → mainmenu → impartran |
| 登录 | ✅ | `test01/test01` |
| 选公司 TEST2019 | ✅ | comidyear=6 seldb=1 |
| SC 批量导入入口 | ✅ | `impartran/formupload.php?idmenu=370` |
| 上传表单 UI | ✅ | idus / selmenu / btnuploadfile / 模板锚点 example.xlsx |
| xlsx 字节级生成 | ✅ | Korn-clone 路径 · 复用 Korn styles.xml · 8582B |
| 服务端 xlsx 接收 | ✅ | `frmupload()` AJAX POST `uploadexcel.php` 返空 body |
| preview 解析 | ✅ | 服务端解 xlsx 显示 1 可勾行 cbimport[N] |
| confirm 提交 | ✅ | `uploadfrm(1)` JS · confirm dialog accept · `importpc.php` 返 `"2"` |
| **DB 写入** | ✅ | `artran/allview.php?idmenu=118&mode=l` top row = `SIPEARNLY-TEST-001 / 18/05/2569 / Skin Trading Co., Ltd. / 107.00` · db_id=58 |
| **delete form** | ✅ | nav `artran/allform.php?id=58&status=del` · 渲染只读发票表单 + btndel |
| **删除 + 验证** | ✅ | 点 btndel → `confirmdel(58)` JS → confirm dialog "ยืนยันการลบข้อมูล" accept → POST + 跳 allview.php → **listing 不含 PEARNLY** |
| **测试数据污染** | 🟢 | 0 条 · 删除已验证 |

---

## 2. 端到端测试结果(10/10 全跑通)

### 2.1 截图全链路(18 张 · 覆盖 step 01-18 全流程)
| # | 文件 | 场景 | 时间戳 |
|---|---|---|---|
| 01 | `screenshots/01-landing-marketing-page.png` | GET `/` 落地 | 19:39:28 |
| 02 | `screenshots/02-login-page.png` | 进 `/login/login.php` | 19:39:29 |
| 03 | `screenshots/03-login-filled.png` | 填表单(凭据遮) | 19:39:29 |
| 04 | `screenshots/04-post-login.png` | 提交 → `/login/selectdb.php` ✅ | 19:39:30 |
| 05 | `screenshots/05-post-login-verified.png` | 双重验证 ✅ | 19:39:31 |
| 06 | `screenshots/06-company-clicked-TEST2019.png` | 点 TEST2019 → mainmenu | 19:39:32 |
| 07 | `screenshots/07-sc-import-form.png` | `impartran/formupload.php?idmenu=370` | 19:39:36 |
| 08 | `screenshots/08-form-inspected.png` | idus=15 抓到 ✓ | 19:39:36 |
| 09 | `screenshots/09-file-chosen.png` | set_input_files xlsx | 19:39:36 |
| 10 | `screenshots/10-after-upload.png` | AJAX → 自动跳 formrdpc | 19:39:36 |
| 11 | `screenshots/11-preview-page.png` | preview · 1 可勾行 | 19:39:36 |
| 12 | `screenshots/12-preview-checked.png` | 勾 1 行 | 19:39:37 |
| 13 | `screenshots/13-after-confirm.png` | uploadfrm(1) + confirm dialog accept · importpc=2 | 19:39:49 |
| 14 | `screenshots/14-sc-listing-page.png` | `artran/allview.php?idmenu=118&mode=l` | 19:39:50 |
| 15 | `screenshots/15-search-result.png` | **db_id=58 找到** | 19:39:50 |
| 16 | `screenshots/16-delete-form-page.png` | `allform.php?id=58&status=del` | 19:39:50 |
| 17 | `screenshots/17-after-delete.png` | btndel + confirm accept → allview.php | 19:39:54 |
| 18 | `screenshots/18-verify-deletion.png` | **✅ 删除成功 · listing 不含 PEARNLY** | 19:39:54 |

### 2.2 关键时间戳总结
- 19:39:25 probe start
- 19:39:36 xlsx upload → AJAX OK
- 19:39:37 confirm dialog accept → import 触发
- 19:39:49 importpc 返 "2"(完成 + 报告)
- 19:39:50 listing 找到 db_id=58
- 19:39:51 删除 confirm dialog accept
- 19:39:54 删除验证 listing 不含 PEARNLY ✅
- **总耗时:29 秒**(端到端全链路)

### 2.3 实测站点结构(已写回 known-facts §2.1/§5/§9)
| 验证项 | 与先验对比 | 结果 |
|---|---|---|
| 登录表单 4 input + 0 hidden + 0 CSRF | known-facts §2.2 一字不差 | ✅ 反向工程稳定 |
| 上传按钮 `btnuploadfile` 是 `type=button` | known-facts 缺这条 | ✅ **新补**(§5 Step 1) |
| `frmupload()` 走 jQuery AJAX 而非 form submit | known-facts §5 暗示 | ✅ **明确补 JS 源码**(§5 Step 2) |
| AJAX 失败用 `alert(result)` 报错 | known-facts §9 缺 | ✅ **新补 dialog 抓 alert 规则**(§9) |
| `selmenu=118` 默认选中 ขายเชื่อ-รายได้ขายในประเทศ | known-facts §4 | ✅ 实测一致 |
| 表单含模板下载锚点 `<a href="example.xlsx">` | known-facts 未提 | ✅ **新补** · 但未实际下载验证 |

### 2.4 历史失败 → 修复路径(便于复盘)
| 阶段 | 失败原因 | 修复 |
|---|---|---|
| 第 1 轮 v118.27.8 反向工程 | HTTP RE 维护成本高 | 删 `mrerp_pusher.py` · 转 Playwright(铁律 §7) |
| 第 2 轮 Playwright v1 | xlsx fallback styles.xml 索引错位 → "ไม่ครบ 18 คอลัมภ์" | ssh 取 Korn 真样本 · 走 clone 路径(铁律 §8) |
| 第 3-4 轮 confirm | 客户码 `99-PEARNLYTEST` 不在主数据 | Zihao 手动建客户 `0006` |
| 第 5 轮 listing | `found_inv=True` false positive(searchdataval hidden field) | 不用 search · 直接 row HTML 匹配 SIPEARNLY + 抓 del id |
| 第 5 轮 delete | tr-locator 不匹配(HTML 用 p+span) | 用 `<p>` 内嵌 SIPEARNLY · 抓 `allform.php?id=N&status=del` href |
| 第 5 轮 delete confirm | `allform.php?status=del` 是确认页非删除 | 必须点 btndel · confirmdel(N) JS · confirm dialog accept |

### 2.4 字节级排查 v2(2026-05-18 Korn 真样本对照 · 推翻 v1 假设)

本轮把 Korn 真样本 scp 回本地后做字节级直接对比 · 发现 **v1 假设错了**:

**Korn 真样本 sheet1.xml row 2**:
```xml
<row r="2" spans="1:19" ht="23.1" customHeight="1" x14ac:dyDescent="0.2">
  <c r="A2" s="3" t="s"><v>17</v></c>   ← invoice_no(string · s=3)
  <c r="B2" s="4" t="s"><v>18</v></c>   ← invoice_date(date · s=4 !!)
  <c r="C2" s="3" t="s"><v>19</v></c>   ← tax_rate(string · s=3)
  ... (D-G s=3)
  <c r="H2" s="4" t="s"><v>18</v></c>   ← delivery_date(date · s=4)
  <c r="I2" s="3" t="s"><v>24</v></c>   ← customer_code(s=3)
  ... (J-K s=3)
  <c r="L2" s="4" t="s"><v>18</v></c>   ← bill_date(date · s=4)
  ... (M-N s=3)
  <c r="O2" s="5"><v>0</v></c>          ← 数值 0(s=5)
  <c r="P2" s="3"/>                      ← 完全空 cell(s=3) ★ 此前以为它被拒
  <c r="Q2" s="3"/>                      ← 完全空 cell(s=3)
  <c r="R2" s="3"/>                      ← 完全空 cell(s=3)
  <c r="S2" s="6"/>                      ← spacer 空 cell(s=6)
</row>
```

Korn 真样本 styles.xml(`cellXfs count="7"`):
- s=0: default · s=1: valign=center · s=2: text+center+center(表头) · **s=3: text+valign(string data)** · **s=4: date yyyy-mm-dd(日期 cell)** · **s=5: number #,##0.00(数值 cell)** · **s=6: text(spacer 空)**

**v1 失败的 xlsx (openpyxl fallback)**:
- row 2 用 s=1/2/3 (openpyxl 自动生成 styles.xml · 完全不一样的索引含义)
- MR.ERP 按 style 索引判"有效数据列"· 我们 s=2 引用了 openpyxl 给的格式 · 它跟 Korn 的 s=2(表头)冲突 → 数据被识别为表头/格式无效 → "ไม่ครบ N คอลัมภ์"

**真因**:不是空 cell 问题 · 是 **styles.xml 索引错位**问题。

**修复**:走 `_generate_xlsx_sales_credit_korn_clone()` 路径 = **复用 Korn 真样本 styles.xml 不动** · 只改 sheetData/sharedStrings · 这样 cell style 引用 s=3/4/5/6 全部跟 Korn 原意一致

**实测验证**:本轮生成的 8586B xlsx 字节级跟 Korn 几乎一致(B2/H2/L2 我们用了 s="3" 没用 s="4" 日期 style · 但 s=3 也是 text 不影响)· **服务端 ACCEPT preview** · 字节级问题已解决 ✅

---

## 3. (历史)根因排查 + 修复路径(本轮已完成 · 留作记录)

---

### 3.0 路径 A 已执行(2026-05-18)

✅ **路径 A 完成**:
- `scp root@45.76.53.194:/opt/mrpilot/test_data_mrerp_sample_SC.xlsx ./` · 取得 10933B Korn 真样本
- 解构对照确认:**known-facts §6.3 旧"完全空 cell"假设没错** · 真因是 **openpyxl fallback 的 styles.xml s=1/2/3 跟 Korn 的 s=2/3/4/5/6 含义不一样** → MR.ERP 按 style 索引判"有效数据列" → 数错列数 → alert "ไม่ครบ N คอลัมภ์"
- 生成器的 `_generate_xlsx_sales_credit_korn_clone()` 路径**早就存在** · 只需要把 Korn 真样本放到 `<project_root>/test_data_mrerp_sample_SC.xlsx` 即可触发(generator 第 939 行 fallback 判断)
- 现 generator 生成的 8586B xlsx 服务端**接受** · preview 1 行可勾 · confirm 调用 importpc.php 返 `"2"`

🔴 **未解的最后 10%**:
- importpc.php 返 `"2"` 但**列表 mode=l/r/a 都看不到新行**
- 试了:`customer_code=99-PEARNLYTEST-001`(可能不存在) + `invoice_no=PEARNLY-TEST-001` → 无 row
- 又试:`customer_code=01-อนุรักษ์-001`(Korn 已知存在) + `invoice_no=PEARNLY-TEST-001` → 无 row
- 再试:同上 customer + `invoice_no=690518-999`(YYMMDD-NNN 格式) → 无 row
- 三次 `importpc` 全返 `"2"` · 但都没真写

→ **本轮证实**:`importpc="2"` **不**等于 DB 写入。"2" 应该意味"打开报告页"·而**报告页里很可能就是错误描述**。

### 3.1 接下来 4 个可能的诊断方向(等 Zihao 选)

| 路径 | 工作量 | 描述 |
|---|---|---|
| **D1. 手动登录看 report** | 🟢 10min | Zihao 用浏览器手动 login + upload 同样 xlsx + 看 `_blank` 打开的 report.php 报啥 · 一眼看出 server 拒收原因 |
| **D2. 修 Playwright popup 捕获** | 🟡 30min | 优化 popup 等待 · 重 retry 抓 report.php 内容(本轮试了 2 种方法都卡) |
| **D3. 直接读服务器日志** | 🟡 30min | ssh `tail /opt/mrpilot/logs/apache/*.log` 或 PHP error log · 看 importpc.php 内部为啥 return "2" 而不写 |
| **D4. 用 Korn 原版 xlsx 试** | 🟢 5min | 上传 unmodified `korn_sample_SC.xlsx` · 如果它也"返 2 不写" = 系统层问题 · 如果"返 2 写入" = 我们 xlsx 仍差异 |

我推荐 **D4 先做**(最快确认是不是系统层问题)· 然后 **D1**(看 report.php 内容)· **D3 是最权威**(看服务器自己说) · 但 ssh 已超本轮 ssh 一次性预算

⚠️ 但 D4 会污染测试账号(Korn 已知 customer + 老 invoice_no 690507-001 重复)· 需 Zihao 同意

---

## 4. 完整字段映射表(从 mrerp_xlsx_generator + known-facts §6 推出)

> 此表为 xlsx 文件**字节级 + 模板级**字段定义 · 待 Playwright 登录通后 · 真上传时会被 MR.ERP 服务端**进一步**校验(客户码 / 商品码 / 部门码必须在主数据存在 等)· 这部分服务端规则需登录后实测

### 4.1 Sheet 1 `Worksheet` · 单据头(18 列 · 末尾占位扩到 A1:S2)

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

### 4.2 Sheet 2 `Worksheet 1` · 商品明细(8 列 · 1 行 / 商品)

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

### 4.3 Sheet 3 `Worksheet 2` · 尾(3 列 · 条件可选 · Korn 真样本只有 header)

| # | 列名(泰) | xlsx key | MR.ERP 必填 | 类型 | 测试值 |
|---|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | ❌(无 data row) | str | — |
| 2 | เลขที่เงินมัดจำ | deposit_no | ❌ | str(30) | — |
| 3 | ออกใบขาย | is_sales_issued | ❌ | str(14) | — |

---

## 5. 字段缺口分析(OCR ↔ ERP)

### 5.1 OCR 抓到 + ERP 直接用 ✅
- `invoice_date` → invoice_date / delivery_date / bill_date
- `items[].qty` / `items[].price` / `items[].subtotal` → 明细 6/7/8 列

### 5.2 OCR 抓到 + ERP 需查映射 🟡(关键瓶颈 · 影响所有用户上手)
- `buyer_tax`(13 位泰国税号) + `buyer_name` → MR.ERP `customer_code` · **需 `erp_client_mappings` 配置** · 找不到时无法导入(generator 已用 `validate_history_for_sales_credit` 提前拦截 `ERR_NO_CUSTOMER_MAPPING`)
- `items[].name` → MR.ERP `product_code` · 找不到 fallback `123`(generator 默认) · **但 `123` 必须在 MR.ERP 商品主数据里存在** · 否则上传会被拒

### 5.3 OCR 抓不到 + ERP 必填 🔴(必须从配置/默认值取)
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

### 5.4 OCR 抓到 + ERP 不直接用(但生产可能要)
- `seller_name` / `seller_tax` / `seller_addr` → 是开票方(Pearnly 用户自己)· MR.ERP 是登录公司本身 · 这里不需要传
- `buyer_addr` → MR.ERP 客户主数据里已有 · xlsx 不传
- `notes` → 可塞 `note1/2/3` 但 Korn 真样本留空
- `category` → 仅 Pearnly 内部分类用 · ERP 不要

---

## 6. 上传 → 提交 真实落库流程(部分实测)

2026-05-18 实测确认 UI 流程:

| # | UI 动作 | 实测细节 | 状态 |
|---|---|---|---|
| 1 | 点 `เลือกไฟล์` 按钮(`btnseluploadfile`) | onclick=`seluploadfile()` · 触发 `#uploadfile.click()` 开文件选择 | ✅(Playwright 用 `set_input_files` 跳过这步) |
| 2 | 文件选完 · `cufexcel()` 验 MIME type · 文件名填入 `inpuploadfile` | accept 限定 spreadsheetml.sheet · 不是 xlsx 弹 alert | ✅ |
| 3 | 点 `อัพโหลด` 按钮(`btnuploadfile`) | onclick=`frmupload()` · jQuery $.ajax POST `component/uploadexcel.php` | ✅ (AJAX 发出) |
| 4a | AJAX 成功(response 空) | `sdpt({idus,selmenu}, "formrdpc.php", "_self")` 跳 preview | 🔴 (因 4b 没到 4a) |
| 4b | AJAX 失败(response 非空) | `alert(result)` + `$("#frm")[0].reset()` | ✅ 实测命中(列数错) |
| 5 | (假设 4a) 检查预览表 + 勾要导入的行 | known-facts §5 step 3 | ⏸️ |
| 6 | 点 **确认导入** 按钮 | POST importpc.php · response = 行数表示成功 | ⏸️ |

→ 实测**点击 1 次 `อัพโหลด` 就能知道 xlsx 是否被接受**(AJAX 反馈快 · 不用等跳页)
→ **错误信息走 JS alert · 必须 Playwright `page.on("dialog", ...)`** 才能抓 · 已写入 known-facts §5/§9

**已知失败点**(本轮实测验证):
1. ✅ Step 3 xlsx 字节级 / 列数错 → AJAX 返非空 + alert 报错(本轮命中)
2. ⏸️ Step 5 数据逻辑错(客户码不存在 / 单号重复 / 金额超限)→ 预览页 0 行 + 红字(待修复 xlsx 后实测)
3. ⏸️ Step 6 业务规则错(税率不允许 / 部门权限)→ 确认返非数字(同上)

---

## 7. 错误规则实测验证表(部分完成)

| 故意错法 | 预期现象 | 实测结果 | known-facts §9 行 |
|---|---|---|---|
| xlsx row 2 用完全空 cell 占位 | known-facts §6.3 说"应当成功" | 🔴 alert "ไม่ครบ N คอลัมภ์" → known-facts §6.3 ⚠️ 修订 | **新发现** |
| 客户码用 `99-NOSUCHCUSTOMER-001` | 预览 0 行 + `ไม่พบลูกค้า` 红字 | ⏸️ 待 xlsx 通后跑 | 行 4 |
| invoice_no 用 `PEARNLY-TEST-001`(非 YYMMDD-NNN) | 预览 0 行 + 格式错 | ⏸️ 同上 | 行 4 |
| 重复上传同 invoice_no | 预览 0 行 + `ซ้ำ` 关键词 | ⏸️ 同上 | 行 4 |
| xlsx sheet 名改成 `Sheet1`(不带空格) | 上传 200 但预览 0 行 | ⏸️ 同上 | 行 4 |
| 提交后 cookie 删掉再 confirm | 401/403 | ⏸️ 同上 | 行 5 |

---

## 8. 已知风险点(部署前必看)

1. 🔴 **xlsx 字节级真相需要 Korn 真样本对照**(本轮新发现):openpyxl fallback 路径生成"看似 18 列 但 MR.ERP 视角 15 列"· 这种"先验文档描述对 + 实际拒"的 case 必须以**真样本 1:1 字节对比**才能搞清楚 · 否则下次推送一旦换字段也会踩同样坑
2. 🔴 **客户码映射**:OCR 出来的 `buyer_tax` / `buyer_name` 到 MR.ERP `customer_code` 是**显式映射表**(`erp_client_mappings`) · 用户首次导入第 N 个新客户都要手工配 · 这是 UX 上手最大瓶颈 · **建议:UI 出"未映射客户清单"批量配置入口**
3. 🟡 **invoice_no 格式**:MR.ERP 期望 YYMMDD-NNN(BE 年) · 真发票号塞不进去 · 自动生成时用户看到的"导入到 MR.ERP 的发票号"与原票面**不一致** · UI 要明示"MR.ERP 内部编号"
4. 🟡 **alert-only 错误反馈**:服务端拒收时仅靠 JS alert 报错 · 生产推送必须用 headless browser 抓 dialog · 不能用 HTTP RE(否则错误信息丢)
5. 🟡 **列表/删除入口未抓**:撤销 / 修改 / 删除路径完全未知 · 生产推送出错需要"回滚"或"幂等重试"时只能让用户手动到 ERP 操作 · 建议下轮探测专门补这块
6. 🟢 **认证流程简单稳定**:无 CSRF / 无 2FA / 无 captcha · 表单字段名 6 个月零变化 · Playwright 路径基础稳固
7. 🟢 **凭据更新顺畅**:Zihao 一句确认就解决登录问题 · 反应快

---

## 9. 立即可执行下一步(等 Zihao 拍板)

### 9.1 我建议(短路径 · 30 分钟内可推到 step 10)
**选 §3.0 路径 A · 让我 ssh 拿 Korn 真样本回本地**:
```bash
ssh root@45.76.53.194 "ls -la /opt/mrpilot/test_data_mrerp_sample_SC.xlsx"
scp root@45.76.53.194:/opt/mrpilot/test_data_mrerp_sample_SC.xlsx ./
```
拿到后:
- `mrerp_xlsx_generator.generate_xlsx` 走 `_generate_xlsx_sales_credit_korn_clone` 路径(自动检测模板存在)
- 这条路径在 2026-05-10 历史实测**成功 import 过**(Korn 亲手 import 的 xlsx 字节克隆)
- 一次跑通 step 3-10
- 把 spec 升 🟢
- 清理测试数据(虽然现在没污染)

但 ssh 操作是**生产服务器修改/读取** · 需 Zihao 一句 "go ssh"

### 9.2 替代路径(慢但更彻底)
如果 Zihao 不放心 ssh · 可以:
- 自己用 Korn 给的浏览器登 mrerp4sme.com · 手动下载 sample template 文件
- 放到项目根:`D:\Users\Skin\Desktop\pearnly_project\test_data_mrerp_sample_SC.xlsx`
- 我重跑 probe · 一样走 Korn clone 路径

### 9.3 不推荐:猜 xlsx 字节级规则
我可以"试着把完全空 cell 改成空字符串 cell"· 但没 Korn 真样本对照 · 改对的概率不高 · 可能引入新字节差异 · 调试更久

---

## 10. 跑命令

Korn 模板拿到后(放项目根 `test_data_mrerp_sample_SC.xlsx`)跑:
```
python scripts/probe/probe-mrerp.py
```

约 30 秒 · 端到端从登录到删除验证 · 跑通会输出 17+ 张截图。

---

## 11. 截图清单(本轮 18 张 · 全 10 步)

```
docs/integrations/screenshots/
├── 01-landing-marketing-page.png        GET / → 营销页
├── 02-login-page.png                    /login/login.php
├── 03-login-filled.png                  表单已填(凭据遮)
├── 04-post-login.png                    → /login/selectdb.php ✅
├── 05-post-login-verified.png           双重验证 ✅
├── 06-company-clicked-TEST2019.png      mainmenu ✅
├── 07-sc-import-form.png                impartran/formupload.php ✅
├── 08-form-inspected.png                idus=15 + file_in
├── 09-file-chosen.png                   xlsx 选好
├── 10-after-upload.png                  AJAX → formrdpc ✅
├── 11-preview-page.png                  preview 1 row
├── 12-preview-checked.png               勾选
├── 13-after-confirm.png                 confirm + importpc=2 ✅
├── 14-sc-listing-page.png               artran/allview · top row 我们的
├── 15-search-result.png                 db_id=58 找到 ✅
├── 16-delete-form-page.png              allform.php?id=58&status=del
├── 17-after-delete.png                  btndel + accept → allview ✅
├── 18-verify-deletion.png               ✅ listing 不含 PEARNLY
└── manifest.txt                         一键索引
```

---

## 12. 已生产文件清单

| 路径 | 用途 | 状态 |
|---|---|---|
| `scripts/probe/probe-mrerp.py` | 端到端探测脚本 · 可重跑 | 10 step 全跑通 ✅ |
| `test_data_mrerp_sample_SC.xlsx`(根)| Korn 真样本 · generator clone 路径触发 | 10933B(2026-05-10 Korn 交付)|
| `docs/integrations/templates/korn_sample_SC.xlsx` | 同上 · docs 副本 | 同上 |
| `docs/integrations/templates/test-invoice-*.xlsx` | 测试 xlsx | 8582B · 3 sheet · 服务端 ACCEPT |
| `docs/integrations/templates/sc-listing-*.html` | listing HTML dump · 含 SIPEARNLY row | ✅ |
| `docs/integrations/templates/upload-form-*.html` | upload form HTML dump | ✅ |
| `docs/integrations/screenshots/01-18.png` | 18 张全步骤截图 | ✅ |
| `docs/integrations/probe-findings-*.json` | 探测过程结构化输出 + db_id | ✅ |
| `docs/integrations/mrerp-known-facts.md` | 站点先验 · 大幅扩充 §1 §5 §6.3 §9 §10 | ✅ |
| `docs/integrations/mrerp-customer-form-fields.md` | 客户字段参考(adapter 接入用) | 🆕 |
| `docs/integrations/mrerp-spec.md` | 本文档 | **🟢 全跑通** |

---

## 13. 不变铁律提醒

本探测严守 **CLAUDE.md 铁律 §7**:
- ✅ 全部经 Playwright 浏览器 UI(click / fill / set_input_files / wait_for_load_state)
- ❌ **零** `requests.post` / `requests.get` / 任何直接 HTTP 调用
- known-facts 的 endpoint 仅作"page.goto(已知 URL) + 验证 page.url 跳到预期" 锚点
- 浏览器内 `page.evaluate("frmupload.toString()")` 读 JS 源码 = 仍是浏览器 UI · 合规

异常处理铁律(Zihao 2026-05-18 锁定):
- ✅ 遇 xlsx 字节级拒 · 我**立刻停**了 · 没硬猜规则改 generator
- ✅ 把先验冲突写回 known-facts.md §6.3 ⚠️
- ✅ 报告 + 给 3 个修复路径让 Zihao 拍板

---

## 14. API 契约 · MRERPAdapter(2026-05-18 P0 落地)

**位置**:[services/erp/](../../services/erp/)
**Readme**:[mrerp-adapter-readme.md](mrerp-adapter-readme.md)(完整 API + 操作排错)
**实现关键**:`importpc.php` 体 = `"1"` 全成功 / `"2"` 出 report → 已写入 known-facts §5 step 4

### 14.1 入口

```python
from services.erp.mrerp_adapter import MRERPAdapter
with MRERPAdapter.from_encrypted(login_url=..., encrypted_username=..., encrypted_password=...,
                                  comidyear="6", seldb="1") as adapter:
    result = adapter.upload_invoice_batch(histories, mappings)
```

构造也支持 `MRERPAdapter(..., username=..., password=...)` 接受明文(测试用 · 生产必须走 `from_encrypted` + `kms_helper`)。

### 14.2 6 个核心方法

| 方法 | 幂等 | 入口签名 | 重试 |
|---|---|---|---|
| `login()` | ✅ | `() -> None` | 3 次指数退避 |
| `select_company()` | ✅ | `() -> None`(自动 login) | 3 次 |
| `upload_invoice_batch(histories, mappings)` | ❌(MR.ERP invoice_no 唯一约束) | `(List, Dict) -> ImportResult` | **不重试** · 失败走 listing fallback |
| `search_invoice(invoice_no)` | ✅ | `(str) -> Optional[InvoiceRecord]` | 3 次 |
| `delete_invoice(db_row_id)` | ✅ | `(str) -> bool`(post-delete listing 校验) | 3 次 |
| `dialog_log()` | ✅ | `() -> List[str]` | — |

### 14.3 ImportResult / SuccessRow / FailedRow 字段

```python
@dataclass class ImportResult:
    total: int                          # = len(input histories)
    success: List[SuccessRow]
    failed:  List[FailedRow]
    elapsed_ms: int
    xlsx_size_bytes: int
    report_xlsx_path: Optional[str]     # 当 importpc=2 时归档
    @property all_success: bool          # total>0 且 failed=[]

@dataclass class SuccessRow:
    invoice_no:     str                  # = derive_mrerp_invoice_no(history)
    mrerp_bill_no:  str                  # = "SI" + invoice_no
    original:       Dict                 # 原 history dict echo back

@dataclass class FailedRow:
    invoice_no:     str
    reasons:        List[str]            # หมายเหตุ \n-split lines
    original:       Dict
    evidence_screenshot: Optional[str]   # 报告捕获时刻 PNG
```

### 14.4 异常分类

```
MRERPError                       (base · 上层 catch-all)
├── MRERPAuthError               (登录被踢 / 主页被踢) → 不重试 · 通知用户
├── MRERPTechnicalError          (timeout / DNS / 5xx / 选择器缺) → 内部 3 次指数退避
└── MRERPBusinessError           (preview 0 行 / frmupload alert) → 不重试 · 返失败 row
                                  ⚠️ 注:per-row 业务失败不抛此异常 · 而是放 ImportResult.failed
                                  仅 xlsx 整体被拒(连 preview 都进不去)才抛
```

### 14.5 字段长度上限(adapter 调用方需自检)

详见 [mrerp-known-facts.md](mrerp-known-facts.md) §7 完整表。摘要:

| 字段 | 上限 | 超长后果 |
|---|---|---|
| `invoice_no` | 18 字符 | report.xlsx หมายเหตุ = `เลขที่ต้องไม่เกิน 18 ตัวอักษร` · row 失败 |
| `bill_no` | 20 字符 | `เลขที่บิลต้องไม่เกิน 20 ตัวอักษร` |
| `customer_code` | 20 字符 | `รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร` |
| `customer_bill` | 20 字符 | `รหัสลูกค้า (บิล) ต้องไม่เกิน 20 ตัวอักษร` |

⚠️ MR.ERP 校验顺序:**长度 > 主数据存在**(长度先错就遮盖"找不到"信息)· adapter 上游应做客户端长度校验,避免误诊。

### 14.6 测试

- `tests/unit/test_mrerp_report_parser.py`(6 tests · 离线)
- `tests/integration/test_mrerp_adapter_technical.py`(1 test · 无网络 · TEST-NET-1 IP)
- `tests/integration/test_mrerp_adapter_happy.py`(1 test · 需 .env.local · 用客户 `0006`)
- `tests/integration/test_mrerp_adapter_business_error.py`(1 test · 需 .env.local · 用 `9999NONEXISTPNLY`)

全套约 22s · 全过 = `ImportResult.all_success` 路径 + listing/delete 闭环已锁定。

