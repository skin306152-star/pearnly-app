# MR.ERP 集成 · 先验事实清单

> 来源：2026-05-10 反向工程实测(原 `mrerp_pusher.py` v118.27.8.0)+ Korn 真样本对照
> 维护原则：**事实归 docs · 不留废代码**(Pearnly 架构铁律 7)
> 后续 Playwright 探测脚本(`scripts/probe/probe-mrerp.ts`)以本文档为先验起点

---

## 1. 基础信息

| 项 | 值 |
|---|---|
| 站点 | https://www.mrerp4sme.com |
| 技术栈 | PHP + Apache(老 PHP 系统 · 整页跳转 · 无 SPA) |
| 认证 | **单一 PHPSESSID cookie** · 无 CSRF · 无 2FA · 无登录验证码 |
| 字符集 | UTF-8(含泰文/中文) |
| 测试公司 | `test01` / `TEST2019` |
| 测试公司参数 | `comidyear=6` · `seldb=1` |

⚠️ **客户码格式 = 公司自定义**(2026-05-18 修订):
- 旧 known-facts §7 写"三段式·含泰文(`01-อนุรักษ์-001`)" — 这只是 Korn DB 用法
- Skin DB 测试客户用 4 位数字 `0006`
- 实际是各租户自己规划编码方案 · ERP 不强制
- adapter 在 armas/allform.php 创建前先查 armas/allview.php 看码是否冲突

---

## 2. 登录流程

### 2.1 站点结构 · 落地 ≠ 登录页(2026-05-18 Playwright 实测补充)
- `https://www.mrerp4sme.com/` = **营销页**(无 form / 无 input)
- 登录表单实际在 `https://www.mrerp4sme.com/login/login.php`
- 营销页 → 登录页通过 `<a href="login/login.php">เข้าสู่ระบบ</a>` 跳转

老 PHP 系统**必须先 GET 一次登录页才会建 PHPSESSID session**。否则后续 POST 会被丢弃。

```
GET https://www.mrerp4sme.com/             ← 营销页 · 不建 session
GET https://www.mrerp4sme.com/login/login.php  ← 真正建 session
```

### 2.2 提交登录表单

```
POST https://www.mrerp4sme.com/login/checklogin.php
Content-Type: application/x-www-form-urlencoded
Referer: https://www.mrerp4sme.com/
Origin:  https://www.mrerp4sme.com
```

字段名(**注意复数 s**):
| 字段 | 值 |
|---|---|
| `txtusers` | 用户名 |
| `txtpasswords` | 密码 |
| `btnsubmit` | `Submit`(必带 · 否则 PHP 老代码不认) |

### 2.3 登录成败判定(踩坑笔记)
- POST 后 URL **不变**(同页 echo HTML · 不 redirect)→ 不能靠 URL 判
- 失败也返回 **200 + HTML**(再次回 login 表单)
- 正确判定:GET `/login/mainmenu.php` 后检查
  - 若 URL 包含 `checklogin` / `/login/index` / `/login/?` / `/login.php` → 失败
  - 若 body 含 `txtusers` 或 `txtpasswords` → 失败(被踢回登录表单)

---

## 3. 选公司流程

### 3.1 先到选公司页
```
GET https://www.mrerp4sme.com/login/selectdb.php
```

### 3.2 进入指定公司主菜单(等同点 TEST2019 按钮)
```
GET https://www.mrerp4sme.com/login/mainmenu.php?comidyear=6&seldb=1
Referer: https://www.mrerp4sme.com/login/selectdb.php
```

### 3.3 拿 idus(MR.ERP 内部用户 ID)

`idus` 是 MR.ERP 内部用户标识(test01 = "15")· **每个业务页**都以 `<input type="hidden" name="idus" value="N">` 出现 · 大多数业务接口必须带它。

**最稳的抓法**:GET 任意业务页(如 SC 上传页)后 scrape:
```html
<input type="hidden" name="idus" id="idus" value="15">
```

注意:`name` 和 `value` 之间常有 `id` 等其他属性 · 严格正则会漏 · 用 DOM 解析更稳。

---

## 4. 业务模块路径分类

🔴 **铁律**:MR.ERP 路径分两套(`impartran` ≠ `imparse`)
- `impartran/` = **交易类业务单据**(销售/采购/收付款)
- `imparse/` = **主数据类**(客户/商品档案 · 偶有交易)

`idmenu`(URL 路由 ID) ≠ `selmenu`(业务子类型字典)

| 业务子类型 | path | idmenu | selmenu | 实测 | 备注 |
|---|---|---|---|---|---|
| **销售-赊销**(sales_credit) | impartran | 370 | 118 | ✅ | Korn 样本已成功 import |
| 销售-现金(sales_cash) | imparse | 371 | TBD | 🟡 | selmenu 待抓(进 idmenu=371 看下拉 default) |
| 采购-赊购 | TBD | TBD | TBD | ❌ | 待抓 |
| 采购-现金 | TBD | TBD | TBD | ❌ | 待抓 |
| 客户档案 | imparse | TBD | TBD | ❌ | 待抓 |
| 商品档案 | imparse | TBD | TBD | ❌ | 待抓 |
| 财务收款 | impartran | TBD | TBD | ❌ | 待抓 |
| 财务付款 | impartran | TBD | TBD | ❌ | 待抓 |
| 会计凭证 | impartran | TBD | TBD | ❌ | 待抓 |

---

## 5. 销项发票批量导入 5 步流程(已实测 ✅)

### Step 1 · 进入批量导入页
```
GET https://www.mrerp4sme.com/impartran/formupload.php?idmenu=370
Referer: https://www.mrerp4sme.com/login/mainmenu.php
```

页面含:
- `<input type="file" name="uploadfile" id="uploadfile" accept="...spreadsheet..." onchange="cufexcel();">`
- `<input type="hidden" name="idus" id="idus" value="...">`
- `<input type="text" name="inpuploadfile" readonly>` (文件名显示框)
- `<input type="button" name="btnseluploadfile" value="เลือกไฟล์" onclick="seluploadfile();">` (选文件按钮)
- `<input type="button" name="btnuploadfile" value="อัพโหลด" onclick="frmupload();">` ← **真正的上传按钮**
- `<select name="selmenu">`(业务子类型下拉 · default `<option value="118">ขายเชื่อ-รายได้ขายในประเทศ</option>`)
- 模板下载链接(2026-05-18 实测):页面下方 `<a href="example.xlsx">` 类似锚点

🔴 **铁律**:`btnuploadfile` 是 `type="button"`(不是 `type="submit"`) · Playwright selector 必须用 `input[name="btnuploadfile"]` · 不能靠通用 submit selector

### Step 2 · 上传 xlsx(走 AJAX · 不是整页跳转)

`frmupload()` JS 实测(2026-05-18 抓的源码):
```js
function frmupload() {
    if (#uploadfile.value == "") alert("กรุณาเลือกไฟล์...");
    else if (#selmenu.value == "") alert("กรุณาเลือกเมนู...");
    else if (selmenu.option:checked.data-chklac == "2") alert("กรุณากำหนดการเชื่อมโยง...");
    else {
        var formdata = new FormData(#frm);
        $.ajax({
            type: "POST", url: "component/uploadexcel.php", data: formdata,
            success: function(result) {
                if (result == "")           // ← 空 = 成功
                    sdpt({idus, selmenu}, "formrdpc.php", "_self");   // 用 sdpt() 跳预览
                else {                       // ← 非空 = 错误信息
                    $("#frm")[0].reset();
                    alert(result);
                }
            }
        });
    }
}
```

POST 实际请求:
```
POST https://www.mrerp4sme.com/impartran/component/uploadexcel.php
Content-Type: multipart/form-data
Referer: https://www.mrerp4sme.com/impartran/formupload.php?idmenu=370
X-Requested-With: XMLHttpRequest
Origin: https://www.mrerp4sme.com
```

multipart 字段:
- `uploadfile` = .xlsx 二进制 + filename
- `idus` = 上一步 scrape 的值
- `selmenu` = `118`(sales_credit)

**响应**:
- 成功 = `200 + 空 body` → JS 用 `sdpt()` 跳 `formrdpc.php`(client-side form post)
- 失败 = `200 + 错误描述 string` → JS `alert(string)` + form reset
  - 实测错误格式(2026-05-18):`Sheet ที่ N ไม่พบข้อมูลในการอัพโหลด หรือข้อมูลในไฟล์ที่อัพโหลดมีจำนวนคอลัมภ์ข้อมูลไม่ครบ M คอลัมภ์`

🔴 **关键**:Playwright 必须**全局挂 `page.on("dialog", ...)`** 才能抓到失败原因 · 否则 alert 被 Playwright 默认 auto-dismiss · 信息全丢

### Step 3 · 拿预览页(解析可勾选行)
```
POST https://www.mrerp4sme.com/impartran/formrdpc.php
Content-Type: application/x-www-form-urlencoded
Referer: https://www.mrerp4sme.com/impartran/formupload.php?idmenu=370
```

form 字段:
- `idus` = ...
- `selmenu` = `118`

**响应 HTML 含**:
- `<input type="checkbox" name="cbimport[N]" value="N">`(N = row_id · 服务端分配)
- 同一 `<form id="frmimportN">` 内有表头 `<p>` + 数据 `<p>` · `<span>` 装值
- 失败时**没有 cbimport · 但可能有错误 HTML**(红字 / `<font color=red>` / JS `alert()` / `ไม่พบ` / `ผิดพลาด` / `ซ้ำ` 等关键词)

### Step 4 · 确认导入(UI · 走 uploadfrm() AJAX)

实测(2026-05-18) · preview 页确认按钮 UI:
```html
<button name="btnuploadfrm1" id="btnuploadfrm1" onclick="uploadfrm(1);">นำเข้าข้อมูล</button>
```

每个 `<form id="frmimportN">` 配套一个 `btnuploadfrmN` 按钮(N=1,2,...)。

`uploadfrm(N)` JS 源码(2026-05-18 抓):
```js
function uploadfrm(form) {
    // 必须有勾选 cbimport
    if (querySelectorAll(`[id=frmimport${form}] [id^=cbimport]:checked`).length > 0) {
        if (confirm(`ยืนยันการ "นำเข้าข้อมูลชุดที่ ${form}"`)) {     // ← JS confirm() · Playwright 必须挂 dialog handler
            let formdata = new FormData(`#frmimport${form}`);
            $.ajax({
                type: "POST", url: "component/importpc.php", data: formdata,
                success: function(result) {
                    if (result == "1") {
                        // "นำเข้าข้อมูลชุดที่ N เสร็จสมบูรณ์" (完成)
                        disableform(form);
                    }
                    else if (result == "2") {
                        // "จบกระบวนการ ระบบกำลังออกรายงาน" (处理结束·系统正在出报告)
                        disableform(form);
                        sdpt({numform:form, idus:$("#idus"+form).val()}, "component/report.php", "_blank");
                    }
                    // else (非 1 非 2): 未知 · 推测是错误描述 string
                }
            });
        }
    }
}
```

**POST endpoint**:
```
POST https://www.mrerp4sme.com/impartran/component/importpc.php
Content-Type: multipart/form-data (FormData(#frmimportN) · 含全 row hidden inputs)
Referer: https://www.mrerp4sme.com/impartran/formrdpc.php
```

**响应**(实测确认 2026-05-18 adapter happy + business error):
- `"1"` = **全部 row 成功提交 · 不生成报告**(实测 happy path · 服务端 importpc.php 体只返 "1" · 不调 sdpt · 没有 report.php 请求)
- `"2"` = **有 row 失败 · 生成报告**(实测 business error · importpc.php 体返 "2" · JS 调 sdpt → POST report.php · 服务端返 xlsx 附件)

🔑 **adapter 关键**:不要永远等 report.php · "1" 时不会有 report · 必须先抓 importpc.php 响应体判分支

⚠️ **2026-05-18 实测重要发现** · `importpc="2"` **不等于** DB 实际写入:
- 完整流程跑通(login → upload → preview 显示 1 行 → click `btnuploadfrm1` → JS confirm dialog accept → AJAX 返 `"2"`)
- 但 `artran/allview.php?idmenu=118` 列表所有 mode(l/r/a)**都看不到新行**
- 用 Korn 已知存在的 `customer_code=01-อนุรักษ์-001` + `invoice_no=690518-999`(YYMMDD-NNN 格式)重试 · 结果同
- 推测 `report.php` 弹窗里有真正的错误/状态信息 · Playwright 抓 popup 时 URL 空 + sdpt 改 `_self` 也卡住 · **待 Zihao 决定排查方向**

### Step 5 · 列表 / 查询 / 删除(2026-05-18 实测补)

**列表 URL 模式**:`/<module>/allview.php?idmenu=<biz_id>[&mode=l|r|a]`
- `<module>` = `artran`(AR Transaction · 销售类) / `imparse`(主数据类) / 其他
- `<biz_id>` = 业务子类型 id(跟 `selmenu` 同号 · 见 §4)
- `mode=l` = List All(全部)
- `mode=r` = Reviewed(已审)
- `mode=a` = Approved(已批)

**已知销售类菜单 idmenu 表**(从 mainmenu HTML 抓 · 2026-05-18):
| 业务 | 模块 | idmenu | 列表 URL |
|---|---|---|---|
| 报价 (ใบเสนอราคา) | arsq | 109 | `/arsq/allview.php?idmenu=109` |
| 销售单 (ใบสั่งขาย) | arso | 112 | `/arso/allview.php?idmenu=112` |
| 收预付 (รับเงินล่วงหน้า) | arad | 115 | `/arad/allview.php?idmenu=115` |
| **销售-赊销** (ขายเชื่อ) | **artran** | **118** | `/artran/allview.php?idmenu=118` |
| 增项票 (ใบเพิ่มหนี้) | arsd | 121 | `/arsd/allview.php?idmenu=121` |
| 减项票 (ใบลดหนี้) | arsc | 123 | `/arsc/allview.php?idmenu=123` |

**列表页元素**(2026-05-18 实测 artran/allview):
- 搜索框:`<input name="txtsearch" placeholder="ค้นหาจาก เลขที่, วันที่, ชื่อ และ จำนวนเงิน" onkeyup="searchdata(1);">`(搜:编号/日期/名/金额)
- 列表头:`เลขที่เอกสาร · วันที่เอกสาร · ชื่อลูกค้า · จำนวนเงิน · URA · View · Edit · Del`
- 注意:**列表 `เลขที่เอกสาร` 列显示的是 `bill_no`(SI + invoice_no)·**不是** `invoice_no` 本身**
- 删除入口:同 row 内 `<a href="allform.php?id=N&status=del"></a>`(N = MR.ERP 内部 row id · 不是 invoice_no)
- 状态切换:`<button onclick="location='allview.php?mode=l';">` 等 3 个按钮

**Mainmenu 结构**(必须先点 parent 才会出 child · `mmlv2()` JS 动态展开):
- top-level: `<span onclick="mmlv2(this);" data-code="m5">ระบบขาย</span>`
- 二级: 展开后才在 DOM 可见 · 三级链接才是 `<a href="../artran/allview.php?idmenu=118">`

### Step 6 · 删除单条记录(2026-05-18 实测 · 2 步)
**Step 6a · 进删除前确认页**(GET · 不真删):
```
GET https://www.mrerp4sme.com/<module>/allform.php?id=<row_db_id>&status=del
```
- `<row_db_id>` 从 listing row 的 `<a href="allform.php?id=N&status=del">` 取
- 页面渲染完整发票表单(只读)+ 末尾有 `<button id="btndel" onclick="confirmdel('N');">Delete</button>`

**Step 6b · 点 btndel + dialog accept**:
- click `btndel` → JS `confirmdel(N)` → 弹 `confirm("ยืนยันการลบข้อมูล")`
- accept → POST 真删 → 跳 `allview.php`(回列表)
- Playwright 必须挂全局 `page.on("dialog")` accept

### Step 7 · 主数据创建(客户/商品/销售员)
**客户(实测)**:
- 创建 URL: `https://www.mrerp4sme.com/armas/allform.php`
- 列表 URL: `https://www.mrerp4sme.com/armas/allview.php`
- 完整字段表 → 见 [docs/integrations/mrerp-customer-form-fields.md](mrerp-customer-form-fields.md)

**商品**:URL 路径未抓 · 主菜单 ระบบสินค้า(m3) 下 · 类似 `<module>/allform.php` 模式

**销售员**:同上 · 主数据类别(可能在 ระบบข้อมูลกลาง m2 下)

### Step 8 · 解析导入报告(report.php 下载的 xlsx)

实测(2026-05-18 Zihao 手动 D1):`importpc.php` 返 `"2"` 后 · `sdpt()` 跳 `component/report.php` 在 _blank 新窗口 · 服务端**下载 xlsx 报告**(命名 `รายงานการนำเข้าข้อมูลชุดที่ N [DDMMYYYY_HHMMSS].xlsx`)

**报告 xlsx 结构**(`docs/integrations/samples/report_failure_customer_not_found.xlsx`):
- **跟 upload xlsx 同 3 sheet 同 sheet 名**(`Worksheet` / `Worksheet 1` / `Worksheet 2`)
- **每 sheet 末尾 +1 列 `หมายเหตุ`**(对比上传时少这列):
  - Sheet 1: 18 → **19 列**(末尾 หมายเหตุ)
  - Sheet 2: 8 → **9 列**
  - Sheet 3: 3 → **4 列**
- Sheet 1 dim 扩到 26 列(末尾占位空 cell)· col 19 即 หมายเหตุ
- **每 row 的 หมายเหตุ cell**:
  - 空 = 该 row 写库成功
  - 非空 = 错误描述(泰文 · 可多行 用 `\n` 分隔)

**adapter 解析方法**(MVP 必含):
```python
from openpyxl import load_workbook
wb = load_workbook(report_xlsx_bytes)
ws = wb["Worksheet"]   # sheet 1 是单据头
header_cells = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column+1)]
note_col = header_cells.index("หมายเหตุ") + 1   # 最后一列(label)
for r in range(2, ws.max_row + 1):
    note = ws.cell(row=r, column=note_col).value
    invoice_no = ws.cell(row=r, column=1).value   # เลขที่
    if note:
        # 该 row 写库失败 · note 是错误描述
        error_msg = note.strip()
    else:
        # 成功
        ...
```

**已知错误信息文案**(2026-05-18 实测):
| 错误文案 | 触发条件 | 解决 |
|---|---|---|
| `ไม่พบข้อมูลรหัสลูกค้า` | customer_code 不在主数据 | 用 armas/allform.php 先建客户(见 §5 Step 7) |
| `ไม่พบข้อมูลรหัสลูกค้า (บิล)` | customer_bill code 不在主数据 | 同上(通常 customer_bill = customer_code) |
| (待抓)`ไม่พบข้อมูลรหัสสินค้า` | product_code 不在主数据 | 商品主数据创建 |
| (待抓)`ไม่พบข้อมูลพนักงานขาย` | salesman 名不在主数据 | 销售员主数据创建 |
| (待抓)`เลขที่เอกสารซ้ำ` | invoice_no 重复 | 改 invoice_no 或先删旧 |

**重要**:`importpc.php` 返 `"2"` **不等于** 所有 row 都写库 · "2" 的语义是 "process completed + 出报告" · 真实结果**必须看 report xlsx 的 หมายเหตุ 列**。

---

## 6. xlsx 文件格式(sales_credit 模板)

### 6.1 sheet 命名 🔴 严格
sheet 数随模板动态 1-4 · 命名 **必须空格分隔**(不是 Sheet1/Sheet2):

| sheet 数 | sheet 名 |
|---|---|
| 1 | `Worksheet` |
| 2 | `Worksheet` · `Worksheet 1` |
| 3 | `Worksheet` · `Worksheet 1` · `Worksheet 2` |
| 4 | `Worksheet` · `Worksheet 1` · `Worksheet 2` · `Worksheet 3` |

### 6.2 sales_credit 3-sheet 结构

#### Sheet 1 `Worksheet`(单据头 · 18 列)
| # | label(泰) | key | type | 默认值 / 备注 |
|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | str(30) | YYMMDD-NNN(BE 年) · 见 §7 |
| 2 | วันที่ | invoice_date | date | YYYY-MM-DD(西历) · cell `@` |
| 3 | อัตราภาษี | tax_rate_str | str(14) | `7 (แยก)` |
| 4 | สาขา | branch_code | str(14) | `00000` |
| 5 | แผนก | department | str(14) | `BOI1` |
| 6 | งาน | job | str(14) | `00002` |
| 7 | พนักงานขาย | salesman | str(30) | `กร ทดสอบ` |
| 8 | กำหนดส่งสินค้า | delivery_date | date | 通常 = invoice_date |
| 9 | รหัสลูกค้า | customer_code | str(50) | 三段式 · 含泰文(`01-อนุรักษ์-001`) |
| 10 | รหัสลูกค้า (บิล) | customer_bill | str(50) | 通常 = customer_code |
| 11 | เลขที่บิล | bill_no | str(30) | `SI` + invoice_no |
| 12 | วันที่ | bill_date | date | = invoice_date |
| 13 | พื้นที่การขาย | sales_area | str(30) | `สุพรรณบุรี` |
| 14 | ประเภทขนส่ง | shipping_type | str(30) | `ขนส่งโดยบริษัท` |
| 15 | หักส่วนลด | discount | num | `0` |
| 16 | หมายเหตุ 1 | note1 | str(50) | 留空(Korn 真样本) |
| 17 | หมายเหตุ 2 | note2 | str(50) | 留空 |
| 18 | หมายเหตุ 3 | note3 | str(50) | 留空 |

⚠️ **额外冷知识**:sheet 1 dimension 必须扩到 **A1:S2**(col 19)· 第 19 列补完全空 cell · 否则 PhpSpreadsheet 解析差异。

#### Sheet 2 `Worksheet 1`(商品明细 · 8 列 · 每行 1 件商品)
| # | label(泰) | key | type | 备注 |
|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | str(30) | 关联 sheet 1 invoice_no |
| 2 | รหัสสินค้า | product_code | str(30) | 默认 `123`(找不到 mapping 时) |
| 3 | แผนก | department | str(14) | `BOI1` |
| 4 | งาน | job | str(14) | `00002` |
| 5 | คลัง | warehouse | str(14) | `0000` |
| 6 | จำนวน | qty | num | |
| 7 | ราคา/หน่วย | unit_price | num | |
| 8 | จำนวนเงิน | amount | num | |

#### Sheet 3 `Worksheet 2`(尾 · 3 列 · 条件可选)
| # | label(泰) | key | type | 备注 |
|---|---|---|---|---|
| 1 | เลขที่ | invoice_no | str(30) | |
| 2 | เลขที่เงินมัดจำ | deposit_no | str(30) | 押金号 · 通常留空 |
| 3 | ออกใบขาย | is_sales_issued | str(14) | 是否开销售单 · 通常留空 |

Korn 真样本 sheet 3 **只有 header · 没 data row** → MR.ERP 服务端把这页当条件可选。

### 6.3 xlsx 字节级冷知识(PhpSpreadsheet 兼容性)

✅ **2026-05-18 Playwright 实测 + Korn 真样本字节级对照(commit 待补)修正前述假设**:

实测拿到 Korn 真样本(2026-05-10 服务器交付的 `test_data_mrerp_sample_SC.xlsx` · 10933B · 3 sheet)字节级解构对照后,真正的规则是:

**通用规则**:
- 字符串走 `sharedStrings.xml` · **不能用 inlineStr**(PhpSpreadsheet 不识别)
- 数值 cell **不带 `t="n"` 属性**(Korn 真样本 default 是 numeric · 加 t 反而异常)
- 每行 `<row>` 带 `spans="1:N"` + `ht="23.1"` + `customHeight="1"` + `x14ac:dyDescent="0.2"` 属性
- worksheet 根标签必须含 `xmlns:x14ac="..."` + `mc:Ignorable="x14ac"`
- 缺失 cell **可以**用完全空 `<c r="X#"/>`(Korn 真样本 P2/Q2/R2/S2 就是这种 · 之前 §6.3 旧假设 **没错** · 上轮 probe 失败是 style 索引问题不是空 cell 问题)
- 日期单元格 number_format = `@`(强制文本)

**Korn 真样本 styles.xml(cellXfs count=7 · 必须保留)**:
| 索引 | numFmt | 用途 |
|---|---|---|
| s=0 | default | 不用 |
| s=1 | 0 + valign=center | 不用 |
| s=2 | **49 文本** + halign=center + valign=center | **表头**(header row 1) |
| s=3 | 49 文本 + valign=center | **string 数据 cell**(data row · 非日期) |
| s=4 | **187 yyyy-mm-dd** + valign=center | **日期 cell**(B2/H2/L2 = invoice_date/delivery_date/bill_date) |
| s=5 | **4 数字 #,##0.00** + valign=center | **数值 cell**(O2 折扣 + sheet2 qty/price/amount) |
| s=6 | 49 文本(无 alignment) | **spacer 占位**(sheet1 S2 末尾) |

⚠️ **2026-05-18 实测 v1 失败的真因**:openpyxl fallback 路径生成的 styles.xml **自己的 s=1/2/3** 跟 Korn 的 s=2/3/4/5/6 含义完全不同 · MR.ERP 解析 cell 时按 style 索引检查"有效数据列",我们 s=2 引用了无效格式 → MR.ERP 数据列数判定失败 → alert `ไม่ครบ N คอลัมภ์`

**正确做法**:用 `_generate_xlsx_sales_credit_korn_clone()` 路径 = 完全保留 Korn 模板的 styles.xml + workbook.xml + [Content_Types].xml + theme.xml · **仅**改写 `sheet1.xml`/`sheet2.xml`/`sheet3.xml` 的 `<sheetData>` 段 + `sharedStrings.xml` · 这样所有字节级规则全继承 Korn

生产部署清单:`test_data_mrerp_sample_SC.xlsx` 必须存在于 `mrerp_xlsx_generator.py` 同目录 · 从服务器 `/opt/mrpilot/test_data_mrerp_sample_SC.xlsx` 取

---

## 7. 字段格式规则

### invoice_no 格式 · YYMMDD-NNN(BE 年)
Korn 真样本:`690507-001`
- `69` = 佛历年末 2 位 = 西历年 + 543 → 取末 2 位(2026 → 2569 → `69`)
- `0507` = 月日
- `-001` = 服务端再分配的序号

### 字段长度上限(2026-05-18 集成测试发现)
| 字段 | 上限 | 报错文案 |
|---|---|---|
| `invoice_no`(เลขที่)| **≤ 18 字符** | `เลขที่ต้องไม่เกิน 18 ตัวอักษร` |
| `bill_no`(เลขที่บิล)| **≤ 20 字符** | `เลขที่บิลต้องไม่เกิน 20 ตัวอักษร` |
| `customer_code`(รหัสลูกค้า)| **≤ 20 字符** | `รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร` |
| `customer_bill`(รหัสลูกค้า (บิล))| **≤ 20 字符** | `รหัสลูกค้า (บิล) ต้องไม่เกิน 20 ตัวอักษร` |

⚠️ 这几条限制是 **MR.ERP 服务端业务校验** · xlsx 模板 schema 字段标 `str(30)` / `str(50)` 但服务端实际更严
→ adapter 输入侧需要预先截断 / 验证(2026-05-18 PT-XXXXXX 6-hex 后缀超 18 触发)
→ 测试用 `PEARNLY-TEST-XXXX`(4-hex 后缀 = 17 字符)+ customer_code ≤ 20 字符安全

### 客户码 · 三段式 · 含泰文
`01-อนุรักษ์-001`

### 税率字符串枚举
| 字符串 | 含义 |
|---|---|
| `7 (แยก)` / `7%` | 标准 7% VAT |
| `0%` | 零税率 |
| `นอกระบบ` | 不在 VAT 体系内 |
| `ยกเว้น` | 免税 |

### 金额上限
`999,999,999.99`(超限要截断 · 见 `mrerp_xlsx_generator.fmt_number`)

---

## 8. Playwright 探测策略建议

基于以上事实 · 探测脚本应:

1. **不直接用 HTTP** · 用 Playwright 完整模拟用户(浏览器跳转/cookie/JS 都靠引擎)
2. **凭据从 `.env.local` 读** · 绝不硬编码 · 不打印
3. **headed 模式让 Zihao 看一遍** · 再 headless 验证
4. **每步截图** · 失败也截 · 存 `docs/integrations/screenshots/`
5. **测试发票用 `PEARNLY-TEST-` 前缀** · 客户名 `PEARNLY TEST CO.,LTD.` · 方便人工识别 + 清理
6. **走完整流程**:登录 → 选公司 → SC 模块 → 上传 → 预览审核 → 确认 → 列表搜索 → 删除验证

⚠️ **未知项**(探测脚本要发现):
- 上传后**列表页 URL**(impartran 系列的"查看/搜索/编辑/删除"路径未抓过)
- 列表页**搜索筛选字段**
- 单条发票**编辑/删除入口**(可能在主菜单别处 · 不在 impartran 下)
- **下载模板按钮**是否存在(formupload.php 上可能有)

---

## 9. 已知失败 case + 排错线索

| 现象 | 可能原因 | 排查 |
|---|---|---|
| 上传按钮点击后页面没跳 | `frmupload()` AJAX 上传失败 · 服务端返非空 string · JS `alert(result)` 弹窗 | **必须挂 Playwright `page.on("dialog", ...)`** 捕获 alert 内容(2026-05-18 实测发现) |
| alert `Sheet N ไม่พบข้อมูล / ไม่ครบ N คอลัมภ์` | xlsx 字节级与 MR.ERP 期望不符 · 数据列数不足 | 见 §6.3 ⚠️ · 排查 row 2 实际"有 `<v>` 数据列"数量 |
| 上传 200 但预览页 0 行 | xlsx 数据被服务端拒(走到 preview 但无 cbimport) | scrape HTML 找 `<font color=red>` / `ไม่พบ` / `ผิดพลาด` / `ซ้ำ` 等 |
| 上传 401/403 | session 过期 | 重新登录 |
| 选公司被踢回 login | 密码错 / session 没建 | 检查是否漏 §2.1 预热 GET |
| 提交后 URL 是 `/index.php` | 登录失败(静默 302 回营销首页) | 用"body 含 `ออกจากระบบ` OR URL 含 selectdb/mainmenu"做正向判定 |
| confirm 返非数字 | 业务校验失败 | response body 通常带泰文错误描述 |
| scrape idus 失败 | 服务端返了登录页 | dump body 前 1500 字符诊断 |

---

## 10. 凭据存储铁律

- ❌ **绝对不**把 MR.ERP 用户名/密码写进代码
- ❌ **绝对不**把它们提交进 git
- ✅ 探测脚本走 `.env.local`(已在 `.gitignore`)
- ✅ 未来生产存 DB 必须经 `kms_helper.encrypt_str` 加密(Fernet · key 在服务器 env)

---

## 10. 主数据依赖矩阵(销项导入前必须存在)

2026-05-18 实测确认 · sales_credit xlsx 导入要求以下主数据在 MR.ERP DB **已存在**(否则 report 报错):

| xlsx 字段 | 主数据类型 | 创建路径 | 风险 | 实测错误文案 |
|---|---|---|---|---|
| `customer_code` | 客户 | `armas/allform.php` · ✅ 实测 | 🔴 高 | `ไม่พบข้อมูลรหัสลูกค้า` |
| `customer_bill` | 客户(bill) | 同上(通常 = customer_code) | 🔴 高 | `ไม่พบข้อมูลรหัสลูกค้า (บิล)` |
| `product_code` | 商品 | 待抓 · ระบบสินค้า(m3) 下 | 🔴 高 | (待实测 · 推测 `ไม่พบข้อมูลรหัสสินค้า`) |
| `salesman` | 销售员名 | 待抓 · 可能 ระบบข้อมูลกลาง(m2) | 🟡 中 | (待实测) |
| `department`("BOI1") | 部门码 | 待抓 | 🟢 低 | (默认值通常 OK) |
| `job`("00002") | 工作号 | 待抓 | 🟢 低 | 同上 |
| `branch_code`("00000") | 分店码 | 内置 总部 | 🟢 低 | — |
| `tax_rate_str`("7 (แยก)") | 税率枚举 | 系统预置 | 🟢 低 | — |
| `sales_area` / `shipping_type` | 销售区/运输 | 客户主数据继承 | 🟢 低 | — |

### 10.1 客户码格式 · 公司自定义(非通用三段式)

2026-05-18 实测两个 DB 客户码格式完全不同:

| DB | 公司 | 客户码格式 | 示例 |
|---|---|---|---|
| Korn DB(seldb=?) | Korn Trading | **三段式 含泰文** | `01-อนุรักษ์-001` |
| Skin DB(`comidyear=6` / `seldb=1` / TEST2019) | 测试公司 | **4 位数字** | `0006` |

→ **客户码不是 ERP 强制格式** · 各租户自己规划编码方案。
→ adapter 接入时:**先查 `armas/allview.php` 搜索 customer_code 是否冲突** · 然后才能新建。
→ 旧 known-facts §7 写"必须三段式" = **误解** · 仅 Korn DB 用法。

### 10.2 已知存在的测试客户码

| DB | 客户码 | 客户名 | 用途 |
|---|---|---|---|
| Korn DB | `01-อนุรักษ์-001` | (未知 Thai name)| Korn 2026-05-10 reverse-engineering 实测样本 |
| Skin DB(TEST2019) | `0006` | `Skin Trading Co., Ltd.` | **2026-05-18 Zihao 建** · probe end-to-end 用 |

### 10.3 报错文案解析方法

**永远从 `report.php` 下载的 xlsx 解析** · 不靠 importpc.php response code 判定:
- `importpc.php` 返 `"2"` ≠ 写库成功 · 只是"流程结束 + 出报告"
- **真实结果在 report xlsx**:`Worksheet` sheet · 最后一列 `หมายเหตุ` · 每 row 一个错误描述(空 = 该 row OK)
- 详见 §5 step 8

**已知错误文案**(2026-05-18 实测样本 `samples/report_failure_customer_not_found.xlsx` + adapter 集成测试):
- `ไม่พบข้อมูลรหัสลูกค้า` = 找不到客户码(customer_code 列)
- `ไม่พบข้อมูลรหัสลูกค้า (บิล)` = 找不到 customer_bill code
- `รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร` = customer_code 超 20 字符
- `รหัสลูกค้า (บิล) ต้องไม่เกิน 20 ตัวอักษร` = customer_bill 超 20 字符
- `เลขที่ต้องไม่เกิน 18 ตัวอักษร` = invoice_no 超 18 字符
- `เลขที่บิลต้องไม่เกิน 20 ตัวอักษร` = bill_no 超 20 字符
- 同 row 多错误用 `\n` 分隔(例:`ไม่พบข้อมูลรหัสลูกค้า\nไม่พบข้อมูลรหัสลูกค้า (บิล)`)

**校验顺序**(2026-05-18 集成测试发现):MR.ERP 服务端**先做长度校验** · 长度过 → 直接返长度错;长度过 → 才查主数据存在 → 返"找不到"
→ adapter MUST validate field lengths client-side before xlsx upload(否则 "ไม่พบ" 类错误被长度错误屏蔽 · 用户看不到根因)

### 10.4 客户主数据 Copy-from-Seed 创建流(2026-05-18 实测)

`armas/allform.php` 的 `inpdupdata`("สำเนา")按钮触发 `bshlistbox(this)` 弹出客户列表 · 点击行后 JS 函数 `bshlistboxafterselectdata` 通过 AJAX 把整个 seed 客户的所有字段(包括所有 master-data ref:salesman / sales area / shipping type / other branch / GL account code · 加上对应的 hidden val IDs)复制进当前表单。

**调用方需覆盖的 4 个字段**:
- `txtarcode`(新客户码)
- `txtname`(新客户名)
- `txttaxid`(新税号)
- `txtaddr1..4`(若 OCR 抓到)

**不要覆盖**:`txtrectype` / `txtacfile` / `txtemp` / `txtararea` / `txtardelivery` / `txtothcombrhcus` 全套 + 数字默认 (`txtdiscount=0.00` 等)+ `txtcountry=ประเทศไทย` + `selprefix=1`。

完整字段映射:[docs/integrations/mrerp-customer-copy-flow.md](mrerp-customer-copy-flow.md)

**已知限制**:`test01` 账号在 TEST2019 上 alldel.php 返"Delete Success"但客户不删 · 测试 orphan 累积。生产用 admin 账号不受影响。详见 copy-flow.md §8。

### 10.6 商品主数据 Copy-from-Seed 创建流(2026-05-18 实测 · Task 2 Phase 3)

`stkmas/allform.php` 也有 `inpdupdata`(สำเนา)按钮 + 同款 bshlistbox popup。

**关键差异 vs 客户(armas)**:
- 弹层**虚拟滚动**:73+ 商品的 TEST2019 popup 一次只 DOM-渲染 ~10 行;直接点击行选择只对前 N 个有效
- 弹层有内置 search 输入 `#bshlistboxinpsearch`(onkeyup="bshdatalistbox()")· 输入种子码就过滤
- adapter 实现:`MRERPProductSyncService._copy_from_seed` 先 `fill()` 搜索框再 `click()` 行

**Override 字段(6 个 vs customer 的 4 个)**:
- `txtstkcode`(商品码 · adapter 生成)
- `txtstkname`(商品名 · OCR `items[].name`)
- `txtstkapcode` / `txtstkapname`(AP 镜像)
- `txtstkarcode` / `txtstkarname`(AR 镜像)

**继承 seed**:`selstktype` / `selstkmet` / 4 个 unit triplet / 9 个 GL account triplet / AP master ref / 价格 / cost / TRU + disable flags。

**ERR/WARN catalog**(Task 2 新加 · 4-lang):
- `ERR_NO_SEED_PRODUCT` · 没配 seed 抛
- `ERR_SEED_PRODUCT_NOT_FOUND` · seed 码不在 popup
- `ERR_PRODUCT_UNIT_NOT_FOUND` · OCR `item.unit_code` 与 seed 的 `txtunit_usell` 不匹配
- `WARN_PRODUCT_NAME_TRUNCATED` · 商品名超 100 字符自动截断
- `WARN_PRODUCT_PRICE_INHERITED_FROM_SEED` · seed 销售价照搬给新商品 · 提醒用户事后改

完整字段映射:[docs/integrations/mrerp-product-form-fields.md](mrerp-product-form-fields.md) · 实现:[services/erp/mrerp_product_sync.py](../../services/erp/mrerp_product_sync.py)

**已知限制**:同 customer · `test01` alldel.php 返 "Delete Success" 但不真删 · 生产用 admin 不受影响。

### 10.7 adapter 创建顺序(逻辑依赖)

1. 销售员 / 部门 / 工作号 / 分店(用户首次配置 · 1 次性)
2. 商品(OCR 看到新商品名 → 抓 + 自动建 · 主流场景)
3. 客户(OCR 看到新客户名/税号 → 抓 + 自动建)
4. **然后**才能 sales_credit xlsx 上传 + 下载 report + 解析 หมายเหตุ → 用户看
5. 如有 row 失败:从报错文案推断缺啥主数据 → auto-create → retry

⚠️ **adapter 设计要点**:
- 上传前先用 Playwright nav 各 `allview.php` 列表 · 搜 customer/product/salesman 是否存在
- 不存在 → 自动建(`allform.php` 填表 + 保存)
- 上传后 **永远下载 report.php xlsx 解析 หมายเหตุ** · 不靠 importpc response code
- 失败 row 给用户清晰错误信息(基于 หมายเหตุ 文案 · 可 i18n 4 语)
- 这是 **adapter MVP 必含功能**

---

## 11. 历史窗口产出参考

抓包窗口产出的代码已按"事实归 docs / 不留废代码"铁律删除 · 仅本文档作为先验留存。如需深度回溯历史 cURL / 字节序列实测过程 · 见:
- `CLAUDE.md/STATE_PEARNLY.md` § "🔌 MR.ERP 反向工程结果"
- `CLAUDE.md/BACKLOG.md` § v27.8.0 ~ v27.8.1.x
- `docs/cleanup/round1-final-report.md`

xlsx 生成器仍保留(`mrerp_xlsx_generator.py`)· Playwright 方案上传同一文件格式 · 不需要重写。

---

## 12. 现金销售(sales_cash · ใบขายเงินสด)· 2026-07-01 实测定型

- 端点:`imparse` / idmenu 371 / selmenu 125 · 回读列表 `arse/allview.php?idmenu=125`。
- 模板:官方 `test_data_mrerp_sample_cash.xlsx`(4 sheet · 克隆生成见 `services/erp/mrerp_xlsx_sales_cash.py`)。
  - Sheet1 = 25 列表头(赊销前 14 列 + `หักส่วนลด`折扣 + `จำนวนเงินสดรับ`现金收讫 + `รับอื่นๆ 1/2/3`收款科目及金额 + 3 备注)。
  - Sheet2 商品明细 / Sheet3 尾 与赊销同 · Sheet4 支票页(现金/转账留空表头)。
  - 共享样式索引(该模板 cellXfs):表头 s=4 · 文本 s=8 · 日期 s=9 · 数值 s=10。
- **★收款模型(踩坑定型)**:`รับอื่นๆ 1/2/3` **不是付款方式代号,是 GL 科目码**(科目表 · `1111-01`=现金 / `1112-01`=银行储蓄 …)。
  - 空 → `เป็นค่าว่าง`;填自由文本/银行账户代号(如 `ARBA01`)→ `ไม่พบข้อมูล`。
  - **3 个收款槽必须全非空且是有效科目码**。做法:槽1=收款科目/全额,槽2/3=同科目/金额 0(占位满足非空,不产生额外分录);`จำนวนเงินสดรับ` 现金收讫填 0。
  - 转账/刷卡票→银行科目;现金票→现金科目。⚠️ 科目码**按套账不同**,生产须按套账注入(对接 S4 科目解析);未配用 TEST2019 默认,推别的套账会因科目不存在被 report 回读挡下(fail-safe)。
- 科目码来源:现金票表单 `รายได้อื่น` 字段(`txtacfile_dispai` · onfocus `bshlistbox`)弹出科目选择器;TEST2019 现金/银行段:`1111-01`现金 / `1111-02`备用金 / `1112-01`银行储蓄 / `1113-01/02`活期。
- 端到端验证:HTTP 直写 → report 回读成功 → `arse` 现金列表 UI 命中 `SE690701-…` 金额 107.00 → 删清理(2026-07-01 · test01/TEST2019)。

---

## 13. 自建客户(master_customer · imparmas)· 2026-07-01 实测定型

- 端点:`imparmas` / idmenu 367 / **无 selmenu**(主数据导入 selmenu 发空串,别发 'None')· 回读列表 `armas/allview.php?idmenu=105`(需搜索关键词才出行)。
- 模板:官方 `test_data_mrerp_sample_customer.xlsx`(单 sheet · 25 列 · 克隆见 `services/erp/mrerp_xlsx_customer.py`)。
- **必填/校验(report Z=หมายเหตุ 列逐行给错)**:客户码(A,≥2)、类型(B,=4·`1-11`应收)、前缀(C,=`บริษัท`文本·填 '1' 报 ไม่พบข้อมูล)、名(D)、地址 1-4(E-H·空报 เป็นค่าว่าง→无数据填 '-')、**邮箱(K)必填且须合法格式**(空报 เป็นค่าว่าง·'-' 报格式非法→无则填合法占位)、科目码(M,`1130-03`应收)、联系前缀+名(N/O)、业务员(P,`กร`)、**销售区(Q)须恰 6 字符**(`สุพรรณ`·填 '0001' 4 字符被拒)、运输(R,`TRUCK1`)、分支(Y,`00000`)。
- 结构码来源:读现有客户 `armas/allform.php?id=<N>&status=edit` 的字段值(全合法)· 或各字段 onfocus `bshlistbox` 弹 `div[id*=listbox]` 选择器(Code/Name)。★结构码(科目/业务员/区域)**按套账不同**,生产须按套账注入。
- 成败判定:`importpc.php` 返 **`1`=全部成功**(无报告);返 `2`→拉 report 读 Z 备注列(空=成功·非空=该行错因)。注意 `mrerp_report_parser` 是发票口径,主数据判成败用 raw==1 或直读 Z 列。
- 端到端验证:HTTP 导入 raw=1 → armas 列表 UI 命中(PT… · ลูกหนี้การค้า · บริษัท · 名)→ 删(2026-07-01 · test01/TEST2019)。

---

## 14. 自建商品(master_product · impstkmas)· 2026-07-01 实测定型

- 端点:`impstkmas` / idmenu 353 / **无 selmenu** · 回读列表 `stkmas/allview.php?idmenu=24`(需搜索)。
- 模板:官方 `test_data_mrerp_sample_product.xlsx`(单 sheet · **29 列 A-AC** · 克隆见 `services/erp/mrerp_xlsx_product.py`)。
- 库存型(STKTYP=1)· **必填极多**(约 20 项):类型(A)/类目(B)/码(C)/名(D)/售价(I)/成本法(J)/4 单位(K/L/M/O)+ 每单位数量(N/P)/标准成本(Q)/寿命(R)/最小最大(S/T)/**8 个 GL 科目(U-AB:收入·退·折 / 采购·退·折 / 存货 / 成本)**/供应商(AC)。
- **★踩坑:类型/成本法认「短标签」非 select 值/全名**——类型只认 `จัดทำสต๊อค`(库存型 · 带前缀 `สินค้า : จัดทำสต๊อค` 或值 `1` 都报 ไม่พบข้อมูล);成本法认 `Average`(非 `1`)。同客户前缀(`บริษัท` 非 `1`)一个套路。
- 结构码照抄现有商品(如 P26050030):类目 `03-FIG` · 单位 `ผน` · 科目 `4110-01/4110-10/4110-20/5110-01/5110-11/5110-21/1150-30/5100-01` · 供应商占位 `CODE_NOAP`。★8 科目/类目**按套账不同**,生产须注入(`mappings["_mrerp_product_*"]`)。
- report:码在 **C 列**,备注在**末列(AD)** —— `_parse_master_report(code_col="C")`(客户是 A/Z)。importpc `1`=成功;`2`→读备注(空/已存在=成功)。
- 热路自动建:销项明细行对不上已有商品 → `autocreate.provision_products`(商品码=名 md5 · 确定性幂等)→ 建 → 注入 `mappings['products']`。
- 端到端验证:推带新买方+新商品的销项票 → 客户+商品都自动建 → 票落库 → armas/stkmas/artran 三处 UI 命中 → 删(2026-07-01 · test01/TEST2019)。

---

## 15. 采购(impaptran)+ 自建供应商(impapmas)· 2026-07-01 实测定型

**采购单(purchase · ซื้อสินค้า)**:
- 端点 `impaptran` / idmenu 363 / **selmenu=67**(ซื้อ)· 另有 453(ซื้อ-ค่าใช้จ่าย 费用采购)· 回读 aptran。
- 模板 `impaptran/example.xlsx`(官方 · **3-sheet**):**表头 16 列**(A单号/B日期/C税率/D分店5位/E部门/F工作/G员工/H交货日/**I供应商码**/J供应商票码/**K供应商票号**/L票日/M折扣/N-P备注)· **明细 8 列**(A单号/B商品码/C部门/D工作/E仓4位/F量/G单价/H金额)· **尾 3 列**(A单号/B押金号/C出库单 · 留空 = 不建收货/库存,库存归 S4)。
- 账套主体=**买方**;供应商(ผู้จำหน่าย)=采购票**卖方**。税率填 `7 (แยก)`(同现金票)· 分店 `00000` · 仓 `0000`。
- 生成器 `mrerp_xlsx_purchase.py`(克隆策略同 sales_cash · 该模板样式 表头 s13/文本 s7/日期 s14/数值 s9)。preflight 走独立最小校验 `validate_purchase_history`(日期+正额+供应商码 · **非** sales_credit 口径 · 后者查客户映射对采购不适用)。

**自建供应商(master_supplier · impapmas)**:
- 端点 `impapmas` / idmenu 359 / 无 selmenu · 回读 apmas。模板 `impapmas/example.xlsx`(单 sheet · **22 列**)。
- 必填结构码(row3 min-length 约束):**A码≥2 / B类型恰4字符 / M应付科目≥2 / V分店恰5字符**。邮箱(K)必填且须合法格式(同客户)。
- **★2026-07-01 实测默认值直接被接受**(无 report 报错):type=`2-21`(应付/贸易债权人)· account=`2110-01`(应付科目)· branch=`00000` · prefix=`บริษัท`。⚠️ type/account/branch 按套账不同,生产经 `mappings["_mrerp_supplier_*"]` 覆盖。
- 生成器 `mrerp_xlsx_supplier.py`(改自 customer · 该模板样式 表头 s6/文本 s7/数值 s10)· `adapter.create_suppliers`(idempotent · code_col="A")· `autocreate.provision_suppliers`(供应商码=卖方税号 · 确定性幂等 · 建成功注入 `mappings['suppliers']`)。
- 热路接线:`upload_invoice_batch` 采购分支 preflight 前 `provision_suppliers`;商品自建 `provision_products` 改为**销/采都走**。

**端到端验证(2026-07-01 · test01/TEST2019)**:推带新供应商+新商品的采购票 → 供应商(impapmas)+ 商品(impstkmas)自动建 → 采购票(impaptran)落库 690701-848469 → aptran 列表 UI 命中 · apmas/stkmas 命中(已清)。**★交易单(aptran)删除机制与主数据不同**(列表行删除链接非静态 `status=del` · 走 JS/AJAX)· 主数据(apmas/stkmas)仍走 `allform.php?id=N&status=del`+btndel。

**费用采购(purchase_expense · ซื้อ-ค่าใช้จ่าย · selmenu=453)· 2026-07-09 实测定型**:
- 与 67 共用 `impaptran`/363 五步 + 同一份 3-sheet 模板。回读 `aptran/allview.php?idmenu=453`(+showdata 搜索,实测可用)。展示层单据号自动加前缀 **PN**(67=PG)。ISO 日期服务器自动转佛历。完整生产路径 `upload_routed_batch` 三票混批 3/3 真落库(PNPGCC5F-1/2/3 · 321/150/85)。
- **★★alert("Error : ") 假成功的真正根因 = 缺 formupload GET 会话上下文(已修)**:老 PHP 要求会话先 GET 过目标模块的 `formupload.php?idmenu=N`(服务器 session 按「最后打开的 form」存导入上下文);`MrErpSession.prepare()` 幂等,provisioning(impapmas/impstkmas)先跑会吃掉首次导航 → 后续 impaptran 导入带错上下文 → importpc 炸 `alert("Error : ")` 空消息(67+自动建同会话同病)。修法:`adapter._upload_xlsx` 上传前显式 GET 本模块 formupload(一处覆盖主数据+交易全部导入)。⚠️ 早期「453 必须费用/服务型物料、库存商品不落库」的结论**是错的**(混淆变量污染)——补测 453+库存商品(03-FIG)+正确会话上下文 → raw='1' 真落库,**453 导入不强制物料类型**。
- **★假成功签名(第二道防线)**:importpc 返非数字体(alert/Error)时 report 备注列**全空**——逐行判会把整批误判成功。`_classify` 已诚实化:raw 非纯数字 → 整批 failed(`ERR_MRERP_IMPORT_ERROR` + raw 摘要)。
- 税率合法标签(aptran bshlistboxdata 实测):`0` / `7 (แยก)` / `7 (รวม)` / `นอกระบบ`(体系外 · 0% · 不进 VAT 报表)。
- **会计口径(拍板 · 与服务器强制无关)**:费用票无完整税票,进项 VAT 不可抵扣计入费用成本 → 税率 `นอกระบบ` · **单行** · 金额=**含税总额**(不逐行展开 items · 费用 GL 粒度来自物料科目)· 表头备注 1 留 items 名(人读线索)。通用费用物料建**费用/服务型**(type 短标签 `บริการ, ค่าใช้จ่าย` · 类目 `04-SER` · 8 个 GL 科目全费用科目,TEST2019 实测 5230-01 全链绿)——依据是费用过账走物料科目、不挂库存/销货成本,非 453 强制。实测 นอกระบบ+单行含税总额落库成功(PNPXN-11B2 · 321.00)。
- preflight `validate_expense_history`(日期+含税总额>0+供应商码 · **不跑 vat_rate_anomaly**——不抵扣就无所谓票面税率异常)。生成器 `generate_xlsx_purchase(..., expense=True)` · 通用费用物料自建见 `autocreate._provision_expense_item`(码默认 EXPENSE · 键 `_mrerp_expense_item_code/name/acc/category` 可覆盖)。

---

## 16. 库存进出(入库 impstktranrec / 出库 impstktraniss)· 2026-07-01 实测定型

- Zihao 定:库存只做**建库存型商品 + 进出库数量**,不算成本/COGS。
- **入库**:`impstktranrec` / idmenu 355 / **selmenu=28**(รับสินค้า)· 回读 stktranrec/idmenu 28。
- **出库**:`impstktraniss` / idmenu 356 / **selmenu=32**(จ่ายสินค้าเพื่อผลิต)· 回读 stktraniss/idmenu 32。
- 模板 `{path}/example.xlsx`(**2-sheet**):**表头 6 列**(A单号/B日期/C分店/D-F备注)· **明细**:入库 8 列(A单号/B商品码/C部门/D工作/E仓4位/F数量/**G单价/H金额**)· 出库 6 列(到 F数量止 · **无价额**)。
- 生成器 `mrerp_xlsx_stock.py`(入库/出库共用 · kind 控明细列 · 该模板样式 表头 s4/文本 s8/日期 s9/数值 s6)· 分店 `00000` · 仓 `0000`。preflight `validate_stock_history`(日期+至少一条可解析商品)· 商品自建(provision_products)对库存单也走。
- 端到端验证(2026-07-01 · test01/TEST2019):建库存商品 → 入库 **IR690701-017699** / 出库 **IS690701-784830** 落库(各 250)· **stktranrec/stktraniss 列表 UI 截图命中**。
- **★交易单删除机制(采购/库存单同)**:列表数据表**在 iframe 里靠 JS 渲染**,Del 是 JS 钮(非静态 `status=del` 链接)· Playwright 主帧/子帧 locator 均难稳定驱动 → 测试单留在授权测试账套 TEST2019(隔离·单号随机 id 派生不撞)。主数据(apmas/stkmas/armas)仍走 `allform.php?id=N&status=del`+btndel 可删。**待办(测试卫生)**:摸清交易单 iframe 数据端点/删除 JS,建 HTTP 删除助手清测试单。

---

## 17. 科目安全阀(account_valve)· 2026-07-01 · Zihao 定:匹配不上退回用户,不静默硬建

`services/erp/mrerp_http/account_valve.py`。两层:
- **反应层(工作即生效)**:MR.ERP 导入 report 报科目未匹配(泰文含"บัญชี/รหัสบัญชี"+"ไม่พบ/ไม่ถูกต้อง")时,`tag_account_review` 把该失败置顶归为 **`ERR_ACCOUNT_NEEDS_REVIEW`**(接进 `_classify`)→ 友好文案(四语·见 mrerp_business_friendly)提示"为该套账配置正确科目码,系统不自动建科目"。
- **主动层(提供科目表才启用·像 own_tax 闸)**:调用方把该套账科目表放 `mappings['_mrerp_accounts']` 后,`account_gate` 校验配置的科目码覆盖(`_mrerp_*acc*` 键值)都在表内,不在→推前全挡下退回(`upload_invoice_batch` 里·先于自建/preflight/任何网络)。未提供科目表 → 休眠不误挡。
- **⚠️ 科目表拉取协议未打通**:科目选择器走 `{path}/component/bshlistboxdata.php`(POST · JS 驱动),POST 参数没抓全 → **主动层现休眠**,靠反应层兜底。**待办**:抓通 bshlistboxdata POST 参数 → 拉该套账科目表填 `_mrerp_accounts` → 主动层生效(前门/推送路由接)。
- 决策依据:Zihao 明确"科目匹配现有则用,匹配不上退回用户兜底,不静默硬建"——**科目是唯一不自建的主数据**(客户/供应商/商品都自建)。
