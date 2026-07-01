# -*- coding: utf-8 -*-
"""
services/erp/mrerp_business_friendly.py

Friendly-message catalog for MR.ERP business failures.

Maps the patterns that show up in the report.php xlsx's `หมายเหตุ` column
(or in our own ERR_* codes coming out of validate_history_for_sales_credit)
to friendly, localized messages.

The catalog has two layers:
- ERR_* codes  : exact-string keys; cover everything our adapter can
                 emit before reaching MR.ERP (length checks, missing
                 customer mapping, etc.).
- Thai reasons : substring-match keys (case-insensitive). Lets us catch
                 the actual server-side rejections from MR.ERP even when
                 the report wording drifts a bit between releases.

P1-A §3.9 (Zihao 2026-05-18 拍板) — 4-language coverage:
    th     Thai      (primary; matches MR.ERP UI language)
    en     English   (international)
    zh     Simplified Chinese (mainland)
    zh_TW  Traditional Chinese (Taiwan/HK)

Deviation note: CLAUDE.md's standard 4-lang set is `zh/en/th/ja`. Zihao
explicitly substituted ja → zh_TW for this catalog because the failure-
message UI surface lives close to MR.ERP-side accountants where Taiwan
locale is more common than Japanese.

Lookup contract (`get_friendly(reason, lang='zh')`):
    - returns the lang string when found
    - falls back to English, then to the input reason
    - never returns None

Use `translate_reasons(reasons, lang)` for the common case of a whole
FailedRow.reasons list.
"""

from __future__ import annotations

from typing import Dict, List, Optional

SUPPORTED_LANGS = ("th", "en", "zh", "zh_TW")
DEFAULT_LANG = "zh"


# Adapter-side ERR codes — these never reach MR.ERP. Cover the validate
# pre-flight + the technical errors that show up in FailedRow.reasons.
_ERR_CATALOG: Dict[str, Dict[str, str]] = {
    "ERR_NO_HISTORY": {
        "th": "ไม่มีข้อมูลใบกำกับ",
        "en": "Invoice payload is empty",
        "zh": "发票数据为空",
        "zh_TW": "發票資料為空",
    },
    "ERR_NO_CLIENT": {
        # Bug 1 (Zihao 2026-05-19 拍板 · v118.34.22) · 把 "client_id 缺失" 这种技术词
        # 翻译成会计师能看懂的「请先在发票详情指定客户」· 同时告诉用户去哪 / 怎么修.
        "th": "ใบกำกับนี้ยังไม่ได้กำหนดลูกค้า Pearnly · กรุณาเปิดรายละเอียดใบกำกับและเลือกลูกค้าก่อน",
        "en": "This invoice has no Pearnly client assigned · open the invoice details and pick a client first",
        "zh": "这张发票还没分配 Pearnly 客户 · 请先在发票详情里指定客户",
        "zh_TW": "這張發票還沒分配 Pearnly 客戶 · 請先在發票詳情指定客戶",
    },
    "ERR_ENDPOINT_NO_CLIENTS": {
        # Bug 1 (v118.34.22) · POST/PATCH endpoint 时 client_ids 空数组的友好错.
        "th": "ยังไม่ได้เลือกลูกค้า Pearnly สำหรับการเชื่อม ERP · กรุณาเลือกลูกค้าอย่างน้อย 1 รายการในขั้นตอน 1 ของวิซาร์ด",
        "en": "No Pearnly clients are linked to this ERP connection · pick at least one client in wizard Step 1",
        "zh": "这个 ERP 连接还没绑任何 Pearnly 客户 · 请在向导第 1 步至少选 1 个客户",
        "zh_TW": "這個 ERP 連線還沒綁任何 Pearnly 客戶 · 請在精靈第 1 步至少選 1 個客戶",
    },
    "ERR_ACCOUNT_NEEDS_REVIEW": {
        # 科目安全阀(Zihao 定 · 匹配不上退回用户不硬建):科目码不在该套账科目表 → 让用户配置正确科目码。
        "th": "รหัสบัญชีไม่ตรงกับผังบัญชีของชุดบัญชีนี้ · กรุณาตั้งค่ารหัสบัญชีที่ถูกต้องสำหรับชุดบัญชีนี้ (ระบบไม่สร้างบัญชีให้อัตโนมัติ)",
        "en": "Account code not found in this account-set's chart · please configure the correct account codes for this account-set (accounts are not auto-created)",
        "zh": "科目码不在该套账的科目表里 · 请为该套账配置正确的科目码(系统不会自动新建科目)",
        "zh_TW": "科目碼不在該套帳的科目表裡 · 請為該套帳配置正確的科目碼(系統不會自動新建科目)",
    },
    "ERR_NO_CUSTOMER_MAPPING": {
        # 问题 b (Zihao 2026-05-19 拍板 · v118.34.26) · action-oriented:
        # 告诉用户去哪里配 mapping · 或者开 wizard 种子客户开自动建.
        "th": "ลูกค้านี้ยังไม่มีรหัสลูกค้า MR.ERP ที่ตรงกัน · กรุณาเปิดวิซาร์ดเชื่อม MR.ERP เลือก ลูกค้าต้นแบบ (เปิดสร้างอัตโนมัติ) · หรือไปที่ การตั้งค่า ERP เพื่อเพิ่มการแมปด้วยตนเอง",
        "en": "This client has no matching MR.ERP customer code · open the MR.ERP wizard and pick a seed customer (enables auto-create), or go to ERP settings to add the mapping manually",
        "zh": "这个客户在 MR.ERP 里还没对应客户码 · 请打开 MR.ERP 连接向导选「种子客户」(开自动建) · 或去 ERP 设置手动加映射",
        "zh_TW": "這個客戶在 MR.ERP 裡還沒對應客戶碼 · 請打開 MR.ERP 連線精靈選「種子客戶」(開自動建立) · 或去 ERP 設定手動加對應",
    },
    # Fail-safe name verification (Zihao 2026-05-26 拍板 · P1)
    # 复用 code 后反查 MR.ERP 真名复核 · 不匹配/无法确认都阻断 · 不再静默错推。
    "ERR_CUSTOMER_NAME_MISMATCH": {
        "th": "ระบบตรวจสอบพบว่ารหัสลูกค้าที่จะส่งไป MR.ERP ตรงกับลูกค้าคนละรายกับผู้ซื้อในใบกำกับ · หยุดส่งเพื่อกันบันทึกผิดลูกค้า · กรุณาแก้ไขการแมปลูกค้าในการตั้งค่า ERP แล้วส่งใหม่",
        "en": "Verification found the customer code about to be pushed maps to a different MR.ERP customer than this invoice's buyer · push stopped to avoid recording against the wrong customer · fix the customer mapping in ERP settings and retry",
        "zh": "复核发现要推送的客户码在 MR.ERP 对应的是另一个客户 · 跟这张发票的买方不一致 · 为防记到错客户已停止推送 · 请到 ERP 设置更正客户映射后重推",
        "zh_TW": "複核發現要推送的客戶碼在 MR.ERP 對應的是另一個客戶 · 跟這張發票的買方不一致 · 為防記到錯客戶已停止推送 · 請到 ERP 設定更正客戶對應後重推",
    },
    "ERR_CUSTOMER_VERIFY_UNAVAILABLE": {
        "th": "ยังยืนยันกับ MR.ERP ไม่ได้ว่าลูกค้าตรงกันหรือไม่ (เครือข่าย/หมดเวลา) · ยังไม่ได้ส่งเพื่อความปลอดภัย · ระบบจะลองใหม่อัตโนมัติ",
        "en": "Could not confirm with MR.ERP whether the customer matches (network/timeout) · not pushed for safety · will retry automatically",
        "zh": "暂时无法向 MR.ERP 确认客户是否匹配(网络/超时)· 为安全起见尚未推送 · 系统会自动重试",
        "zh_TW": "暫時無法向 MR.ERP 確認客戶是否相符(網路/逾時)· 為安全起見尚未推送 · 系統會自動重試",
    },
    "ERR_NO_INVOICE_NO": {
        "th": "เลขที่ใบกำกับว่าง",
        "en": "Invoice number is empty",
        "zh": "发票号为空",
        "zh_TW": "發票號為空",
    },
    "ERR_NO_INVOICE_DATE": {
        "th": "วันที่ใบกำกับว่าง",
        "en": "Invoice date is empty",
        "zh": "发票日期为空",
        "zh_TW": "發票日期為空",
    },
    "ERR_NO_TOTAL_AMOUNT": {
        "th": "ยอดรวมว่างหรือเท่ากับ 0",
        "en": "Total amount missing or zero",
        "zh": "总金额为空或为 0",
        "zh_TW": "總金額為空或為 0",
    },
    "ERR_NEGATIVE_AMOUNT": {
        "th": "ยอดรวมติดลบ ห้ามใช้กับใบกำกับขาย",
        "en": "Negative total amount — sales_credit upload requires "
        "positive total (use a credit note workflow instead)",
        "zh": "总金额为负 · 销项发票不允许(请走红字发票流程)",
        "zh_TW": "總金額為負 · 銷項發票不允許(請走紅字發票流程)",
    },
    "ERR_INVOICE_NO_TOO_LONG": {
        "th": "เลขที่ใบกำกับยาวเกิน 18 ตัวอักษร (ตัดอัตโนมัติแล้ว)",
        "en": "Invoice number exceeds 18 chars (auto-rejected before upload)",
        "zh": "发票号超过 18 字符 · 已在上传前自动拦截",
        "zh_TW": "發票號超過 18 字元 · 已在上傳前自動攔截",
    },
    "ERR_BILL_NO_TOO_LONG": {
        "th": "เลขที่บิล (SI + เลขที่) ยาวเกิน 20 ตัวอักษร",
        "en": "Bill number (SI + invoice_no) exceeds 20 chars",
        "zh": "账单号(SI + 发票号)超过 20 字符",
        "zh_TW": "帳單號(SI + 發票號)超過 20 字元",
    },
    "ERR_CUSTOMER_CODE_TOO_LONG": {
        "th": "รหัสลูกค้ายาวเกิน 20 ตัวอักษร",
        "en": "Customer code exceeds 20 chars",
        "zh": "客户码超过 20 字符",
        "zh_TW": "客戶碼超過 20 字元",
    },
    "ERR_CUSTOMER_BILL_TOO_LONG": {
        "th": "รหัสลูกค้า (บิล) ยาวเกิน 20 ตัวอักษร",
        "en": "Customer billing code exceeds 20 chars",
        "zh": "客户账单码超过 20 字符",
        "zh_TW": "客戶帳單碼超過 20 字元",
    },
    "ERR_TAX_RATE_INVALID": {
        "th": "อัตราภาษีไม่อยู่ในรายการที่อนุญาต",
        "en": "Tax rate is not in the allowed set " "{vat_7, vat_0, vat_exempt, non_vat}",
        "zh": "税率不在允许枚举内(vat_7 / vat_0 / vat_exempt / non_vat)",
        "zh_TW": "稅率不在允許列舉內(vat_7 / vat_0 / vat_exempt / non_vat)",
    },
    "ERR_DATE_FUTURE": {
        "th": "วันที่ใบกำกับเลย 30 วันในอนาคต ห้ามอัปโหลด",
        "en": "Invoice date is more than 30 days in the future — upload blocked",
        "zh": "发票日期超过 30 天未来 · 拒绝上传",
        "zh_TW": "發票日期超過 30 天未來 · 拒絕上傳",
    },
    "WARN_DATE_NEAR_FUTURE": {
        "th": "วันที่ใบกำกับเกิน 7 วันในอนาคต — โปรดยืนยัน",
        "en": "Invoice date is more than 7 days in the future — please confirm",
        "zh": "发票日期超过 7 天未来 · 请确认",
        "zh_TW": "發票日期超過 7 天未來 · 請確認",
    },
    "WARN_DATE_TOO_OLD": {
        "th": "วันที่ใบกำกับเก่ากว่า 2 ปี — โปรดยืนยัน",
        "en": "Invoice date is more than 2 years old — please confirm",
        "zh": "发票日期超过 2 年 · 请确认",
        "zh_TW": "發票日期超過 2 年 · 請確認",
    },
    "ERR_NO_SEED_CUSTOMER": {
        "th": "ต้องเลือกลูกค้าต้นแบบในวิซาร์ดเชื่อม ERP ก่อนสร้างลูกค้าใหม่อัตโนมัติ",
        "en": "Auto-create needs a seed customer. Pick one in the ERP " "connection wizard.",
        "zh": "自动建客户需先选模板 · 请到 ERP 连接向导挑一个种子客户",
        "zh_TW": "自動建立客戶需先選範本 · 請到 ERP 連線精靈挑一個種子客戶",
    },
    "ERR_SEED_NOT_FOUND": {
        "th": "ไม่พบลูกค้าต้นแบบในระบบ MR.ERP — ตรวจสอบรหัสและเลือกใหม่",
        "en": "Seed customer not found in MR.ERP — verify the code and " "reselect.",
        "zh": "MR.ERP 里没找到所选种子客户 · 请核对客户码并重新选择",
        "zh_TW": "MR.ERP 裡沒找到所選種子客戶 · 請核對客戶碼並重新選擇",
    },
    # Connection-test buckets (C-1 wizard health-check path)
    "ERR_NO_CREDS": {
        "th": "ยังไม่ตั้งชื่อผู้ใช้ / รหัสผ่าน MR.ERP",
        "en": "MR.ERP username / password not configured",
        "zh": "尚未填 MR.ERP 用户名 / 密码",
        "zh_TW": "尚未填 MR.ERP 使用者名稱 / 密碼",
    },
    "ERR_CRED_DECRYPT": {
        "th": "ถอดรหัสรหัสผ่านที่บันทึกไว้ไม่ได้ — กรอกใหม่",
        "en": "Stored credentials failed to decrypt — please re-enter them",
        "zh": "保存的凭据无法解密 · 请重填一次",
        "zh_TW": "儲存的憑證無法解密 · 請重填一次",
    },
    "ERR_AUTH": {
        "th": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง — โปรดตรวจสอบ",
        "en": "MR.ERP login bounced — verify the username and password",
        "zh": "MR.ERP 登录被拒 · 用户名或密码错 · 请核对",
        "zh_TW": "MR.ERP 登入被拒 · 使用者名稱或密碼錯 · 請核對",
    },
    "ERR_TECHNICAL": {
        "th": "เครือข่ายหรือ MR.ERP ขัดข้องชั่วคราว — ลองอีกครั้ง",
        "en": "Network or MR.ERP outage. Try again in a minute.",
        "zh": "网络或 MR.ERP 暂时不可用 · 稍等再试",
        "zh_TW": "網路或 MR.ERP 暫時不可用 · 稍等再試",
    },
    "ERR_BUSINESS": {
        "th": "MR.ERP ตอบกลับด้วยข้อผิดพลาด — ดูรายละเอียดเพิ่มเติม",
        "en": "MR.ERP returned a business error — check details below",
        "zh": "MR.ERP 返业务错误 · 查看下方详情",
        "zh_TW": "MR.ERP 返業務錯誤 · 查看下方詳情",
    },
    "ERR_UNEXPECTED": {
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิด — แจ้งทีมงาน",
        "en": "Unexpected error — please contact support",
        "zh": "意外错误 · 请联系客服",
        "zh_TW": "意外錯誤 · 請聯絡客服",
    },
    # Product-sync buckets (Task 2 · Zihao 2026-05-18 拍板)
    "ERR_NO_SEED_PRODUCT": {
        "th": "ต้องเลือกสินค้าต้นแบบในวิซาร์ดเชื่อม ERP ก่อนสร้างสินค้าใหม่อัตโนมัติ",
        "en": "Auto-create needs a seed product. Pick one in the ERP " "connection wizard.",
        "zh": "自动建商品需先选模板 · 请到 ERP 连接向导挑一个种子商品",
        "zh_TW": "自動建立商品需先選範本 · 請到 ERP 連線精靈挑一個種子商品",
    },
    "ERR_SEED_PRODUCT_NOT_FOUND": {
        "th": "ไม่พบสินค้าต้นแบบในระบบ MR.ERP — ตรวจสอบรหัสและเลือกใหม่",
        "en": "Seed product not found in MR.ERP — verify the code and " "reselect.",
        "zh": "MR.ERP 里没找到所选种子商品 · 请核对商品码并重新选择",
        "zh_TW": "MR.ERP 裡沒找到所選種子商品 · 請核對商品碼並重新選擇",
    },
    "ERR_PRODUCT_UNIT_NOT_FOUND": {
        "th": "หน่วย OCR ไม่ตรงกับหน่วยของสินค้าต้นแบบ — เปลี่ยนต้นแบบ" "หรือเอา hint หน่วยออก",
        "en": "OCR unit does not match the seed product's unit — pick "
        "a seed with the right unit or drop the OCR unit hint",
        "zh": "OCR 单位与种子商品单位不符 · 换个种子或删去 OCR 单位提示",
        "zh_TW": "OCR 單位與種子商品單位不符 · 換個種子或刪去 OCR 單位提示",
    },
    # Fail-safe name verification (Zihao 2026-05-26 拍板 · P1)
    "ERR_PRODUCT_NAME_MISMATCH": {
        "th": "ระบบตรวจสอบพบว่ารหัสสินค้าที่จะส่งไป MR.ERP ตรงกับสินค้าคนละรายการกับในใบกำกับ (หรือยังเป็นสินค้าตัวอย่าง) · หยุดส่งเพื่อกันบันทึกผิดสินค้า · กรุณาแก้ไขการแมปสินค้าในการตั้งค่า ERP แล้วส่งใหม่",
        "en": "Verification found the product code about to be pushed maps to a different MR.ERP product than this invoice line (or is still a placeholder product) · push stopped to avoid recording the wrong item · fix the product mapping in ERP settings and retry",
        "zh": "复核发现要推送的商品码在 MR.ERP 对应的是另一个商品 · 跟发票上的商品不一致(或仍是占位商品)· 为防记错商品已停止推送 · 请到 ERP 设置更正商品映射后重推",
        "zh_TW": "複核發現要推送的商品碼在 MR.ERP 對應的是另一個商品 · 跟發票上的商品不一致(或仍是佔位商品)· 為防記錯商品已停止推送 · 請到 ERP 設定更正商品對應後重推",
    },
    "ERR_PRODUCT_VERIFY_UNAVAILABLE": {
        "th": "ยังยืนยันกับ MR.ERP ไม่ได้ว่าสินค้าตรงกันหรือไม่ (เครือข่าย/หมดเวลา) · ยังไม่ได้ส่งเพื่อความปลอดภัย · ระบบจะลองใหม่อัตโนมัติ",
        "en": "Could not confirm with MR.ERP whether the product matches (network/timeout) · not pushed for safety · will retry automatically",
        "zh": "暂时无法向 MR.ERP 确认商品是否匹配(网络/超时)· 为安全起见尚未推送 · 系统会自动重试",
        "zh_TW": "暫時無法向 MR.ERP 確認商品是否相符(網路/逾時)· 為安全起見尚未推送 · 系統會自動重試",
    },
    "WARN_PRODUCT_NAME_TRUNCATED": {
        "th": "ชื่อสินค้ายาวเกิน 100 ตัวอักษร — ถูกตัดให้พอดี",
        "en": "Product name exceeded 100 chars — truncated to fit",
        "zh": "商品名超过 100 字符 · 已自动截断",
        "zh_TW": "商品名超過 100 字元 · 已自動截斷",
    },
    "WARN_PRODUCT_PRICE_INHERITED_FROM_SEED": {
        "th": "ราคาขายสืบทอดจากสินค้าต้นแบบ — โปรดตรวจสอบในระบบ MR.ERP",
        "en": "Sales price inherited from the seed product — please " "review in MR.ERP",
        "zh": "销售价继承自种子商品 · 请到 MR.ERP 核对",
        "zh_TW": "銷售價繼承自種子商品 · 請到 MR.ERP 核對",
    },
}


# Substring patterns that show up verbatim in MR.ERP's report.php xlsx
# หมายเหตุ column. Match is case-insensitive containment so we catch
# minor wording drift between MR.ERP versions.
_THAI_REASON_CATALOG: List[tuple] = [
    (
        "ไม่พบข้อมูลรหัสลูกค้า (บิล)",
        {
            "th": "ไม่พบรหัสลูกค้า (บิล) ในระบบ — สร้างลูกค้าก่อน",
            "en": "Customer billing code not found in MR.ERP master data — "
            "create the customer first",
            "zh": "MR.ERP 主数据找不到客户账单码 · 需先创建客户",
            "zh_TW": "MR.ERP 主資料找不到客戶帳單碼 · 需先建立客戶",
        },
    ),
    (
        "ไม่พบข้อมูลรหัสลูกค้า",
        {
            "th": "ไม่พบรหัสลูกค้าในระบบ — สร้างลูกค้าก่อน",
            "en": "Customer code not found in MR.ERP master data — " "create the customer first",
            "zh": "MR.ERP 主数据找不到客户码 · 需先创建客户",
            "zh_TW": "MR.ERP 主資料找不到客戶碼 · 需先建立客戶",
        },
    ),
    (
        "ไม่พบข้อมูลรหัสสินค้า",
        {
            "th": "ไม่พบรหัสสินค้าในระบบ — สร้างสินค้าก่อน",
            "en": "Product code not found in MR.ERP master data — " "create the product first",
            "zh": "MR.ERP 主数据找不到商品码 · 需先创建商品",
            "zh_TW": "MR.ERP 主資料找不到商品碼 · 需先建立商品",
        },
    ),
    (
        "ไม่พบข้อมูลพนักงานขาย",
        {
            "th": "ไม่พบพนักงานขายในระบบ",
            "en": "Salesman not found in MR.ERP master data",
            "zh": "MR.ERP 主数据找不到销售员",
            "zh_TW": "MR.ERP 主資料找不到業務員",
        },
    ),
    (
        "เลขที่เอกสารซ้ำ",
        {
            # 问题 1 (Zihao 2026-05-19 拍板 · v118.34.24) · 文案改人话 + 行动指引.
            # 旧文案: "发票号与 MR.ERP 已有记录重复" — 干 · 不知道下一步.
            # 新文案: 解释 + 告诉用户去 MR.ERP 后台编辑.
            "th": "ใบกำกับนี้เคยส่งเข้า MR.ERP แล้ว · ส่งซ้ำไม่ได้ · หากต้องการแก้ไข กรุณาเปิด MR.ERP แล้วแก้รายการนี้โดยตรง",
            "en": "This invoice was already pushed to MR.ERP previously · duplicates aren't allowed · to update, open MR.ERP and edit the bill directly",
            "zh": "这张发票之前已经推送过 MR.ERP 了 · 不能重复推 · 如需更新请去 MR.ERP 后台直接编辑这张单据",
            "zh_TW": "這張發票之前已經推送過 MR.ERP 了 · 不能重複推 · 如需更新請去 MR.ERP 後台直接編輯這張單據",
        },
    ),
    (
        "เลขที่ดังกล่าวมีอยู่ในระบบแล้ว",
        {
            # 同 "เลขที่เอกสารซ้ำ" 处理 · MR.ERP 两种文案 · 用户面行动指引一致.
            "th": "ใบกำกับนี้เคยส่งเข้า MR.ERP แล้ว · ส่งซ้ำไม่ได้ · หากต้องการแก้ไข กรุณาเปิด MR.ERP แล้วแก้รายการนี้โดยตรง",
            "en": "This invoice was already pushed to MR.ERP previously · duplicates aren't allowed · to update, open MR.ERP and edit the bill directly",
            "zh": "这张发票之前已经推送过 MR.ERP 了 · 不能重复推 · 如需更新请去 MR.ERP 后台直接编辑这张单据",
            "zh_TW": "這張發票之前已經推送過 MR.ERP 了 · 不能重複推 · 如需更新請去 MR.ERP 後台直接編輯這張單據",
        },
    ),
    (
        "เลขที่ต้องไม่เกิน 18 ตัวอักษร",
        {
            "th": "เลขที่ใบกำกับยาวเกิน 18 ตัวอักษร",
            "en": "Invoice number exceeds the 18-character limit",
            "zh": "发票号超过 18 字符限制",
            "zh_TW": "發票號超過 18 字元限制",
        },
    ),
    (
        "เลขที่บิลต้องไม่เกิน 20 ตัวอักษร",
        {
            "th": "เลขที่บิลยาวเกิน 20 ตัวอักษร",
            "en": "Bill number exceeds the 20-character limit",
            "zh": "账单号超过 20 字符限制",
            "zh_TW": "帳單號超過 20 字元限制",
        },
    ),
    (
        "รหัสลูกค้า (บิล) ต้องไม่เกิน 20 ตัวอักษร",
        {
            "th": "รหัสลูกค้า (บิล) ยาวเกิน 20 ตัวอักษร",
            "en": "Customer billing code exceeds the 20-character limit",
            "zh": "客户账单码超过 20 字符限制",
            "zh_TW": "客戶帳單碼超過 20 字元限制",
        },
    ),
    (
        "รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร",
        {
            "th": "รหัสลูกค้ายาวเกิน 20 ตัวอักษร",
            "en": "Customer code exceeds the 20-character limit",
            "zh": "客户码超过 20 字符限制",
            "zh_TW": "客戶碼超過 20 字元限制",
        },
    ),
]


def get_friendly(
    reason: Optional[str],
    lang: str = DEFAULT_LANG,
) -> Dict[str, str]:
    """Translate one rejection reason into all 4 supported languages.

    Returns a dict containing every supported language. If no catalog
    entry matches, returns a dict where every language falls back to
    the raw `reason` string (so callers always get a printable value).

    `lang` selects which key is treated as primary (used by callers that
    want a single-string fallback), but the full dict is returned either
    way so the UI can offer "show original" toggles.
    """
    if not reason:
        return {k: "" for k in SUPPORTED_LANGS}

    # Exact match on ERR_* codes first (cheap, deterministic).
    if reason in _ERR_CATALOG:
        return dict(_ERR_CATALOG[reason])

    # Substring match for Thai reasons coming from report.php.
    low = reason.strip().lower()
    for pattern, translations in _THAI_REASON_CATALOG:
        if pattern.lower() in low:
            return dict(translations)

    # Unknown — echo the raw reason in every language. The UI can render
    # it verbatim; the user at least sees something honest.
    return {k: reason for k in SUPPORTED_LANGS}


def translate_reasons(
    reasons: List[str],
    lang: str = DEFAULT_LANG,
) -> List[Dict[str, str]]:
    """Apply get_friendly to a whole list (typically FailedRow.reasons).

    Returns a parallel list of {lang -> text} dicts.
    """
    return [get_friendly(r, lang=lang) for r in (reasons or [])]


def primary_friendly(
    reason: Optional[str],
    lang: str = DEFAULT_LANG,
) -> str:
    """Convenience: one string in the caller's chosen language, falling
    back gracefully to English then to the raw text."""
    translations = get_friendly(reason, lang=lang)
    if lang in translations and translations[lang]:
        return translations[lang]
    return translations.get("en") or (reason or "")


# Pearnly 前端主 UI 的 4 语集(home.js currentLang)· 注意是 ja 不是 zh_TW。
# catalog 历史按 th/en/zh/zh_TW 编(失败信息界面靠近台湾会计师 · 见模块头注释),
# 这里把它映射到主 UI 的 zh/th/en/ja:ja 无目录条目 → 退英文(国际兜底)。
APP_UI_LANGS = ("zh", "th", "en", "ja")


def _match_catalog(reason: str) -> Optional[Dict[str, str]]:
    """命中则返回 catalog 原始 dict(th/en/zh/zh_TW),否则 None。"""
    if reason in _ERR_CATALOG:
        return _ERR_CATALOG[reason]
    low = reason.strip().lower()
    for pattern, translations in _THAI_REASON_CATALOG:
        if pattern.lower() in low:
            return translations
    return None


def friendly_for_ui(reason: Optional[str]) -> Optional[Dict[str, str]]:
    """P2-C (Zihao 2026-05-27) · 给前端日志/异常渲染用的友好文案 4 语 dict。

    返回 {zh, th, en, ja}(主 UI 语言集),**仅当 reason 命中 catalog 时**;
    未命中返回 None → 调用方(前端)回退自己的 humanizeError(处理网络错误)/ 原文,
    避免把 raw 泰文/ERR 码直接展示给中日英用户(B7「不裸透泰文」)。

    ja 无 catalog 条目 → 退 en(国际兜底);任何语言缺失 → 退 en → 退 raw reason。
    """
    if not reason:
        return None
    matched = _match_catalog(reason)
    if matched is None:
        return None
    en = matched.get("en") or reason
    return {
        "zh": matched.get("zh") or en,
        "th": matched.get("th") or en,
        "en": en,
        "ja": en,  # 无日语目录 → 英文兜底(文档化偏差)
    }
