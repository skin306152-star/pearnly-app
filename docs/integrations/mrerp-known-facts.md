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

### Step 4 · 确认导入(真写库)
```
POST https://www.mrerp4sme.com/impartran/component/importpc.php
Content-Type: multipart/form-data
Referer: https://www.mrerp4sme.com/impartran/formrdpc.php
X-Requested-With: XMLHttpRequest
```

multipart 字段:
- `idus` = ...
- `selmenu` = `118`
- `cballfrmimport1` = `on`(表示全选)
- `cbimport[N]` = `N`(每个要导入的 row 一项 · 数组形式)

**响应**:成功 = `200 + 短字符串`(实测 `"2"` · 推测是导入条数或最后 row_id)· 非纯数字 = 业务错误

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
- 字符串走 `sharedStrings.xml` · **不能用 inlineStr**(PhpSpreadsheet 不识别)
- 数值 cell **不带 `t="n"` 属性**(Korn 真样本 default 是 numeric · 加 t 反而异常)
- 每行加 `spans="1:N"` 属性
- 日期单元格 number_format = `@`(强制文本)

⚠️ **2026-05-18 Playwright 实测发现先验冲突**:
- 历史反向工程说"缺失 cell 补**完全空 cell** `<c r="X#"/>`(让 row 显式声明每列存在)"
- 但实际上传被拒 · MR.ERP 报错:`จำนวนคอลัมภ์ข้อมูลไม่ครบ 18 คอลัมภ์`(数据列数不到 18 列)
- 字节级抽样显示我们 row 2 = 14 string cell + 1 数值 cell + **3 完全空 P/Q/R** + 1 spacer S = 19 cell · MR.ERP 视角"有效列" = 15 · 拒
- **假设**:MR.ERP 数 `<v>` 子节点 cell 数 · 完全空 `<c/>` 不算
- **下一步排查**(尚未确认):
  - Korn 真样本 P/Q/R 是不是带空 `<v>`(`<c><v></v></c>` 或引用空 sharedString `<c t="s"><v>N</v></c>` N→"")
  - 或者 schema note1/2/3 实际可以填占位字符(如空格 " ")让 generator 产生 string cell
- **解决前禁止上传** · 不要硬猜规则改 generator(可能引入更深的字节差异)

---

## 7. 字段格式规则

### invoice_no 格式 · YYMMDD-NNN(BE 年)
Korn 真样本:`690507-001`
- `69` = 佛历年末 2 位 = 西历年 + 543 → 取末 2 位(2026 → 2569 → `69`)
- `0507` = 月日
- `-001` = 服务端再分配的序号

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

## 11. 历史窗口产出参考

抓包窗口产出的代码已按"事实归 docs / 不留废代码"铁律删除 · 仅本文档作为先验留存。如需深度回溯历史 cURL / 字节序列实测过程 · 见:
- `CLAUDE.md/STATE_PEARNLY.md` § "🔌 MR.ERP 反向工程结果"
- `CLAUDE.md/BACKLOG.md` § v27.8.0 ~ v27.8.1.x
- `docs/cleanup/round1-final-report.md`

xlsx 生成器仍保留(`mrerp_xlsx_generator.py`)· Playwright 方案上传同一文件格式 · 不需要重写。
