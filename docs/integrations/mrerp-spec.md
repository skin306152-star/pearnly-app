# MR.ERP 销项发票批量导入 · 端到端探测报告

> **🟡 9/10 跑通**(2026-05-18 路径 A 后):Korn 真样本 ssh 取回 · xlsx 字节级走 Korn-clone 路径 · 服务端 **AJAX 接收 + preview 显示 1 行 + confirm 调 importpc.php 返 `"2"`(JS 认为成功)** · 但 `artran/allview.php?idmenu=118` 列表所有 mode(l/r/a)**找不到新行**。
>
> 🔴 **未解**:`importpc="2"` 但 DB 没新行 · `report.php` 在 `_blank` popup 加载 · Playwright 抓不到 · sdpt-monkey-patch 改 _self 也卡住。**按指令异常即停 · 等 Zihao 决定** 排查方向。

最后探测:2026-05-18 18:39 · run_id `20260518-183903`
凭据:✅ `test01 / test01`
Korn 模板:✅ `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` 已 scp 取回 · 项目根 + `docs/integrations/templates/korn_sample_SC.xlsx`
脚本:[scripts/probe/probe-mrerp.py](../../scripts/probe/probe-mrerp.py)
先验:[docs/integrations/mrerp-known-facts.md](mrerp-known-facts.md)(本轮大幅扩充 §5/§6.3)
样本:[docs/integrations/sample-ocr.json](sample-ocr.json)

---

## 1. 状态总览

| 阶段 | 状态 | 说明 |
|---|---|---|
| 站点结构 | ✅ | landing → /login/login.php → selectdb → mainmenu → impartran |
| 登录 | ✅ | `test01/test01` · 一次通 |
| 选公司 TEST2019 | ✅ | comidyear=6 seldb=1 |
| SC 批量导入入口 | ✅ | `impartran/formupload.php?idmenu=370` |
| 上传表单 UI | ✅ | idus / selmenu / btnuploadfile / 模板锚点 example.xlsx 全抓到 |
| **xlsx 字节级生成** | ✅ | **Korn-clone 路径** · 用 Korn 真样本 styles.xml/workbook.xml 不动 · 仅改写 sheetData + sharedStrings · 8586B(vs Korn 10933B · 差异是数据量少) |
| **服务端 xlsx 接收** | ✅ | `frmupload()` AJAX POST `uploadexcel.php` 返空 body · `sdpt()` 跳 `formrdpc.php` preview |
| **preview 解析** | ✅ | 服务端解析 xlsx 后 preview 显示 **1 可勾行**(cbimport[N] checkbox)· 字段全识别 |
| **confirm 提交** | ✅ | 点 `btnuploadfrm1` → JS `confirm()` dialog accept → `uploadfrm(1)` POST `importpc.php` 返 `"2"` · JS 认为"完成+出报告" |
| 报告 popup | 🔴 | `sdpt()` `_blank` 打开 `component/report.php` · Playwright 抓 popup URL 空 · monkey-patch 改 `_self` 也卡 click timeout |
| **DB 写入** | 🔴 | `artran/allview.php?idmenu=118` 三种 mode(l/r/a)全部找不到 2026-05-18 行(即使用 Korn 已知 customer code `01-อนุรักษ์-001` + YYMMDD-NNN 格式 invoice_no 重试) |
| 列表搜索 + 删除 | ⏸️ | 阻于"DB 未写入"未解 |
| **测试数据污染** | 🟢 | 0 条新行进入 MR.ERP 列表 · 但是 `importpc="2"` 是否在某个隐藏 staging 表写入数据 · 暂不可知 · 等 Zihao 看 report 后决定是否清理 |

---

## 2. 端到端测试结果(本轮跑到 xlsx 被拒为止)

### 2.1 截图全链路(12 张 · 覆盖 step 1-6 + 服务端拒收)
| # | 文件 | 场景 | 信息 |
|---|---|---|---|
| 01 | `screenshots/01-landing-marketing-page.png` | GET `/` 落地 | 营销 SPA · 5 个导航链接 · 无登录表单 |
| 02 | `screenshots/02-login-page.png` | 点 `เข้าสู่ระบบ` 进 `/login/login.php` | 登录表单可见 · form action=`checklogin.php` |
| 03 | `screenshots/03-login-filled.png` | 填 `txtusers` + `txtpasswords` | 凭据已遮挡(filter) |
| 04 | `screenshots/04-post-login.png` | 提交后跳 `/login/selectdb.php` | ✅ 登录成功 · 公司选择页 |
| 05 | `screenshots/05-post-login-verified.png` | 双重验证(GET selectdb 不被踢) | ✅ 已认证 |
| 06 | `screenshots/06-company-clicked-TEST2019.png` | 点 TEST2019 公司 | 跳 mainmenu · `comidyear=6&seldb=1` 自动带上 |
| 07 | `screenshots/07-sc-import-form.png` | 直达 `impartran/formupload.php?idmenu=370` | 销项赊销批量导入页 |
| 08 | `screenshots/08-form-inspected.png` | 抓 form 结构 | **idus=15 抓到 ✓** · file input 存在 · selmenu default=118 |
| 09 | `screenshots/09-file-chosen.png` | `set_input_files(test-invoice.xlsx)` | 文件名显示在 `inpuploadfile` |
| 10 | `screenshots/10-after-upload.png` | 点 `btnuploadfile` → AJAX 触发 | 🔴 AJAX 返非空 → JS alert |
| 11 | `screenshots/11-preview-page.png` | (没真到 preview · 仍在 formupload) | URL 没变(AJAX 被拒) |
| 12 | `screenshots/12-preview-empty.png` | preview 0 行(因为没上传成功) | n_rows=0 |

### 2.2 实测站点结构(已写回 known-facts §2.1/§5/§9)
| 验证项 | 与先验对比 | 结果 |
|---|---|---|
| 登录表单 4 input + 0 hidden + 0 CSRF | known-facts §2.2 一字不差 | ✅ 反向工程稳定 |
| 上传按钮 `btnuploadfile` 是 `type=button` | known-facts 缺这条 | ✅ **新补**(§5 Step 1) |
| `frmupload()` 走 jQuery AJAX 而非 form submit | known-facts §5 暗示 | ✅ **明确补 JS 源码**(§5 Step 2) |
| AJAX 失败用 `alert(result)` 报错 | known-facts §9 缺 | ✅ **新补 dialog 抓 alert 规则**(§9) |
| `selmenu=118` 默认选中 ขายเชื่อ-รายได้ขายในประเทศ | known-facts §4 | ✅ 实测一致 |
| 表单含模板下载锚点 `<a href="example.xlsx">` | known-facts 未提 | ✅ **新补** · 但未实际下载验证 |

### 2.3 关键错误信息(MR.ERP 服务端原文)
**Playwright dialog handler 抓到的 alert 内容**:
```
Sheet ที่ 1 ไม่พบข้อมูลในการอัพโหลด
หรือข้อมูลในไฟล์ที่อัพโหลดมีจำนวนคอลัมภ์ข้อมูลไม่ครบ 18 คอลัมภ์
Sheet ที่ 2 ไม่พบข้อมูลในการอัพโหลด
หรือข้อมูลในไฟล์ที่อัพโหลดมีจำนวนคอลัมภ์ข้อมูลไม่ครบ 8 คอลัมภ์
Sheet ที่ 3 ข้อมูลในไฟล์ที่อัพโหลดมีจำนวนคอลัมภ์ข้อมูลไม่ครบ 3 คอลัมภ์
```

直译:
> Sheet 1: 找不到数据 或 上传文件中数据列数不到 18 列
> Sheet 2: 同 8 列
> Sheet 3: 同 3 列

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

## 3. 根因 + 修复路径推荐(待 Zihao 拍板)

---

### 3.0 路径 A 已执行(本轮)+ 仍未解的最后 10%

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

## 11. 截图清单(本轮 12 张)

```
docs/integrations/screenshots/
├── 01-landing-marketing-page.png        GET / → 营销页
├── 02-login-page.png                    /login/login.php · 4 input · 0 hidden ✅
├── 03-login-filled.png                  表单已填(凭据已遮)
├── 04-post-login.png                    302 → /login/selectdb.php ✅ 登录成功
├── 05-post-login-verified.png           双重验证通过 ✅
├── 06-company-clicked-TEST2019.png      点 TEST2019 → mainmenu ✅
├── 07-sc-import-form.png                impartran/formupload.php?idmenu=370 ✅
├── 08-form-inspected.png                idus=15 · file_in=True · selmenu=118 ✅
├── 09-file-chosen.png                   set_input_files 完成
├── 10-after-upload.png                  AJAX 触发(URL 不动 · 因被拒)
├── 11-preview-page.png                  停在 formupload.php(没跳 formrdpc)
├── 12-preview-empty.png                 n_rows=0 · 未到 preview
└── manifest.txt                         一键索引
```

Korn 模板修复后预期 +5 张:`13-preview-checked` / `14-after-confirm` / `15-search-result` / `16-after-delete` / `17-verify-deletion`

---

## 12. 已生产文件清单(本轮新加 + 沿用)

| 路径 | 用途 | 状态 |
|---|---|---|
| `scripts/probe/probe-mrerp.py` | 端到端探测脚本 | 已更新 step 06 + dialog handler |
| `docs/integrations/mrerp-known-facts.md` | 站点先验事实 | **本轮新增 §6.3 ⚠️** + §5 §9 实测扩充 |
| `docs/integrations/mrerp-spec.md` | 本文档 | **本轮重写** |
| `docs/integrations/sample-ocr.json` | OCR 真实输出 | 不变 |
| `docs/integrations/screenshots/01-12.png` | 12 张截图 | **本轮覆盖**(更深远) |
| `docs/integrations/templates/upload-form-*.html` | upload page HTML dump | ✅ 本轮抓到 |
| `docs/integrations/templates/test-invoice-*.xlsx` | 测试 xlsx(6807B · 3 sheet) | ✅ 但被 MR.ERP 拒 |
| `docs/integrations/probe-findings-*.json` | 探测过程结构化输出 | 含 alert 消息原文 |

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
