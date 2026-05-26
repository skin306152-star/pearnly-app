/**
 * static/erp-mrerp-connect.js
 *
 * C-2 + C-3 + C-4 (Zihao 2026-05-18 拍板).
 *
 * Adds MR.ERP / FlowAccount cards into #erp-connect-cards (alongside
 * the existing Xero card IIFE) + the 3-step connect wizard modal +
 * the sidebar push-log scaffold.
 *
 * Self-contained:
 *   - Does NOT touch home.js translations dict. All i18n lives in a
 *     local `T` map below.
 *   - Does NOT modify any existing #endpoint-modal / #btn-add-endpoint
 *     logic (those die in C-6 once the legacy webhook flow is
 *     deprecated).
 *
 * 4-lang i18n: th / en / zh / zh_TW (Zihao swapped ja → zh_TW for the
 * MR.ERP-adjacent surface — see services/erp/mrerp_business_friendly.py
 * docstring). Falls back to en when the active lang has no entry, then
 * to the key itself.
 */
(function () {
    'use strict';

    // ─────────────────────────────────────────────────────────────
    // Local i18n (does NOT touch home.js translations)
    // ─────────────────────────────────────────────────────────────
    const T = {
        // Card labels
        'mrerp-card-name': {
            zh: 'MR.ERP',
            en: 'MR.ERP',
            th: 'MR.ERP',
            zh_TW: 'MR.ERP',
            ja: 'MR.ERP',
        },
        'flow-card-name': {
            zh: 'FlowAccount',
            en: 'FlowAccount',
            th: 'FlowAccount',
            zh_TW: 'FlowAccount',
            ja: 'FlowAccount',
        },
        'card-coming-soon': {
            zh: '即将上线',
            en: 'Coming soon',
            th: 'เร็วๆ นี้',
            zh_TW: '即將上線',
            ja: '近日公開',
        },
        'card-not-configured': {
            zh: '未连接',
            en: 'Not connected',
            th: 'ยังไม่เชื่อม',
            zh_TW: '未連接',
            ja: '未接続',
        },
        'card-connected': {
            zh: '已连接',
            en: 'Connected',
            th: 'เชื่อมแล้ว',
            zh_TW: '已連接',
            ja: '接続済み',
        },
        'card-checking': {
            zh: '检查中…',
            en: 'Checking…',
            th: 'กำลังตรวจสอบ…',
            zh_TW: '檢查中…',
            ja: '確認中…',
        },
        'card-needs-attention': {
            zh: '需关注',
            en: 'Needs attention',
            th: 'ต้องตรวจสอบ',
            zh_TW: '需關注',
            ja: '要確認',
        },
        'card-btn-connect': {
            zh: '连接',
            en: 'Connect',
            th: 'เชื่อมต่อ',
            zh_TW: '連接',
            ja: '接続',
        },
        'card-btn-edit': {
            zh: '修改',
            en: 'Edit',
            th: 'แก้ไข',
            zh_TW: '修改',
            ja: '編集',
        },
        'card-btn-retest': {
            zh: '重新测试',
            en: 'Re-test',
            th: 'ทดสอบใหม่',
            zh_TW: '重新測試',
            ja: '再テスト',
        },
        'card-stat-last-push': {
            zh: '上次推送',
            en: 'Last push',
            th: 'ส่งล่าสุด',
            zh_TW: '上次推送',
            ja: '最終送信',
        },
        'card-stat-month-pushed': {
            zh: '本月已推',
            en: 'This month',
            th: 'เดือนนี้',
            zh_TW: '本月已推',
            ja: '今月',
        },
        'card-stat-month-failed': {
            zh: '失败',
            en: 'Failures',
            th: 'ล้มเหลว',
            zh_TW: '失敗',
            ja: '失敗',
        },
        'card-stat-mode-auto': {
            zh: '自动推送',
            en: 'Auto push',
            th: 'ส่งอัตโนมัติ',
            zh_TW: '自動推送',
            ja: '自動送信',
        },
        'card-stat-mode-manual': {
            zh: '手动推送',
            en: 'Manual push',
            th: 'ส่งด้วยตนเอง',
            zh_TW: '手動推送',
            ja: '手動送信',
        },
        'card-stat-mode-none': {
            zh: '未配置',
            en: 'Not set',
            th: 'ยังไม่ตั้งค่า',
            zh_TW: '未設定',
            ja: '未設定',
        },
        // Empty state
        'empty-banner-title': {
            zh: '还没有连接任何 ERP · 点上面的卡片开始连接',
            en: 'No ERP connected yet — pick a card above to connect',
            th: 'ยังไม่ได้เชื่อม ERP — เลือกการ์ดด้านบนเพื่อเริ่ม',
            zh_TW: '尚未連接任何 ERP · 點上面的卡片開始連接',
            ja: 'まだ ERP に接続していません · 上のカードから接続を開始',
        },
        'empty-banner-hint': {
            zh: '推送是自动的 · 设置一次,日常使用不再来这页',
            en: "Pushes are automatic — set up once and you won't need to come back",
            th: 'การส่งเป็นอัตโนมัติ — ตั้งครั้งเดียวก็ใช้งานต่อได้เลย',
            zh_TW: '推送是自動的 · 設定一次,日常使用不再來這頁',
            ja: '送信は自動 · 一度設定すれば、戻る必要はありません',
        },
        // Wizard
        'wiz-title-connect': {
            zh: '连接 MR.ERP',
            en: 'Connect MR.ERP',
            th: 'เชื่อมต่อ MR.ERP',
            zh_TW: '連接 MR.ERP',
            ja: 'MR.ERP に接続',
        },
        'wiz-step-1-h': {
            zh: '这个连接用于哪些客户?',
            en: 'Which Pearnly clients does this connection cover?',
            th: 'การเชื่อมต่อนี้ครอบคลุมลูกค้าใดบ้าง?',
            zh_TW: '此連線適用於哪些客戶?',
            ja: 'この接続はどの取引先をカバーしますか?',
        },
        'wiz-step-1-hint': {
            zh: '这些客户的发票将被推送到 MR.ERP',
            en: 'Invoices for these clients will be pushed to MR.ERP',
            th: 'ใบกำกับของลูกค้าเหล่านี้จะถูกส่งไป MR.ERP',
            zh_TW: '這些客戶的發票將被推送到 MR.ERP',
            ja: 'これらの取引先の請求書を MR.ERP に送信します',
        },
        'wiz-step-1-select-all': {
            zh: '全选',
            en: 'Select all',
            th: 'เลือกทั้งหมด',
            zh_TW: '全選',
            ja: 'すべて選択',
        },
        // Bug 1 (Zihao 2026-05-19 拍板 · v118.34.22) · Step 1 必选 ≥1 客户
        'wiz-step-1-need-client': {
            zh: '请至少选 1 个 Pearnly 客户 · 这个 ERP 连接才知道把谁的发票推过去',
            en: 'Pick at least one Pearnly client · the ERP connection needs to know whose invoices to push',
            th: 'เลือกลูกค้า Pearnly อย่างน้อย 1 รายการ · ERP จะได้รู้ว่าจะส่งใบกำกับของใคร',
            zh_TW: '請至少選 1 個 Pearnly 客戶 · 這個 ERP 連線才知道把誰的發票推過去',
            ja: '少なくとも 1 件の Pearnly 取引先を選択してください · ERP 連携が誰の請求書を送るか判断するために必要です',
        },
        'wiz-step-2-h': {
            zh: '填入 MR.ERP 登录信息',
            en: 'Enter your MR.ERP login',
            th: 'กรอกข้อมูลเข้าสู่ระบบ MR.ERP',
            zh_TW: '填入 MR.ERP 登入資訊',
            ja: 'MR.ERP のログイン情報を入力',
        },
        'wiz-username': {
            zh: '用户名',
            en: 'Username',
            th: 'ชื่อผู้ใช้',
            zh_TW: '使用者名稱',
            ja: 'ユーザー名',
        },
        'wiz-password': {
            zh: '密码',
            en: 'Password',
            th: 'รหัสผ่าน',
            zh_TW: '密碼',
            ja: 'パスワード',
        },
        'wiz-pwd-hint': {
            zh: '密码会用我们的密钥加密 · 数据库里不存明文',
            en: 'Password is encrypted with our key — we never store it in plain text',
            th: 'รหัสผ่านถูกเข้ารหัสด้วยคีย์ของเรา — ไม่เก็บเป็น plain text',
            zh_TW: '密碼會用我們的金鑰加密 · 資料庫不存明文',
            ja: 'パスワードは弊社のキーで暗号化されます · 平文では保存しません',
        },
        'wiz-test-btn': {
            zh: '测试连接',
            en: 'Test connection',
            th: 'ทดสอบการเชื่อม',
            zh_TW: '測試連線',
            ja: '接続テスト',
        },
        'wiz-test-pending': {
            zh: '尚未测试',
            en: 'Not tested yet',
            th: 'ยังไม่ได้ทดสอบ',
            zh_TW: '尚未測試',
            ja: '未テスト',
        },
        'wiz-test-running': {
            zh: '正在测试…',
            en: 'Testing…',
            th: 'กำลังทดสอบ…',
            zh_TW: '正在測試…',
            ja: 'テスト中…',
        },
        'wiz-test-ok': {
            zh: '✓ 已连接 · 发现 {n} 个 ERP 年度账套/数据库',
            en: '✓ Connected — found {n} ERP year-database(s)',
            th: '✓ เชื่อมแล้ว — พบชุดบัญชีรายปี ERP {n} รายการ',
            zh_TW: '✓ 已連接 · 發現 {n} 個 ERP 年度帳套/資料庫',
            ja: '✓ 接続済み — ERP 年度データベース {n} 件',
        },
        // P-4 (Zihao 2026-05-19 拍板 · v118.34.21) · 失败时把截图路径单独显示
        'wiz-screenshot-saved': {
            zh: '失败截图存到了:{path} · 发给客服可以加快排查',
            en: 'Failure screenshot saved at: {path} · send this to support to speed up triage',
            th: 'บันทึกภาพข้อผิดพลาดที่: {path} · ส่งให้ทีมซัพพอร์ตเพื่อช่วยตรวจสอบ',
            zh_TW: '失敗截圖存到了:{path} · 發給客服可加快排查',
            ja: 'エラースクショ保存先: {path} · サポートに送ると調査が早まります',
        },
        'wiz-step-3-h': {
            zh: '选择 ERP 年度账套 + 推送模式',
            en: 'Pick the ERP year-database and push mode',
            th: 'เลือกชุดบัญชีรายปี ERP และโหมดการส่ง',
            zh_TW: '選擇 ERP 年度帳套 + 推送模式',
            ja: 'ERP 年度データベースと送信モードを選択',
        },
        'wiz-company': {
            zh: 'ERP 公司 / 年度账套',
            en: 'ERP company / year-database',
            th: 'บริษัท ERP / ชุดบัญชีรายปี',
            zh_TW: 'ERP 公司 / 年度帳套',
            ja: 'ERP 会社 / 年度データベース',
        },
        'wiz-company-hint': {
            zh: '请选择这批发票要写入的 MR.ERP 年度账套。通常同一家公司会按年度或数据库区分账套。',
            en: 'Pick the MR.ERP year-database these invoices write into. The same company is usually split into account-sets by year or database.',
            th: 'เลือกชุดบัญชีรายปี MR.ERP ที่ใบกำกับชุดนี้จะบันทึกเข้าไป โดยปกติบริษัทเดียวกันจะแยกชุดบัญชีตามปีหรือฐานข้อมูล',
            zh_TW: '請選擇這批發票要寫入的 MR.ERP 年度帳套。通常同一家公司會按年度或資料庫區分帳套。',
            ja: 'この請求書群を書き込む MR.ERP 年度データベースを選択してください。通常、同じ会社は年度やデータベースで帳簿が分かれます。',
        },
        'wiz-mode': {
            zh: '推送模式',
            en: 'Push mode',
            th: 'โหมดการส่ง',
            zh_TW: '推送模式',
            ja: '送信モード',
        },
        'wiz-mode-auto': {
            zh: '识别后自动推送(不需要手动)',
            en: 'Auto-push after OCR (hands-off)',
            th: 'ส่งอัตโนมัติหลัง OCR เสร็จ',
            zh_TW: '辨識後自動推送(不需手動)',
            ja: 'OCR 完了後に自動送信(手動不要)',
        },
        'wiz-mode-manual': {
            zh: '我手动点「推送」才推',
            en: "Only push when I click the 'Push' button",
            th: 'ส่งเมื่อกดปุ่ม "Push" เท่านั้น',
            zh_TW: '我手動點「推送」才推',
            ja: '「送信」ボタンを押したときのみ送信',
        },
        'wiz-seed': {
            zh: '自动创建买方时使用的模板(可选)',
            en: 'Template for auto-creating buyer customers (optional)',
            th: 'แม่แบบสำหรับสร้างลูกค้าผู้ซื้ออัตโนมัติ (ทางเลือก)',
            zh_TW: '自動建立買方時使用的範本(可選)',
            ja: '買い手の自動作成に使うテンプレート(任意)',
        },
        'wiz-seed-hint': {
            zh: '如果发票买方在 ERP 中不存在,系统会自动创建 ERP 买方客户。模板只用于继承 ERP 默认分类、账务等设置;客户名称、税号、地址来自发票识别结果。不选 = 关闭自动创建。',
            en: "If the invoice buyer doesn't exist in ERP, the system auto-creates an ERP buyer customer. The template only supplies ERP defaults (category, accounting, etc.); name, tax ID and address come from the invoice. Leave blank to disable auto-create.",
            th: 'หากผู้ซื้อในใบกำกับไม่มีใน ERP ระบบจะสร้างลูกค้าผู้ซื้อ ERP อัตโนมัติ · แม่แบบใช้สืบทอดค่าเริ่มต้น (หมวดหมู่/บัญชี) เท่านั้น · ชื่อ เลขภาษี ที่อยู่ มาจากใบกำกับ · เว้นว่าง = ปิดการสร้างอัตโนมัติ',
            zh_TW: '如果發票買方在 ERP 中不存在,系統會自動建立 ERP 買方客戶。範本只用於繼承 ERP 預設分類、帳務等設定;客戶名稱、稅號、地址來自發票辨識結果。不選 = 關閉自動建立。',
            ja: '請求書の買い手が ERP に存在しない場合、ERP 買い手顧客を自動作成します。テンプレートは ERP の既定設定(分類・勘定など)の継承のみに使用し、名称・税番号・住所は請求書から取得します。空欄 = 自動作成を無効化。',
        },
        'wiz-seed-empty': {
            zh: '— 不自动建(默认) —',
            en: '— do not auto-create (default) —',
            th: '— ไม่สร้างอัตโนมัติ (ค่าเริ่มต้น) —',
            zh_TW: '— 不自動建立(預設) —',
            ja: '— 自動作成しない(デフォルト) —',
        },
        'wiz-seed-loading': {
            zh: '正在拉取客户列表…',
            en: 'Loading customer list…',
            th: 'กำลังโหลดรายชื่อลูกค้า…',
            zh_TW: '正在拉取客戶列表…',
            ja: '顧客リストを読み込み中…',
        },
        'wiz-seed-fallback': {
            zh: '⚠ 无法拉取客户列表 · 请手动输入客户码',
            en: '⚠ Could not fetch the customer list — please type the code manually',
            th: '⚠ ไม่สามารถดึงรายชื่อลูกค้าได้ — กรุณาพิมพ์รหัสด้วยตนเอง',
            zh_TW: '⚠ 無法拉取客戶列表 · 請手動輸入客戶碼',
            ja: '⚠ 顧客リストを取得できません — コードを手動で入力してください',
        },
        'wiz-seed-placeholder': {
            zh: '请选择一个现有客户作模板',
            en: 'Pick an existing customer as the template',
            th: 'เลือกลูกค้าที่มีอยู่เพื่อใช้เป็นแม่แบบ',
            zh_TW: '請選擇一個現有客戶作範本',
            ja: '既存の顧客をテンプレートとして選択',
        },
        // Bug 2 (Zihao 2026-05-19 拍板 · v118.34.22) · 已保存 seed code 不在 listing
        // 当前页时 · 用这个 label 标记 · 让用户知道 endpoint 配置就是这个值 ·
        // 不会被误以为是 listing[0] fallback 默认.
        'wiz-seed-saved-not-in-list': {
            zh: '(已保存 · 当前列表暂未显示)',
            en: '(saved · not on current listing page)',
            th: '(บันทึกไว้ · ไม่ปรากฏในหน้าปัจจุบัน)',
            zh_TW: '(已儲存 · 當前列表暫未顯示)',
            ja: '(保存済み · 現在のリストには表示されていません)',
        },
        // v118.34.32 (Zihao 2026-05-19 拍板) · fail-over 状态的 dynamic 文案 ·
        // 让用户一眼看出当前显示的是"上次保存的值" + "可以手动改" · 不是状态冲突.
        'wiz-seed-fallback-saved': {
            zh: '⚠ 无法拉取最新客户列表 · 当前显示上次保存的「{code}」· 你可以手动改成别的',
            en: '⚠ Could not fetch the latest customer list · showing the previously saved value "{code}" · you can type a different one',
            th: '⚠ ไม่สามารถดึงรายชื่อลูกค้าล่าสุดได้ · กำลังแสดงค่าที่บันทึกไว้ "{code}" · คุณสามารถพิมพ์ค่าอื่นได้',
            zh_TW: '⚠ 無法拉取最新客戶列表 · 當前顯示上次儲存的「{code}」· 你可以手動改成別的',
            ja: '⚠ 最新の顧客リストを取得できません · 前回保存した「{code}」を表示中 · 別の値を入力できます',
        },
        'wiz-seedp-fallback-saved': {
            zh: '⚠ 无法拉取最新商品列表 · 当前显示上次保存的「{code}」· 你可以手动改成别的',
            en: '⚠ Could not fetch the latest product list · showing the previously saved value "{code}" · you can type a different one',
            th: '⚠ ไม่สามารถดึงรายการสินค้าล่าสุดได้ · กำลังแสดงค่าที่บันทึกไว้ "{code}" · คุณสามารถพิมพ์ค่าอื่นได้',
            zh_TW: '⚠ 無法拉取最新商品列表 · 當前顯示上次儲存的「{code}」· 你可以手動改成別的',
            ja: '⚠ 最新の商品リストを取得できません · 前回保存した「{code}」を表示中 · 別の値を入力できます',
        },
        'wiz-seed-input-placeholder': {
            zh: '输入客户码(如 0006)',
            en: 'Customer code (e.g. 0006)',
            th: 'รหัสลูกค้า (เช่น 0006)',
            zh_TW: '輸入客戶碼(如 0006)',
            ja: '顧客コード (例: 0006)',
        },
        // Seed PRODUCT (Task 2 Phase 5)
        'wiz-seedp': {
            zh: '自动创建商品时使用的模板(可选)',
            en: 'Template for auto-creating products (optional)',
            th: 'แม่แบบสำหรับสร้างสินค้าอัตโนมัติ (ทางเลือก)',
            zh_TW: '自動建立商品時使用的範本(可選)',
            ja: '商品の自動作成に使うテンプレート(任意)',
        },
        'wiz-seedp-hint': {
            zh: '如果发票商品在 ERP 中不存在,系统会自动创建 ERP 商品。模板只用于继承单位、分类、账户等默认设置;商品名称、价格、数量来自发票识别结果。不选 = 关闭自动创建。',
            en: "If an invoice product doesn't exist in ERP, the system auto-creates an ERP product. The template only supplies defaults (unit, category, account); product name, price and quantity come from the invoice. Leave blank to disable auto-create.",
            th: 'หากสินค้าในใบกำกับไม่มีใน ERP ระบบจะสร้างสินค้า ERP อัตโนมัติ · แม่แบบใช้สืบทอดค่าเริ่มต้น (หน่วย/หมวดหมู่/บัญชี) เท่านั้น · ชื่อ ราคา จำนวน มาจากใบกำกับ · เว้นว่าง = ปิดการสร้างอัตโนมัติ',
            zh_TW: '如果發票商品在 ERP 中不存在,系統會自動建立 ERP 商品。範本只用於繼承單位、分類、帳戶等預設設定;商品名稱、價格、數量來自發票辨識結果。不選 = 關閉自動建立。',
            ja: '請求書の商品が ERP に存在しない場合、ERP 商品を自動作成します。テンプレートは既定値(単位・分類・勘定)の継承のみに使用し、名称・価格・数量は請求書から取得します。空欄 = 自動作成を無効化。',
        },
        'wiz-seedp-empty': {
            zh: '— 不自动建(默认) —',
            en: '— do not auto-create (default) —',
            th: '— ไม่สร้างอัตโนมัติ (ค่าเริ่มต้น) —',
            zh_TW: '— 不自動建立(預設) —',
            ja: '— 自動作成しない(デフォルト) —',
        },
        'wiz-seedp-loading': {
            zh: '正在拉取商品列表…',
            en: 'Loading product list…',
            th: 'กำลังโหลดรายการสินค้า…',
            zh_TW: '正在拉取商品列表…',
            ja: '製品リストを読み込み中…',
        },
        'wiz-seedp-fallback': {
            zh: '⚠ 无法拉取商品列表 · 请手动输入商品码',
            en: '⚠ Could not fetch the product list — please type the code manually',
            th: '⚠ ไม่สามารถดึงรายการสินค้าได้ — กรุณาพิมพ์รหัสด้วยตนเอง',
            zh_TW: '⚠ 無法拉取商品列表 · 請手動輸入商品碼',
            ja: '⚠ 製品リストを取得できません — コードを手動で入力してください',
        },
        'wiz-seedp-input-placeholder': {
            zh: '输入商品码(如 P001)',
            en: 'Product code (e.g. P001)',
            th: 'รหัสสินค้า (เช่น P001)',
            zh_TW: '輸入商品碼(如 P001)',
            ja: '商品コード (例: P001)',
        },
        'btn-cancel': {
            zh: '取消',
            en: 'Cancel',
            th: 'ยกเลิก',
            zh_TW: '取消',
            ja: 'キャンセル',
        },
        'btn-prev': {
            zh: '← 上一步',
            en: '← Previous',
            th: '← ก่อนหน้า',
            zh_TW: '← 上一步',
            ja: '← 前へ',
        },
        'btn-next': {
            zh: '下一步 →',
            en: 'Next →',
            th: 'ถัดไป →',
            zh_TW: '下一步 →',
            ja: '次へ →',
        },
        'btn-finish': {
            zh: '完成 ✓',
            en: 'Finish ✓',
            th: 'เสร็จสิ้น ✓',
            zh_TW: '完成 ✓',
            ja: '完了 ✓',
        },
        // v118.34.4 · new strings for the integration-row card style.
        'mrerp-card-desc': {
            zh: '把识别完的发票自动推到 MR.ERP · 客户/商品/销售员自动建',
            en: 'Auto-push OCRed invoices to MR.ERP — customers / products / salesmen auto-created',
            th: 'ส่งใบกำกับที่ OCR แล้วเข้า MR.ERP อัตโนมัติ — ลูกค้า / สินค้า / พนักงานขาย สร้างให้',
            zh_TW: '把辨識完的發票自動推到 MR.ERP · 客戶/商品/銷售員自動建',
            ja: 'OCR 済みの請求書を MR.ERP に自動送信 — 取引先/商品/営業担当を自動作成',
        },
        'flow-card-desc': {
            zh: '泰国本地 SaaS 会计 · 即将上线',
            en: 'Thai-local SaaS accounting · coming soon',
            th: 'ระบบบัญชี SaaS ของไทย · เร็วๆ นี้',
            zh_TW: '泰國本地 SaaS 會計 · 即將上線',
            ja: 'タイのローカル SaaS 会計 · 近日公開',
        },
        'card-see-logs': {
            zh: '看推送日志 →',
            en: 'See push logs →',
            th: 'ดูประวัติส่ง →',
            zh_TW: '看推送記錄 →',
            ja: '送信ログを見る →',
        },
        // v118.34.34 (Zihao 2026-05-19 拍板 · 批 2 改动 7) · 启用/停用 toggle
        'card-btn-disable': {
            zh: '停用',
            en: 'Disable',
            th: 'ปิดใช้งาน',
            zh_TW: '停用',
            ja: '無効化',
        },
        'card-btn-enable': {
            zh: '启用',
            en: 'Enable',
            th: 'เปิดใช้งาน',
            zh_TW: '啟用',
            ja: '有効化',
        },
        'card-disabled-pill': {
            zh: '已停用',
            en: 'Disabled',
            th: 'ปิดใช้งานแล้ว',
            zh_TW: '已停用',
            ja: '無効',
        },
        'card-disabled-tip': {
            zh: '已停用 · 自动推送跳过 · 手动推送不可选 · 重新点「启用」才会推送',
            en: 'Disabled · auto-push skipped · cannot be selected for manual push · click "Enable" to resume',
            th: 'ปิดใช้งาน · ส่งอัตโนมัติถูกข้าม · เลือกส่งด้วยตนเองไม่ได้ · กด "เปิดใช้งาน" เพื่อใช้ต่อ',
            zh_TW: '已停用 · 自動推送跳過 · 手動推送不可選 · 重新點「啟用」才會推送',
            ja: '無効化済み · 自動送信はスキップ · 手動送信で選択不可 · 「有効化」をクリックで再開',
        },
        'card-toggle-disable-confirm': {
            zh: '停用 MR.ERP 后,新发票不会再推送(已成功的不动)· 继续?',
            en: 'Disabling MR.ERP stops new pushes (existing successful pushes are kept). Continue?',
            th: 'ปิดใช้งาน MR.ERP จะหยุดส่งใบกำกับใหม่ (รายการที่สำเร็จแล้วยังคงอยู่) · ดำเนินการต่อ?',
            zh_TW: '停用 MR.ERP 後,新發票不會再推送(已成功的不動)· 繼續?',
            ja: 'MR.ERP を無効化すると新しい送信は停止します (既存の成功は保持) · 続行しますか?',
        },
        'card-toggle-disable-success': {
            zh: '已停用 MR.ERP',
            en: 'MR.ERP disabled',
            th: 'ปิดใช้งาน MR.ERP แล้ว',
            zh_TW: '已停用 MR.ERP',
            ja: 'MR.ERP を無効化しました',
        },
        'card-toggle-enable-success': {
            zh: '已启用 MR.ERP',
            en: 'MR.ERP enabled',
            th: 'เปิดใช้งาน MR.ERP แล้ว',
            zh_TW: '已啟用 MR.ERP',
            ja: 'MR.ERP を有効化しました',
        },
        'card-toggle-failed': {
            zh: '切换失败 · 稍后再试',
            en: 'Toggle failed · please retry',
            th: 'สลับสถานะไม่สำเร็จ · ลองอีกครั้ง',
            zh_TW: '切換失敗 · 稍後再試',
            ja: '切り替えに失敗しました · 再試行してください',
        },
        // Wizard finish toasts / validation messages — were hardcoded
        // Chinese before v118.34.4.
        'wiz-fill-creds': {
            zh: '请先填入用户名和密码',
            en: 'Please enter username and password first',
            th: 'กรุณากรอกชื่อผู้ใช้และรหัสผ่านก่อน',
            zh_TW: '請先填入使用者名稱和密碼',
            ja: 'ユーザー名とパスワードを入力してください',
        },
        'wiz-save-failed': {
            zh: '保存失败 · 状态 {status}',
            en: 'Save failed · status {status}',
            th: 'บันทึกไม่สำเร็จ · สถานะ {status}',
            zh_TW: '儲存失敗 · 狀態 {status}',
            ja: '保存失敗 · ステータス {status}',
        },
        'wiz-saved': {
            zh: '已保存',
            en: 'Saved',
            th: 'บันทึกแล้ว',
            zh_TW: '已儲存',
            ja: '保存しました',
        },
        // v118.34.4 · the new 3-way ERP subtab split (连接 / 推送日志 /
        // 字段映射). "推送日志" reuses home.js's existing erp-logs-title
        // key. "连接" needs its own translation since the original key
        // (auto-erp-subtab-connect) meant "连接 & 推送日志" — which is
        // now misleading. We don't touch home.js dict per Zihao's rule,
        // so we localize this tab from our own IIFE in _localizeSubtabs().
        'auto-erp-subtab-connect-only': {
            zh: '连接',
            en: 'Connect',
            th: 'เชื่อมต่อ',
            zh_TW: '連接',
            ja: '接続',
        },
    };

    function _activeLang() {
        try {
            if (typeof window.currentLang === 'string' && window.currentLang)
                return window.currentLang;
            const ls = localStorage.getItem('mrpilot_lang');
            if (ls) return ls;
        } catch (e) {}
        return 'zh';
    }

    function t(key, vars) {
        const lang = _activeLang();
        const entry = T[key] || {};
        let v = entry[lang] || entry.en || entry.zh || key;
        if (vars && typeof v === 'string') {
            Object.keys(vars).forEach(function (k) {
                v = v.replace(new RegExp('\\{' + k + '\\}', 'g'), String(vars[k]));
            });
        }
        return v;
    }

    function _esc(s) {
        return typeof window.escapeHtml === 'function'
            ? window.escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }

    function _toast(msg, kind) {
        try {
            if (typeof window.showToast === 'function') window.showToast(msg, kind || 'info');
        } catch (e) {}
    }

    function _tk() {
        try {
            return localStorage.getItem('mrpilot_token') || '';
        } catch (e) {
            return '';
        }
    }

    function _authHeaders() {
        const h = { 'Content-Type': 'application/json' };
        const tk = _tk();
        if (tk) h['Authorization'] = 'Bearer ' + tk;
        return h;
    }

    function _fmtRelativeTime(iso) {
        if (!iso) return '—';
        const d = new Date(iso);
        const diffMs = Date.now() - d.getTime();
        if (diffMs < 0) return d.toLocaleString();
        const s = Math.floor(diffMs / 1000);
        if (s < 60) return s + 's';
        if (s < 3600) return Math.floor(s / 60) + 'm';
        if (s < 86400) return Math.floor(s / 3600) + 'h';
        return Math.floor(s / 86400) + 'd';
    }

    // ─────────────────────────────────────────────────────────────
    // Data layer — fetches endpoints + test-connection
    // ─────────────────────────────────────────────────────────────
    async function _loadEndpoints() {
        try {
            const r = await fetch('/api/erp/endpoints', { headers: _authHeaders() });
            if (!r.ok) return [];
            const data = await r.json();
            return Array.isArray(data.items) ? data.items : [];
        } catch (e) {
            return [];
        }
    }

    async function _testConnection(endpointId, refresh) {
        try {
            const q = refresh ? '?refresh=1' : '';
            const r = await fetch(
                '/api/erp/endpoints/' + encodeURIComponent(endpointId) + '/test-connection' + q,
                {
                    method: 'POST',
                    headers: _authHeaders(),
                }
            );
            if (!r.ok) return { ok: false, error_code: 'ERR_HTTP_' + r.status };
            return await r.json();
        } catch (e) {
            return { ok: false, error_code: 'ERR_NETWORK', raw_error: String(e).slice(0, 200) };
        }
    }

    // ─────────────────────────────────────────────────────────────
    // Card rendering · v118.34.4 大改写
    //
    // 一比一复刻 Pearnly 既有 .integration-row 卡片样式
    // (Google Drive / LINE Bot / Gmail 抓取 那种横向 icon + 名字 +
    // 描述 + 按钮 的卡片)。
    //
    // 不再用 .mrerp-card 这种自创类 · CSS 完全 reuse home.css 的
    // .integration-row + .int-icon + .int-info + .int-actions。
    // ─────────────────────────────────────────────────────────────
    function _renderCards(host, mrerpEp) {
        // host 是 #erp-connect-cards · 我们渲染 MR.ERP 卡片。
        // Xero 卡片由另一个 IIFE 在 host 内单独 prepend · 我们不动它,只 append 自己的。
        // v118.34.35 · FlowAccount "即将上线" 空卡片移除
        const cardsHtml = [_renderMrerpCard(mrerpEp)].join('');

        // Find or create our own append zone (not interfering with
        // anything Xero IIFE put in there).
        let zone = host.querySelector('[data-mrerp-zone]');
        if (!zone) {
            zone = document.createElement('div');
            zone.setAttribute('data-mrerp-zone', '1');
            // Tiny top margin so we don't crowd whatever sits above
            // (typically the Xero card or a section title).
            zone.style.marginTop = '8px';
            host.appendChild(zone);
        }
        zone.innerHTML = cardsHtml;

        _bindCardEvents(zone, mrerpEp);
    }

    // The MR.ERP icon — small grid glyph matching the Pearnly visual
    // style (1.8px stroke, currentColor, viewBox 24).
    const _MRERP_ICON_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
        '<rect x="3" y="3" width="18" height="18" rx="3"/>' +
        '<path d="M7 8h10M7 12h10M7 16h6"/>' +
        '</svg>';

    // FlowAccount icon — circular play-style glyph.
    const _FLOW_ICON_SVG =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
        '<circle cx="12" cy="12" r="9"/>' +
        '<path d="M10 8l5 4-5 4z" fill="currentColor"/>' +
        '</svg>';

    function _renderMrerpCard(ep) {
        const configured = !!ep;
        // v118.34.34 (Zihao 2026-05-19 拍板) · 启用/停用 toggle 状态.
        // ep.enabled 默认 true · 老数据无此字段也按 true 处理.
        const enabled = configured ? ep.enabled !== false : true;

        // Status pill — shown next to the card name (matches the
        // pattern used by other Pearnly cards: name + small inline pill).
        let pill;
        if (!configured) {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral">' +
                _esc(t('card-not-configured')) +
                '</span>';
        } else if (!enabled) {
            // v118.34.34 · 已停用 · 用 neutral 灰 pill · 不显示 checking 状态
            // (停用时不该跑 health check)· title 让 hover 看到原因.
            pill =
                '<span class="mrerp-card-pill mrerp-pill-neutral" ' +
                'title="' +
                _esc(t('card-disabled-tip')) +
                '">' +
                _esc(t('card-disabled-pill')) +
                '</span>';
        } else {
            pill =
                '<span class="mrerp-card-pill mrerp-pill-testing" ' +
                'data-mrerp-test-pill="' +
                _esc(ep.id) +
                '">' +
                _esc(t('card-checking')) +
                '</span>';
        }

        // Action buttons — right side. Use Pearnly's .int-btn-configure
        // class (the same class the OUTER integration row buttons use)
        // so visually we render identically.
        // v118.34.34 · configured 卡片现在额外有「停用/启用」按钮.
        let actionsHtml;
        if (configured) {
            // v118.34.35 · 删 "看推送日志" 按钮 · 统一放在面板底部
            const toggleLabel = enabled ? t('card-btn-disable') : t('card-btn-enable');
            const toggleClass = enabled
                ? 'mrerp-card-toggle mrerp-card-toggle-disable'
                : 'mrerp-card-toggle mrerp-card-toggle-enable';
            actionsHtml =
                '<button type="button" class="' +
                toggleClass +
                '" ' +
                'data-mrerp-card-action="toggle-enabled" ' +
                'data-mrerp-enabled="' +
                (enabled ? '1' : '0') +
                '" ' +
                'title="' +
                _esc(t('card-disabled-tip')) +
                '">' +
                _esc(toggleLabel) +
                '</button>' +
                '<button type="button" class="int-btn-configure" data-mrerp-card-action="edit">' +
                _esc(t('card-btn-edit')) +
                '</button>';
        } else {
            actionsHtml =
                '<button type="button" class="int-btn-configure" data-mrerp-card-action="connect">' +
                _esc(t('card-btn-connect')) +
                '</button>';
        }

        // v118.34.34 · 停用时整行加 is-disabled class 让 CSS 灰掉.
        const rowCls =
            'integration-row' +
            (configured ? ' connected' : '') +
            (configured && !enabled ? ' is-disabled' : '');

        return (
            '<div class="' +
            rowCls +
            '" ' +
            'data-mrerp-card="mrerp"' +
            (ep ? ' data-mrerp-endpoint-id="' + _esc(ep.id) + '"' : '') +
            '>' +
            '<div class="int-icon ic-mrerp">' +
            _MRERP_ICON_SVG +
            '</div>' +
            '<div class="int-info">' +
            '<div class="int-name">' +
            '<span>' +
            _esc(t('mrerp-card-name')) +
            '</span>' +
            pill +
            '</div>' +
            '<div class="int-desc">' +
            _esc(t('mrerp-card-desc')) +
            '</div>' +
            '</div>' +
            '<div class="int-actions">' +
            actionsHtml +
            '</div>' +
            '</div>'
        );
    }

    // v118.34.35 · _renderFlowAccountCard 已删除 (空卡片占位 · 上线时再加回)

    function _bindCardEvents(zone, mrerpEp) {
        // Card-level "Connect" / "Edit" → open wizard
        zone.querySelectorAll(
            '[data-mrerp-card-action="connect"], [data-mrerp-card-action="edit"]'
        ).forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                window._mrerpOpenWizard(mrerpEp || null);
            });
        });
        // "See push logs →" — switch ERP subtab to the new logs panel.
        zone.querySelectorAll('[data-mrerp-card-action="see-logs"]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _switchToLogsTab();
            });
        });
        // v118.34.34 (批 2 改动 7) · 停用/启用 toggle ·
        // 停用要二次确认 · 启用直接切. 切完重 bootstrap 整张卡片以
        // 同步状态(pill/灰化/按钮文字 全部要变).
        zone.querySelectorAll('[data-mrerp-card-action="toggle-enabled"]').forEach(function (btn) {
            btn.addEventListener('click', async function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (!mrerpEp) return;
                const currentlyEnabled = btn.getAttribute('data-mrerp-enabled') === '1';
                const newEnabled = !currentlyEnabled;
                if (!newEnabled) {
                    // 停用要二次确认.
                    let confirmed = false;
                    try {
                        if (typeof window.pearnlyConfirm === 'function') {
                            confirmed = await window.pearnlyConfirm(
                                t('card-toggle-disable-confirm')
                            );
                        } else {
                            confirmed = window.confirm(t('card-toggle-disable-confirm'));
                        }
                    } catch (e2) {
                        confirmed = window.confirm(t('card-toggle-disable-confirm'));
                    }
                    if (!confirmed) return;
                }
                // Optimistic UI lock — disable the button while patching.
                btn.disabled = true;
                try {
                    const r = await fetch('/api/erp/endpoints/' + encodeURIComponent(mrerpEp.id), {
                        method: 'PATCH',
                        headers: _authHeaders(),
                        body: JSON.stringify({ enabled: newEnabled }),
                    });
                    if (!r.ok) {
                        _toast(t('card-toggle-failed'), 'error');
                        btn.disabled = false;
                        return;
                    }
                    _toast(
                        newEnabled
                            ? t('card-toggle-enable-success')
                            : t('card-toggle-disable-success'),
                        'success'
                    );
                    // Reload endpoints & re-render the whole card area so
                    // pill / row class / toggle button label all flip together.
                    await _bootstrap();
                    // v118.34.34 · 通知 home.js · 让推送按钮也更新可选 ERP 数.
                    try {
                        if (typeof window._refreshErpEndpointsCache === 'function') {
                            window._refreshErpEndpointsCache();
                        }
                    } catch (e2) {}
                } catch (err) {
                    _toast(t('card-toggle-failed'), 'error');
                    btn.disabled = false;
                }
            });
        });
    }

    // v118.34.4 · jump to the "推送日志" subtab. We click the tab pill
    // by selector so the existing tab switcher (whatever home.js wires
    // up to .erp-subtab) handles the panel toggle for us — no fragile
    // direct DOM manipulation.
    function _switchToLogsTab() {
        const tab = document.querySelector('.erp-subtabs [data-erp-subtab="logs"]');
        if (tab && typeof tab.click === 'function') {
            tab.click();
            return;
        }
        // Fallback: home.js hasn't wired the new tab yet — just expand
        // the legacy <details> log section.
        const det = document.getElementById('erp-logs-section');
        if (det) {
            det.open = true;
            det.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    async function _refreshCardHealth(endpointId, force) {
        const pill = document.querySelector(
            '[data-mrerp-test-pill="' + CSS.escape(endpointId) + '"]'
        );
        if (!pill) return;
        pill.className = 'mrerp-card-pill mrerp-pill-testing';
        pill.textContent = t('card-checking');
        pill.setAttribute('data-mrerp-test-pill', endpointId);
        const result = await _testConnection(endpointId, !!force);
        if (result.ok) {
            pill.className = 'mrerp-card-pill mrerp-pill-ok';
            pill.textContent = t('card-connected');
            pill.title = '';
        } else {
            pill.className = 'mrerp-card-pill mrerp-pill-err';
            pill.textContent = t('card-needs-attention');
            const friendly = result.error_friendly || {};
            pill.title = (
                friendly[_activeLang()] ||
                friendly.en ||
                result.error_code ||
                ''
            ).toString();
        }
        pill.setAttribute('data-mrerp-test-pill', endpointId);
    }

    // ─────────────────────────────────────────────────────────────
    // Bootstrap
    // ─────────────────────────────────────────────────────────────
    async function _bootstrap() {
        const host = document.getElementById('erp-connect-cards');
        if (!host) return;
        // v118.34.4 · localize the new "连接" tab (key not in home.js dict).
        _localizeSubtabs();
        const endpoints = await _loadEndpoints();
        const mrerpEp =
            endpoints.find(function (e) {
                return (e.adapter || '').toLowerCase() === 'mrerp';
            }) || null;
        _renderCards(host, mrerpEp);
        if (mrerpEp && mrerpEp.enabled !== false) {
            // v118.34.34 · 停用的 endpoint 不跑 health check ·
            // pill 已固定显示「已停用」· 跑 check 反而会把它覆盖成 testing.
            _refreshCardHealth(mrerpEp.id, false);
        }
        // C-5 · conditional hide of the 字段映射 sub-tab.
        _applyMappingsTabVisibility(endpoints);
    }

    // v118.34.4 · localize the new "连接" tab. The new "推送日志" tab
    // uses data-i18n="erp-logs-title" which IS in home.js's dict, so
    // home.js's applyLang() handles it automatically. "连接" uses a
    // new key (auto-erp-subtab-connect-only) we own here.
    function _localizeSubtabs() {
        const connectTab = document.querySelector('.erp-subtab[data-erp-subtab="connect"]');
        if (connectTab) connectTab.textContent = t('auto-erp-subtab-connect-only');
    }

    // ─────────────────────────────────────────────────────────────
    // C-5 (Zihao 2026-05-18 拍板) · "字段映射" sub-tab conditional
    // hide. Rule:
    //   • zero endpoints OR ALL endpoints adapter='mrerp' → hide
    //   • any non-mrerp endpoint (xero / webhook / flowaccount /
    //     other) → leave tab + advanced toolbar VISIBLE for the
    //     legacy mapping workflow
    //   • client-mapping sub-tab inside is hidden when MR.ERP-only
    //     (sync preflight covers it)
    // Adapter-aware; safe to run repeatedly.
    // ─────────────────────────────────────────────────────────────
    function _applyMappingsTabVisibility(endpoints) {
        const eps = (endpoints || []).filter(function (e) {
            return e && e.enabled !== false;
        });
        const adapters = eps.map(function (e) {
            return (e.adapter || '').toLowerCase();
        });
        const hasNonMrerp = adapters.some(function (a) {
            return a && a !== 'mrerp';
        });

        // Tab pill in .erp-subtabs
        const mappingsTabPill = document.querySelector('.erp-subtabs [data-erp-subtab="mappings"]');
        // Sub-panel
        const mappingsPanel = document.querySelector('.erp-subpanel[data-erp-subpanel="mappings"]');
        if (!mappingsTabPill || !mappingsPanel) return;

        const shouldHide = !hasNonMrerp;
        mappingsTabPill.style.display = shouldHide ? 'none' : '';
        mappingsPanel.style.display = shouldHide ? 'none' : '';
        if (shouldHide) {
            // If the mappings tab was active, switch back to connect.
            const connectTab = document.querySelector('.erp-subtabs [data-erp-subtab="connect"]');
            const connectPanel = document.querySelector(
                '.erp-subpanel[data-erp-subpanel="connect"]'
            );
            if (mappingsPanel.classList.contains('active')) {
                if (connectTab) {
                    connectTab.classList.add('active');
                    mappingsTabPill.classList.remove('active');
                }
                if (connectPanel) {
                    connectPanel.classList.add('active');
                    mappingsPanel.classList.remove('active');
                }
            }
        }

        // Inside the mappings tab, hide the "客户映射" sub-tab when
        // mrerp endpoints are present (sync preflight makes it
        // redundant). Other sub-tabs (accounts / taxes / products)
        // are kept because Xero still needs them.
        const clientsSubTab = document.querySelector(
            '.erp-map-subtabs [data-erp-subtab="clients"]'
        );
        if (clientsSubTab) {
            const hideClients = adapters.indexOf('mrerp') >= 0;
            clientsSubTab.style.display = hideClients ? 'none' : '';
        }
    }

    // Expose so home.js can re-invoke after page navigation.
    window._mrerpRenderCards = _bootstrap;

    // Public hook for the wizard module (defined further below in
    // the same file — C-3).
    window._mrerpOpenWizard =
        window._mrerpOpenWizard ||
        function () {
            console.log('[mrerp] wizard not yet attached');
        };

    // ─────────────────────────────────────────────────────────────
    // Auto-bind: render on initial load + whenever the ERP tab
    // becomes visible (subscribed via DOM mutation).
    // ─────────────────────────────────────────────────────────────
    function _scheduleBootstrap() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', _bootstrap, { once: true });
        } else {
            // Already past DOMContentLoaded — defer a tick so
            // home.js's own IIFEs finish first.
            setTimeout(_bootstrap, 0);
        }
    }
    _scheduleBootstrap();

    // Re-bootstrap when the ERP tab is shown (the existing tab
    // switcher just toggles CSS; we listen to the same hash / class
    // mutation home.js uses).
    document.addEventListener(
        'click',
        function (e) {
            const tabEl =
                e.target.closest &&
                e.target.closest('[data-auto-panel="erp"], .auto-tab[data-tab="erp"]');
            if (!tabEl) return;
            setTimeout(_bootstrap, 80);
        },
        true
    );

    // ─────────────────────────────────────────────────────────────
    // v118.34.4 · 跟随 Pearnly 语言切换重新渲染。
    // 之前 bug:卡片用 _activeLang() 在 bootstrap 时计算文字,但用户
    // 后续切语言时不会自动重渲染 · 导致截图里看到的「中泰文混杂」
    // (drawer 标题已经切到泰文,但卡片 pill 还是中文)。
    //
    // 我们订阅三个信号 + 每 800ms 兜底轮询:
    //   1. 监听 storage event(用户在另一个 tab 切语言会 fire)
    //   2. 监听 'mrpilot:lang-changed' custom event(若 home.js 以
    //      后愿意广播 · 我们提前接住)
    //   3. 监听 .lang-switcher 点击(目前 home.js 切语言入口)
    //   4. 轮询 _activeLang() 比较上次值 · 兜底捕获任何
    //      window.currentLang 直接赋值的场景
    // 任意触发就调一次 _bootstrap · 内部本来就只重画 DOM,无副作用。
    // ─────────────────────────────────────────────────────────────
    let _lastLang = _activeLang();
    function _maybeRerenderForLang() {
        const cur = _activeLang();
        if (cur === _lastLang) return;
        _lastLang = cur;
        _bootstrap();
    }
    try {
        window.addEventListener('storage', function (e) {
            if (e && e.key === 'mrpilot_lang') _maybeRerenderForLang();
        });
        window.addEventListener('mrpilot:lang-changed', _maybeRerenderForLang);
        document.addEventListener(
            'click',
            function (e) {
                // Any element whose data-lang attribute looks like a 2-letter
                // code (e.g. zh/en/th/ja/zh_TW) is treated as a lang switch
                // candidate. Cheap heuristic — false positives are harmless
                // because _maybeRerenderForLang short-circuits when nothing
                // actually changed.
                const sw =
                    e.target.closest &&
                    e.target.closest('[data-lang], .lang-switcher button, .lang-option');
                if (!sw) return;
                // Give home.js a tick to commit the change before we read.
                setTimeout(_maybeRerenderForLang, 120);
            },
            true
        );
        // Safety-net poll — 800 ms is invisible to humans, and the
        // _bootstrap call only fires when the lang actually changed.
        setInterval(_maybeRerenderForLang, 800);
    } catch (_e) {
        /* environment without window/document — noop */
    }

    // Expose i18n / fetch helpers for the wizard module to share.
    window._mrerpConnectShared = {
        T,
        t,
        _esc,
        _toast,
        _tk,
        _authHeaders,
        _loadEndpoints,
        _testConnection,
        _activeLang,
    };

    // =============================================================
    // C-3 · 3-step connect wizard (Zihao 2026-05-18 拍板)
    //
    // Loaded inline in this same file (not the originally suggested
    // static/erp-connect-wizard.html) so we don't need a separate
    // fetch — the modal DOM is built in-memory and inserted on first
    // open. Keeps the network footprint to 1 CSS + 1 JS.
    //
    // Modal lifecycle:
    //   _mrerpOpenWizard(endpoint | null)
    //     - endpoint=null → new connection (Step 1 blank)
    //     - endpoint=<obj> → edit (preload from endpoint.config)
    //
    // Step 3 includes the new "新客户模板" (seed_customer_code)
    // dropdown that ties Customer auto-create to a known-good seed
    // (e.g. 0006). Empty selection disables auto-create entirely.
    // =============================================================

    let _wizardEl = null;
    let _wizardState = null;

    function _ensureWizardDom() {
        if (_wizardEl) return _wizardEl;
        const wrap = document.createElement('div');
        wrap.className = 'mrerp-wizard-overlay';
        wrap.setAttribute('role', 'dialog');
        wrap.setAttribute('aria-modal', 'true');
        wrap.innerHTML =
            '<div class="mrerp-wizard">' +
            '<div class="mrerp-wizard-head">' +
            '<div class="mrerp-wizard-title" data-mw-title></div>' +
            '<div class="mrerp-wizard-progress">' +
            '<span class="mrerp-wizard-step-dot is-active" data-mw-dot="1"></span>' +
            '<span class="mrerp-wizard-step-sep"></span>' +
            '<span class="mrerp-wizard-step-dot" data-mw-dot="2"></span>' +
            '<span class="mrerp-wizard-step-sep"></span>' +
            '<span class="mrerp-wizard-step-dot" data-mw-dot="3"></span>' +
            '</div>' +
            '<button class="mrerp-wizard-close" data-mw-close type="button" aria-label="close">' +
            '<svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>' +
            '</button>' +
            '</div>' +
            '<div class="mrerp-wizard-body">' +
            _buildStep1Html() +
            _buildStep2Html() +
            _buildStep3Html() +
            '</div>' +
            '<div class="mrerp-wizard-foot">' +
            '<button class="btn btn-ghost" data-mw-cancel type="button"></button>' +
            '<div class="mrerp-wizard-foot-spacer"></div>' +
            '<button class="btn btn-ghost" data-mw-prev type="button" style="display:none;"></button>' +
            '<button class="btn btn-primary" data-mw-next type="button"></button>' +
            '</div>' +
            '</div>';
        document.body.appendChild(wrap);
        _wizardEl = wrap;
        _bindWizardEvents();
        return wrap;
    }

    function _buildStep1Html() {
        return (
            '<div class="mrerp-wizard-step is-active" data-mw-step="1">' +
            '<h3 class="mrerp-wizard-step-h" data-mw-step1-h></h3>' +
            '<p class="mrerp-wizard-hint" data-mw-step1-hint></p>' +
            '<div class="mrerp-wizard-checkboxes" data-mw-clients>' +
            '<div class="mrerp-card-empty">—</div>' +
            '</div>' +
            '</div>'
        );
    }

    function _buildStep2Html() {
        return (
            '<div class="mrerp-wizard-step" data-mw-step="2">' +
            '<h3 class="mrerp-wizard-step-h" data-mw-step2-h></h3>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-user-label></label>' +
            '<input type="text" class="mrerp-wizard-input" data-mw-user autocomplete="username">' +
            '</div>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-pass-label></label>' +
            '<input type="password" class="mrerp-wizard-input" data-mw-pass autocomplete="new-password">' +
            '<div class="mrerp-wizard-hint" data-mw-pwd-hint></div>' +
            '</div>' +
            '<div class="mrerp-wizard-test-row">' +
            '<button class="btn btn-ghost btn-tiny" type="button" data-mw-test></button>' +
            '<span class="mrerp-wizard-test-status" data-mw-test-status></span>' +
            '</div>' +
            '<div class="mrerp-wizard-test-error" data-mw-test-error style="display:none;">' +
            '<div data-mw-test-error-friendly></div>' +
            '<div class="mrerp-wizard-test-error-screenshot" data-mw-test-error-screenshot style="display:none;"></div>' +
            '<div class="mrerp-wizard-test-error-raw" data-mw-test-error-raw></div>' +
            '</div>' +
            '</div>'
        );
    }

    function _buildStep3Html() {
        // The seed field is dual-rendered: a <select> filled from
        // GET /api/erp/endpoints/:id/customers when editing an
        // existing endpoint (so the user picks from the live list),
        // OR a text input as fallback when creating a new endpoint
        // (no id yet) or when the fetch fails.
        return (
            '<div class="mrerp-wizard-step" data-mw-step="3">' +
            '<h3 class="mrerp-wizard-step-h" data-mw-step3-h></h3>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-company-label></label>' +
            '<select class="mrerp-wizard-select" data-mw-company></select>' +
            '<div class="mrerp-wizard-hint" data-mw-company-hint></div>' +
            '</div>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-mode-label></label>' +
            '<div class="mrerp-wizard-radio-group">' +
            '<label class="mrerp-wizard-radio-row">' +
            '<input type="radio" name="mrerp-mode" value="auto" checked>' +
            '<span data-mw-mode-auto></span>' +
            '</label>' +
            '<label class="mrerp-wizard-radio-row">' +
            '<input type="radio" name="mrerp-mode" value="manual">' +
            '<span data-mw-mode-manual></span>' +
            '</label>' +
            '</div>' +
            '</div>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-seed-label></label>' +
            '<select class="mrerp-wizard-select" data-mw-seed style="display:none;">' +
            '<option value="" data-mw-seed-empty></option>' +
            '</select>' +
            '<input type="text" class="mrerp-wizard-input" data-mw-seed-input style="display:none;" autocomplete="off">' +
            '<div class="mrerp-wizard-hint" data-mw-seed-hint></div>' +
            '<div class="mrerp-wizard-hint" data-mw-seed-fallback-hint style="display:none;color:#8a5a00;"></div>' +
            '</div>' +
            '<div class="mrerp-wizard-field">' +
            '<label class="mrerp-wizard-label" data-mw-seedp-label></label>' +
            '<select class="mrerp-wizard-select" data-mw-seedp style="display:none;">' +
            '<option value="" data-mw-seedp-empty></option>' +
            '</select>' +
            '<input type="text" class="mrerp-wizard-input" data-mw-seedp-input style="display:none;" autocomplete="off">' +
            '<div class="mrerp-wizard-hint" data-mw-seedp-hint></div>' +
            '<div class="mrerp-wizard-hint" data-mw-seedp-fallback-hint style="display:none;color:#8a5a00;"></div>' +
            '</div>' +
            '</div>'
        );
    }

    function _bindWizardEvents() {
        const w = _wizardEl;
        w.querySelector('[data-mw-close]').addEventListener('click', _closeWizard);
        w.querySelector('[data-mw-cancel]').addEventListener('click', _closeWizard);
        w.querySelector('[data-mw-prev]').addEventListener('click', _wizardPrev);
        w.querySelector('[data-mw-next]').addEventListener('click', _wizardNext);
        w.querySelector('[data-mw-test]').addEventListener('click', _wizardRunTest);
        w.addEventListener('click', function (e) {
            // click outside the modal body closes
            if (e.target === w) _closeWizard();
        });
        document.addEventListener('keydown', function (e) {
            if (!_wizardEl || !_wizardEl.classList.contains('is-open')) return;
            if (e.key === 'Escape') _closeWizard();
        });
    }

    function _applyWizardI18n() {
        const w = _wizardEl;
        w.querySelector('[data-mw-title]').textContent = t('wiz-title-connect');
        // Step 1
        w.querySelector('[data-mw-step1-h]').textContent = t('wiz-step-1-h');
        w.querySelector('[data-mw-step1-hint]').textContent = t('wiz-step-1-hint');
        // Step 2
        w.querySelector('[data-mw-step2-h]').textContent = t('wiz-step-2-h');
        w.querySelector('[data-mw-user-label]').textContent = t('wiz-username');
        w.querySelector('[data-mw-pass-label]').textContent = t('wiz-password');
        w.querySelector('[data-mw-pwd-hint]').textContent = t('wiz-pwd-hint');
        w.querySelector('[data-mw-test]').textContent = t('wiz-test-btn');
        w.querySelector('[data-mw-test-status]').textContent = t('wiz-test-pending');
        // Step 3
        w.querySelector('[data-mw-step3-h]').textContent = t('wiz-step-3-h');
        w.querySelector('[data-mw-company-label]').textContent = t('wiz-company');
        w.querySelector('[data-mw-company-hint]').textContent = t('wiz-company-hint');
        w.querySelector('[data-mw-mode-label]').textContent = t('wiz-mode');
        w.querySelector('[data-mw-mode-auto]').textContent = t('wiz-mode-auto');
        w.querySelector('[data-mw-mode-manual]').textContent = t('wiz-mode-manual');
        w.querySelector('[data-mw-seed-label]').textContent = t('wiz-seed');
        w.querySelector('[data-mw-seed-hint]').textContent = t('wiz-seed-hint');
        // Reset the seed select to its initial single-option state so
        // _populateSeedSelector has a consistent starting point. (On
        // subsequent _openWizard calls, the previous run may have
        // populated the select with N customer options + wiped the
        // data-mw-seed-empty option.)
        const seedSelEl = w.querySelector('[data-mw-seed]');
        if (seedSelEl) {
            seedSelEl.innerHTML =
                '<option value="" data-mw-seed-empty>' + _esc(t('wiz-seed-empty')) + '</option>';
        }
        const seedInput = w.querySelector('[data-mw-seed-input]');
        if (seedInput) seedInput.placeholder = t('wiz-seed-input-placeholder');
        const fbHint = w.querySelector('[data-mw-seed-fallback-hint]');
        if (fbHint) fbHint.textContent = t('wiz-seed-fallback');
        // Seed product (Task 2 Phase 5)
        const spLabel = w.querySelector('[data-mw-seedp-label]');
        if (spLabel) spLabel.textContent = t('wiz-seedp');
        const spHint = w.querySelector('[data-mw-seedp-hint]');
        if (spHint) spHint.textContent = t('wiz-seedp-hint');
        const spSelEl = w.querySelector('[data-mw-seedp]');
        if (spSelEl) {
            spSelEl.innerHTML =
                '<option value="" data-mw-seedp-empty>' + _esc(t('wiz-seedp-empty')) + '</option>';
        }
        const spInput = w.querySelector('[data-mw-seedp-input]');
        if (spInput) spInput.placeholder = t('wiz-seedp-input-placeholder');
        const spFbHint = w.querySelector('[data-mw-seedp-fallback-hint]');
        if (spFbHint) spFbHint.textContent = t('wiz-seedp-fallback');
        // Foot
        w.querySelector('[data-mw-cancel]').textContent = t('btn-cancel');
        w.querySelector('[data-mw-prev]').textContent = t('btn-prev');
        w.querySelector('[data-mw-next]').textContent = t('btn-next');
    }

    // Fetch the seed-customer list for the wizard's Step-3 dropdown.
    // Returns null when no endpoint id is available (new wizard) OR
    // when the fetch errors — caller falls back to a text input.
    // 问题 c (Zihao 2026-05-19 拍板 · v118.34.26) · 加 60s client-side
    // timeout (AbortController) · 后端 listing fetch 30s × 3 = 90s worst case
    // · 客户端 60s 兜底超时 · 防 wizard UI 一直 "正在拉取客户列表..."
    async function _fetchSeedCustomers(endpointId) {
        if (!endpointId) return null;
        const ctrl = new AbortController();
        const tid = setTimeout(function () {
            ctrl.abort();
        }, 60_000);
        try {
            const r = await fetch(
                '/api/erp/endpoints/' + encodeURIComponent(endpointId) + '/customers',
                { headers: _authHeaders(), signal: ctrl.signal }
            );
            if (!r.ok) return null;
            const data = await r.json();
            if (!data || !data.ok) return null;
            return Array.isArray(data.customers) ? data.customers : [];
        } catch (e) {
            return null;
        } finally {
            clearTimeout(tid);
        }
    }

    async function _populateSeedSelector(currentSeedCode) {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seed]');
        const inputEl = w.querySelector('[data-mw-seed-input]');
        const fbHintEl = w.querySelector('[data-mw-seed-fallback-hint]');

        // Default both hidden until we know which one to show.
        selectEl.style.display = 'none';
        inputEl.style.display = 'none';
        fbHintEl.style.display = 'none';

        const endpointId = _wizardState && _wizardState.endpoint ? _wizardState.endpoint.id : null;

        // Stage 1: loading
        if (endpointId) {
            selectEl.innerHTML = '<option value="">' + _esc(t('wiz-seed-loading')) + '</option>';
            selectEl.style.display = '';
            selectEl.disabled = true;
        } else {
            // No endpoint persisted yet — go straight to text fallback.
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            return;
        }

        const customers = await _fetchSeedCustomers(endpointId);
        selectEl.disabled = false;

        if (customers === null || customers.length === 0) {
            // Fetch failed (or empty listing) → degrade to text input.
            selectEl.style.display = 'none';
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            inputEl.classList.add('mrerp-seed-input-saved');
            if (currentSeedCode) {
                fbHintEl.textContent = t('wiz-seed-fallback-saved', { code: currentSeedCode });
            } else {
                fbHintEl.textContent = t('wiz-seed-fallback');
            }
            fbHintEl.style.display = '';
            return;
        }
        inputEl.classList.remove('mrerp-seed-input-saved');

        // Populate the dropdown.
        const opts = ['<option value="">' + _esc(t('wiz-seed-empty')) + '</option>'];
        const inList = !!(
            currentSeedCode &&
            customers.some(function (c) {
                return c.code === currentSeedCode;
            })
        );
        // Bug 2 (Zihao 2026-05-19 拍板 · v118.34.22) · 已保存的 seed_customer_code
        // 不在当前 listing 时(可能在分页 page 2+)· 插一个合成 option 在顶部
        // 标记 "(已保存 · 未在当前列表)"· 用户能看出来 endpoint 配置里就是这个 ·
        // 不会被 fallback 到 listing[0] 误以为换了.
        if (currentSeedCode && !inList) {
            opts.push(
                '<option value="' +
                    _esc(currentSeedCode) +
                    '">' +
                    _esc(currentSeedCode + ' · ' + t('wiz-seed-saved-not-in-list')) +
                    '</option>'
            );
        }
        customers.forEach(function (c) {
            const label = (c.prefix ? c.prefix + ' ' : '') + (c.name || '') + ' (' + c.code + ')';
            opts.push('<option value="' + _esc(c.code) + '">' + _esc(label) + '</option>');
        });
        selectEl.innerHTML = opts.join('');
        if (currentSeedCode) {
            selectEl.value = currentSeedCode; // 总是显式 select 已保存的
        } else {
            selectEl.value = ''; // 没设 · 留 placeholder 选中
        }
        // 问题 B (Zihao 2026-05-19 拍板 · v118.34.25) · success path 显式 hide
        // input + fallback hint · 防 race / 上次 fallback 状态残留 → 下拉跟 hint
        // 同时显示的矛盾态.
        inputEl.style.display = 'none';
        fbHintEl.style.display = 'none';
    }

    function _readSeedValue() {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seed]');
        const inputEl = w.querySelector('[data-mw-seed-input]');
        if (selectEl && selectEl.style.display !== 'none') {
            return (selectEl.value || '').trim();
        }
        if (inputEl && inputEl.style.display !== 'none') {
            return (inputEl.value || '').trim();
        }
        return '';
    }

    // Task 2 Phase 5 · seed PRODUCT helpers (parallel to seed customer).
    // 问题 c (v118.34.26) · 加 60s client-side timeout 同 customer side.
    async function _fetchSeedProducts(endpointId) {
        if (!endpointId) return null;
        const ctrl = new AbortController();
        const tid = setTimeout(function () {
            ctrl.abort();
        }, 60_000);
        try {
            const r = await fetch(
                '/api/erp/endpoints/' + encodeURIComponent(endpointId) + '/products',
                { headers: _authHeaders(), signal: ctrl.signal }
            );
            if (!r.ok) return null;
            const data = await r.json();
            if (!data || !data.ok) return null;
            return Array.isArray(data.products) ? data.products : [];
        } catch (e) {
            return null;
        } finally {
            clearTimeout(tid);
        }
    }

    async function _populateSeedProductSelector(currentSeedCode) {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seedp]');
        const inputEl = w.querySelector('[data-mw-seedp-input]');
        const fbHintEl = w.querySelector('[data-mw-seedp-fallback-hint]');
        if (!selectEl || !inputEl) return;

        selectEl.style.display = 'none';
        inputEl.style.display = 'none';
        fbHintEl.style.display = 'none';

        const endpointId = _wizardState && _wizardState.endpoint ? _wizardState.endpoint.id : null;
        if (endpointId) {
            selectEl.innerHTML = '<option value="">' + _esc(t('wiz-seedp-loading')) + '</option>';
            selectEl.style.display = '';
            selectEl.disabled = true;
        } else {
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            return;
        }

        const products = await _fetchSeedProducts(endpointId);
        selectEl.disabled = false;
        if (products === null || products.length === 0) {
            selectEl.style.display = 'none';
            inputEl.style.display = '';
            inputEl.value = currentSeedCode || '';
            inputEl.classList.add('mrerp-seed-input-saved'); // 橙色边框 · 提示用户这是 fallback
            // v118.34.32 (Zihao 2026-05-19 拍板) · fb hint 文案 dynamic ·
            // 把 currentSeedCode 嵌入 · 让用户看出来是 "上次保存的值 · 可改"
            if (currentSeedCode) {
                fbHintEl.textContent = t('wiz-seedp-fallback-saved', { code: currentSeedCode });
            } else {
                fbHintEl.textContent = t('wiz-seedp-fallback');
            }
            fbHintEl.style.display = '';
            return;
        }
        // success path · clean input visual state
        inputEl.classList.remove('mrerp-seed-input-saved');
        const opts = ['<option value="">' + _esc(t('wiz-seedp-empty')) + '</option>'];
        const inList = !!(
            currentSeedCode &&
            products.some(function (p) {
                return p.code === currentSeedCode;
            })
        );
        // Bug 2 (v118.34.22) · 已保存 seed_product_code 不在 listing 时合成 option
        if (currentSeedCode && !inList) {
            opts.push(
                '<option value="' +
                    _esc(currentSeedCode) +
                    '">' +
                    _esc(currentSeedCode + ' · ' + t('wiz-seed-saved-not-in-list')) +
                    '</option>'
            );
        }
        products.forEach(function (p) {
            const label = (p.name || '') + ' (' + p.code + ')';
            opts.push('<option value="' + _esc(p.code) + '">' + _esc(label) + '</option>');
        });
        selectEl.innerHTML = opts.join('');
        if (currentSeedCode) {
            selectEl.value = currentSeedCode;
        } else {
            selectEl.value = '';
        }
        // 问题 B (v118.34.25) · 镜像 customer side · 显式 hide input + hint
        inputEl.style.display = 'none';
        fbHintEl.style.display = 'none';
    }

    function _readSeedProductValue() {
        const w = _wizardEl;
        const selectEl = w.querySelector('[data-mw-seedp]');
        const inputEl = w.querySelector('[data-mw-seedp-input]');
        if (selectEl && selectEl.style.display !== 'none') {
            return (selectEl.value || '').trim();
        }
        if (inputEl && inputEl.style.display !== 'none') {
            return (inputEl.value || '').trim();
        }
        return '';
    }

    function _gotoStep(n) {
        _wizardState.step = n;
        const w = _wizardEl;
        w.querySelectorAll('.mrerp-wizard-step').forEach(function (el) {
            el.classList.toggle('is-active', el.getAttribute('data-mw-step') === String(n));
        });
        w.querySelectorAll('[data-mw-dot]').forEach(function (el) {
            const dn = parseInt(el.getAttribute('data-mw-dot'), 10);
            el.classList.remove('is-active', 'is-done');
            if (dn < n) el.classList.add('is-done');
            else if (dn === n) el.classList.add('is-active');
        });
        w.querySelector('[data-mw-prev]').style.display = n > 1 ? '' : 'none';
        w.querySelector('[data-mw-next]').textContent = n === 3 ? t('btn-finish') : t('btn-next');
    }

    function _closeWizard() {
        if (!_wizardEl) return;
        _wizardEl.classList.remove('is-open');
        _wizardState = null;
    }

    async function _openWizard(endpoint) {
        _ensureWizardDom();
        _applyWizardI18n();
        _wizardState = {
            step: 1,
            endpoint: endpoint || null,
            client_ids: (endpoint && endpoint.config && endpoint.config.client_ids) || [],
            companies: [],
        };
        // Reset inputs
        const w = _wizardEl;
        w.querySelector('[data-mw-user]').value = '';
        w.querySelector('[data-mw-pass]').value = '';
        w.querySelector('[data-mw-test-status]').textContent = t('wiz-test-pending');
        w.querySelector('[data-mw-test-error]').style.display = 'none';
        const seedSel = w.querySelector('[data-mw-seed]');
        seedSel.innerHTML = '<option value="">' + _esc(t('wiz-seed-empty')) + '</option>';

        // Step 1 — load Pearnly clients
        const clientsBox = w.querySelector('[data-mw-clients]');
        clientsBox.innerHTML = '<div class="mrerp-card-empty">…</div>';
        try {
            const r = await fetch('/api/clients?limit=200', { headers: _authHeaders() });
            if (r.ok) {
                const data = await r.json();
                const items = (data && (data.items || data.clients)) || [];
                const preSelected = new Set((_wizardState.client_ids || []).map(String));
                if (items.length === 0) {
                    clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
                } else {
                    clientsBox.innerHTML = items
                        .map(function (c) {
                            const id = String(c.id || c.client_id || '');
                            const checked = preSelected.has(id) ? ' checked' : '';
                            return (
                                '<label class="mrerp-wizard-checkbox-row">' +
                                '<input type="checkbox" data-mw-client value="' +
                                _esc(id) +
                                '"' +
                                checked +
                                '>' +
                                '<span>' +
                                _esc(c.name || c.client_name || '#' + id) +
                                '</span>' +
                                '</label>'
                            );
                        })
                        .join('');
                }
            } else {
                clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
            }
        } catch (e) {
            clientsBox.innerHTML = '<div class="mrerp-card-empty">—</div>';
        }

        _gotoStep(1);
        _wizardEl.classList.add('is-open');
        // Focus the username on Step 2 entry; for now nothing special
        // until user clicks Next.
    }

    function _wizardPrev() {
        if (_wizardState.step > 1) _gotoStep(_wizardState.step - 1);
    }

    async function _wizardNext() {
        if (_wizardState.step === 1) {
            // Collect selected clients
            const ids = [].slice
                .call(_wizardEl.querySelectorAll('[data-mw-client]:checked'))
                .map(function (cb) {
                    return cb.value;
                });
            // Bug 1 (Zihao 2026-05-19 拍板 · v118.34.22) · 至少选 1 客户才能 Next ·
            // 否则保存的 endpoint 没绑任何客户 · 推送时 history.client_id 找不到
            // 关联 → ERR_NO_CLIENT 一连串失败。前端先拦住 · 配合后端 validator 双保险.
            if (!ids.length) {
                _toast(t('wiz-step-1-need-client'), 'warn');
                return;
            }
            _wizardState.client_ids = ids;
            _gotoStep(2);
            setTimeout(function () {
                _wizardEl.querySelector('[data-mw-user]').focus();
            }, 30);
            return;
        }
        if (_wizardState.step === 2) {
            // Move to step 3; populate company + seed dropdown.
            const companies = _wizardState.companies || [];
            const sel = _wizardEl.querySelector('[data-mw-company]');
            sel.innerHTML = companies.length
                ? companies
                      .map(function (c) {
                          return (
                              '<option value="' +
                              _esc(c.comidyear) +
                              ':' +
                              _esc(c.seldb) +
                              '">' +
                              _esc(c.label) +
                              '</option>'
                          );
                      })
                      .join('')
                : '<option value="6:1">' + _esc('TEST2019') + '</option>';

            _gotoStep(3);
            // Seed customer dropdown (Task 1) — async populate from
            // /api/erp/endpoints/:id/customers when editing an
            // existing endpoint. Falls back to text input on new
            // wizard or fetch failure.
            const currentSeed =
                (_wizardState.endpoint &&
                    _wizardState.endpoint.config &&
                    _wizardState.endpoint.config.seed_customer_code) ||
                '';
            _populateSeedSelector(currentSeed);
            // Seed product dropdown (Task 2 Phase 5).
            const currentSeedP =
                (_wizardState.endpoint &&
                    _wizardState.endpoint.config &&
                    _wizardState.endpoint.config.seed_product_code) ||
                '';
            _populateSeedProductSelector(currentSeedP);
            return;
        }
        // Step 3 → finish
        await _wizardFinish();
    }

    async function _wizardRunTest() {
        const w = _wizardEl;
        const username = w.querySelector('[data-mw-user]').value.trim();
        const password = w.querySelector('[data-mw-pass]').value;
        const statusEl = w.querySelector('[data-mw-test-status]');
        const errBox = w.querySelector('[data-mw-test-error]');
        errBox.style.display = 'none';
        if (!username || !password) {
            statusEl.textContent = t('wiz-test-pending');
            return;
        }
        statusEl.textContent = t('wiz-test-running');

        // Use the legacy /api/erp/test-connection endpoint for the
        // wizard (the per-endpoint route only works for already-
        // persisted endpoints; this one tests config in-memory).
        try {
            const r = await fetch('/api/erp/test-connection', {
                method: 'POST',
                headers: _authHeaders(),
                body: JSON.stringify({
                    adapter: 'mrerp',
                    config: {
                        system_url: 'https://www.mrerp4sme.com',
                        // v118.34.2 (Zihao 2026-05-19) · plaintext path.
                        // Backend test_mrerp_endpoint accepts both
                        // {username, password} (plain, this wizard call)
                        // and {username_enc, password_enc} (Fernet,
                        // saved endpoint reload). Sending plain avoids
                        // a pointless server-side encrypt+decrypt
                        // round-trip and shrinks the failure surface.
                        username: username,
                        password: password,
                        comidyear: '6',
                        seldb: '1',
                    },
                }),
            });
            let data;
            try {
                data = await r.json();
            } catch (_je) {
                data = {
                    ok: false,
                    error_code: 'ERR_HTTP_' + r.status,
                    raw_error: await r.text().catch(() => ''),
                };
            }
            if (!r.ok && !data) {
                data = { ok: false, error_code: 'ERR_HTTP_' + r.status };
            }
            if (data.ok || data.success) {
                _wizardState.companies = data.companies || [];
                statusEl.textContent = t('wiz-test-ok', { n: (data.companies || []).length || 1 });
                // 成功时清掉旧截图提示
                const shotEl = w.querySelector('[data-mw-test-error-screenshot]');
                if (shotEl) {
                    shotEl.textContent = '';
                    shotEl.style.display = 'none';
                }
            } else {
                // v118.34.1 (Zihao 2026-05-19 拍板) · 错误条不能空白。
                // 优先级:friendly[lang] > friendly.en > raw_error >
                // error_msg (legacy shape) > response_body (legacy stub) >
                // error_code > generic fallback。至少一条文字一定要落出。
                const f = data.error_friendly || {};
                const friendly =
                    f[_activeLang()] ||
                    f.en ||
                    data.raw_error ||
                    data.error_msg ||
                    data.response_body ||
                    data.error_code ||
                    'HTTP ' + (r.status || 0) + ' · connection failed';
                statusEl.textContent = '✗';
                errBox.style.display = '';
                w.querySelector('[data-mw-test-error-friendly]').textContent = String(
                    friendly
                ).slice(0, 400);
                // P-4 (Zihao 2026-05-19 拍板 · v118.34.21) · login-form 失败后端把
                // 截图路径塞进 raw_error 字串("...screenshot=/tmp/mrerp_login_fail_<ts>.png")
                // 在 dense raw_error block 里被 hidden。这里把它正则抽出来 ·
                // 单独显示在 friendly + raw 之间 · 用户一眼看到能 scp 给客服。
                const shotEl = w.querySelector('[data-mw-test-error-screenshot]');
                const rawText = String(data.raw_error || data.response_body || '');
                const shotMatch = rawText.match(/screenshot=(\S+\.png)/i);
                if (shotEl) {
                    if (shotMatch) {
                        shotEl.textContent = t('wiz-screenshot-saved', { path: shotMatch[1] });
                        shotEl.style.display = '';
                    } else {
                        shotEl.textContent = '';
                        shotEl.style.display = 'none';
                    }
                }
                w.querySelector('[data-mw-test-error-raw]').textContent = rawText.slice(0, 400);
            }
        } catch (e) {
            statusEl.textContent = '✗';
            errBox.style.display = '';
            w.querySelector('[data-mw-test-error-friendly]').textContent = String(
                (e && e.message) || e || 'connection failed'
            ).slice(0, 200);
            w.querySelector('[data-mw-test-error-raw]').textContent = '';
            const shotEl = w.querySelector('[data-mw-test-error-screenshot]');
            if (shotEl) {
                shotEl.textContent = '';
                shotEl.style.display = 'none';
            }
        }
    }

    async function _wizardFinish() {
        const w = _wizardEl;
        const username = w.querySelector('[data-mw-user]').value.trim();
        const password = w.querySelector('[data-mw-pass]').value;
        const companyChoice = w.querySelector('[data-mw-company]').value || '6:1';
        const [comidyear, seldb] = companyChoice.split(':');
        const mode = w.querySelector('input[name="mrerp-mode"]:checked').value;
        const seed = _readSeedValue();
        const seedProduct = _readSeedProductValue();

        if (!username || !password) {
            _toast(t('wiz-fill-creds'), 'warn');
            _gotoStep(2);
            return;
        }

        const config = {
            system_url: 'https://www.mrerp4sme.com',
            // v118.34.4 · save endpoint also takes plaintext (server-
            // side storage layer encrypts before writing to db). The
            // _enc-suffixed names are kept for backward compat with the
            // existing save route contract — content is plaintext here
            // and the route encrypts on insert.
            username_enc: username,
            password_enc: password,
            comidyear: comidyear,
            seldb: seldb,
            client_ids: _wizardState.client_ids || [],
            seed_customer_code: seed || null,
            seed_product_code: seedProduct || null,
        };
        const body = {
            name: 'MR.ERP',
            adapter: 'mrerp',
            config: config,
            is_default: false,
            auto_push: mode === 'auto',
        };

        try {
            const url = _wizardState.endpoint
                ? '/api/erp/endpoints/' + encodeURIComponent(_wizardState.endpoint.id)
                : '/api/erp/endpoints';
            const method = _wizardState.endpoint ? 'PATCH' : 'POST';
            const r = await fetch(url, {
                method: method,
                headers: _authHeaders(),
                body: JSON.stringify(body),
            });
            if (!r.ok) {
                _toast(t('wiz-save-failed', { status: r.status }), 'error');
                return;
            }
            _toast(t('wiz-saved'), 'success');
            _closeWizard();
            setTimeout(_bootstrap, 100);
        } catch (e) {
            _toast(String(e).slice(0, 200), 'error');
        }
    }

    // Replace the no-op stub with the real handler.
    window._mrerpOpenWizard = _openWizard;
})();
