# -*- coding: utf-8 -*-
"""ERP 推送失败码 → 4 语友好文案(从 push_log_queries 抽出 · 纯数据 + 查表)。

发票推送 catalog(mrerp_business_friendly.friendly_for_ui)只覆盖 ERR_* 发票推送码;
身份证→订车单(adapter=mrerp_dms)有独立一组 ERR_DMS_* 码,friendly_for_ui 不覆盖 →
不补就在日志/详情/异常里裸露 ERR_*(Zihao 2026-06-01 指出)。friendly_any 统一入口:
发票优先 → 身份证订车兜底。push 日志/详情/异常三处共用。
覆盖范围(自下而上兜底):发票 catalog → 单据防呆码 → DMS 订车码 → Express 库存码
→ Express 桥接层码(READBACK_VERIFY_FAILED / agent_failed / bridge.failed /
ERR_EXPRESS_DISABLED)→ 纯技术态兜底(connection error / ERP 建单超时 / push failed /
目标系统返 HTML 页)。凡带码的 error_msg 都应落到对应层,不向用户裸露内部码。
"""

from typing import Optional, Dict

from services.erp.mrerp_business_friendly import friendly_for_ui

# 身份证→订车单推送/识别错误码的 4 语友好文案(zh/th/en/ja)。
_DMS_PUSH_FRIENDLY: Dict[str, Dict[str, str]] = {
    "ERR_ID_CARD_REQUIRED_FIELDS": {
        "zh": "身份证关键字段未识别完整(身份证号或姓名)· 已暂停建单 · 请用清晰的正面照重新识别",
        "en": "Key ID-card fields (ID number or name) were not fully recognized; booking was paused. Please rescan a clear front image.",
        "th": "อ่านข้อมูลบัตรประชาชนหลัก (เลขบัตร/ชื่อ) ไม่ครบ จึงหยุดสร้างใบจอง กรุณาสแกนภาพด้านหน้าที่ชัดเจนอีกครั้ง",
        "ja": "身分証の主要項目(番号・氏名)を完全に読み取れず、予約作成を停止しました。鮮明な表面の画像で再読み取りしてください。",
    },
    "ERR_DMS_CUSTOMER_CREATE": {
        "zh": "在 DMS 建客户失败 · 请检查身份证上的地址信息后重试",
        "en": "Failed to create the customer in DMS. Please check the address on the ID card and retry.",
        "th": "สร้างลูกค้าใน DMS ไม่สำเร็จ กรุณาตรวจสอบที่อยู่บนบัตรประชาชนแล้วลองใหม่",
        "ja": "DMS での顧客作成に失敗しました。身分証の住所をご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT_REPORT": {
        "zh": "订车单导入 DMS 时被退回(数据校验未过)· 请核对身份证信息后重试",
        "en": "DMS rejected the booking import (data validation failed). Please verify the ID-card data and retry.",
        "th": "DMS ปฏิเสธการนำเข้าใบจอง (ตรวจสอบข้อมูลไม่ผ่าน) กรุณาตรวจสอบข้อมูลบัตรแล้วลองใหม่",
        "ja": "DMS が予約の取り込みを拒否しました(データ検証エラー)。身分証データをご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT": {
        "zh": "订车单导入 DMS 失败 · 请稍后重试",
        "en": "Failed to import the booking into DMS. Please retry shortly.",
        "th": "นำเข้าใบจองรถไปยัง DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "予約データの DMS への取り込みに失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_BOOKING_PATCH": {
        "zh": "订车单已建但补充资料失败 · 请到 DMS 后台核对该单",
        "en": "The booking was created but updating its details failed. Please verify it in the DMS console.",
        "th": "สร้างใบจองแล้วแต่บันทึกรายละเอียดเพิ่มเติมไม่สำเร็จ กรุณาตรวจสอบใบจองในระบบ DMS",
        "ja": "予約は作成されましたが詳細の更新に失敗しました。DMS 管理画面でご確認ください。",
    },
    # 销售顾问 = DMS 提成归属,建单前必须定死(2026-08-11)。这两码只可能出在订车路径。
    "ERR_DMS_ADVISOR_REQUIRED": {
        "zh": "这张订车单没有销售顾问 · 系统不会替你猜提成算给谁 · 请让管理员为该 DMS 账号配置销售顾问,然后重新开单",
        "en": "This booking has no sales advisor, and the system will not guess who the commission belongs to. Ask your admin to configure the advisor for this DMS account, then create the booking again.",
        "th": "ใบจองนี้ไม่มีที่ปรึกษาการขาย ระบบจะไม่เดาว่าค่าคอมมิชชั่นเป็นของใคร กรุณาให้ผู้ดูแลกำหนดที่ปรึกษาให้บัญชี DMS นี้ แล้วเปิดใบจองใหม่อีกครั้ง",
        "ja": "この予約には販売アドバイザーが設定されておらず、システムが歩合の帰属を推測することはありません。管理者に該当 DMS アカウントのアドバイザー設定を依頼し、予約を作成し直してください。",
    },
    "ERR_DMS_ADVISOR_UNMATCHED": {
        "zh": "这个销售顾问不在 DMS 的顾问名册里 · 请让管理员在 DMS 顾问名册补上这个账号,或联系 Pearnly 为该账号指定归属,然后重新开单",
        "en": "This sales advisor is not in the DMS advisor list. Ask your admin to add this account to the DMS advisor list, or contact Pearnly to assign one, then create the booking again.",
        "th": "ที่ปรึกษาการขายรายนี้ไม่อยู่ในรายชื่อที่ปรึกษาของ DMS กรุณาให้ผู้ดูแลเพิ่มบัญชีนี้ในรายชื่อที่ปรึกษาการขายของ DMS หรือติดต่อทีม Pearnly เพื่อกำหนดให้ แล้วเปิดใบจองใหม่",
        "ja": "この販売アドバイザーは DMS のアドバイザー名簿にありません。管理者に当該アカウントの追加を依頼するか、Pearnly に割り当てを依頼したうえで、予約を作成し直してください。",
    },
    "ERR_DMS_TEMPLATE": {
        "zh": "获取 DMS 订车单模板失败 · 请稍后重试",
        "en": "Failed to fetch the DMS booking template. Please retry shortly.",
        "th": "ดึงแม่แบบใบจองของ DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "DMS の予約テンプレート取得に失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_AUTH": {
        "zh": "DMS 登录失败 · 请到连接向导检查账号和密码",
        "en": "DMS login failed. Please check the username and password in the connection wizard.",
        "th": "เข้าสู่ระบบ DMS ไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่านในตัวช่วยเชื่อมต่อ",
        "ja": "DMS へのログインに失敗しました。連携ウィザードでユーザー名とパスワードをご確認ください。",
    },
    "ERR_DMS_NOT_INVOICE_ENDPOINT": {
        "zh": "该连接是身份证订车专用 · 不能用于推送发票",
        "en": "This connection is for ID-card vehicle booking only and cannot push invoices.",
        "th": "การเชื่อมต่อนี้ใช้สำหรับการจองรถด้วยบัตรประชาชนเท่านั้น ไม่สามารถส่งใบกำกับได้",
        "ja": "この連携は身分証による車両予約専用で、請求書の送信には使用できません。",
    },
    "ERR_DMS_TECHNICAL": {
        "zh": "连接 DMS 超时或网络异常 · 请稍后重试",
        "en": "DMS connection timed out or a network error occurred. Please retry shortly.",
        "th": "การเชื่อมต่อ DMS หมดเวลาหรือเครือข่ายขัดข้อง กรุณาลองใหม่ภายหลัง",
        "ja": "DMS への接続がタイムアウトまたはネットワーク異常です。しばらくしてから再試行してください。",
    },
    "ERR_DMS_CONCURRENT_LOGIN": {
        "zh": "DMS 账号正在其他地方使用 · 请退出其他登录后重试",
        "en": "This DMS account is being used elsewhere. Sign out there and retry.",
        "th": "บัญชี DMS นี้กำลังถูกใช้งานที่อื่น กรุณาออกจากระบบที่อื่นแล้วลองใหม่",
        "ja": "この DMS アカウントは別の場所で使用中です。他の場所からログアウトして再試行してください。",
    },
    "ERR_DMS_UNEXPECTED": {
        "zh": "推送 DMS 时发生未知错误 · 请稍后重试或联系客服",
        "en": "An unexpected error occurred while pushing to DMS. Please retry or contact support.",
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิดขณะส่งไป DMS กรุณาลองใหม่หรือติดต่อฝ่ายสนับสนุน",
        "ja": "DMS への送信中に予期しないエラーが発生しました。再試行するかサポートにお問い合わせください。",
    },
    "ERR_DMS_ADMIN_AUTH": {
        "zh": "DMS 管理员凭据登录失败 · 请检查管理员账号密码设置后重试",
        "en": "DMS admin-credential login failed. Please check the admin username and password settings, then retry.",
        "th": "เข้าสู่ระบบด้วยบัญชีผู้ดูแล DMS ไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่านของผู้ดูแลแล้วลองใหม่",
        "ja": "DMS 管理者アカウントでのログインに失敗しました。管理者のユーザー名とパスワード設定を確認して再試行してください。",
    },
    "ERR_DMS_CUSTOMER_SAVE": {
        "zh": "客户资料保存到 DMS 失败 · 请检查身份证识别出的姓名与地址后重试",
        "en": "Saving the customer to DMS failed. Please check the recognized name and address from the ID card, then retry.",
        "th": "บันทึกข้อมูลลูกค้าลง DMS ไม่สำเร็จ กรุณาตรวจสอบชื่อและที่อยู่ที่อ่านได้จากบัตรประชาชนแล้วลองใหม่",
        "ja": "顧客情報の DMS への保存に失敗しました。身分証から読み取った氏名と住所を確認して再試行してください。",
    },
    "ERR_DMS_ORDER_FAILED": {
        "zh": "在 DMS 建订车单失败 · 请稍后重试;若反复失败请到 DMS 后台确认是否已生成该单",
        "en": "Failed to create the booking in DMS. Please retry shortly; if it keeps failing, check in DMS whether the booking was created.",
        "th": "สร้างใบจองใน DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง หากยังไม่สำเร็จโปรดตรวจในระบบ DMS ว่ามีใบจองแล้วหรือยัง",
        "ja": "DMS での予約作成に失敗しました。しばらくして再試行し、繰り返し失敗する場合は DMS 側で予約が作成済みか確認してください。",
    },
    "ERR_PLAYWRIGHT_MISSING": {
        "zh": "服务器组件缺失(浏览器引擎)· 系统问题,请联系支持处理",
        "en": "A server component (browser engine) is missing. This is a system issue — please contact support.",
        "th": "องค์ประกอบฝั่งเซิร์ฟเวอร์ขาดหายไป เป็นปัญหาของระบบ กรุณาติดต่อฝ่ายสนับสนุน",
        "ja": "サーバー側コンポーネント(ブラウザエンジン)が不足しています。システム側の問題のため、サポートへご連絡ください。",
    },
    "ERR_KMS_MISSING": {
        "zh": "服务器密钥配置缺失 · 系统问题,请联系支持处理",
        "en": "The server encryption key is not configured. This is a system issue — please contact support.",
        "th": "การตั้งค่ากุญแจเข้ารหัสฝั่งเซิร์ฟเวอร์ขาดหายไป เป็นปัญหาของระบบ กรุณาติดต่อฝ่ายสนับสนุน",
        "ja": "サーバーの暗号化キーが未設定です。システム側の問題のため、サポートへご連絡ください。",
    },
}


def dms_push_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中身份证订车错误码 → 返回 {zh,th,en,ja} dict;否则 None。
    按码长度降序匹配(长码先于其前缀短码,如 ERR_DMS_IMPORT_REPORT 先于 ERR_DMS_IMPORT)
    防子串误命中 · 新增码进 _DMS_PUSH_FRIENDLY 即自动生效,无需再维护一份顺序列表。"""
    if not error_msg:
        return None
    for code in sorted(_DMS_PUSH_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _DMS_PUSH_FRIENDLY[code]
    return None


# Express 本地小助手「库存过账」回执码 —— 不带 ERR_ 前缀,作为 error_msg 子串出现
# (DBF_WRITE_FAILED 账套无库存品主档/泰文写盘崩 · STOCK_ITEM_NOT_FOUND 无档案或零负库存 ·
# STOCK_IN_FAILED 采购入库整条路的失败)。未收录时原始码直接裸露给泰国会计看(2026-07-23 真料排障 F1)。
_EXPRESS_STOCK_FRIENDLY: Dict[str, Dict[str, str]] = {
    "DBF_WRITE_FAILED": {
        "zh": "写入 Express 账套失败 · 常见于该账套还没有库存商品主档 · 请先在 Express 建好库存商品,或本批改用「服务·非库存」模式推送",
        "en": "Failed to write into the Express account set — commonly because the set has no stock-item master yet. Please create a stock item in Express first, or push this batch in the “Service · Non-stock” mode.",
        "th": "เขียนข้อมูลลงชุดบัญชี Express ไม่สำเร็จ มักเป็นเพราะชุดบัญชียังไม่มีสินค้าคงคลังตั้งต้น กรุณาสร้างสินค้าคงคลังใน Express ก่อน หรือส่งชุดนี้ด้วยโหมด «บริการ · ไม่ใช่สินค้าคงคลัง»",
        "ja": "Express の帳簿セットへの書き込みに失敗しました。多くは在庫品マスタが未作成のためです。先に Express で在庫品を作成するか、本バッチを「サービス・非在庫」モードで送信してください。",
    },
    # 采购入库路的失败全归这一码(混行/超购货额/缺科目/数量非法)· 会计分不清是哪支,故按最常撞上的顺序给动作。
    "STOCK_IN_FAILED": {
        "zh": "这张进货票没能入库 · 请依次检查:票里库存品和非库存品是否混在一起(混了就拆成两张分别推)· 明细行的数量/金额是否与票面一致 · 账套是否已配存货和销售成本科目",
        "en": "This purchase invoice could not be booked into stock. Check in order: stock and non-stock lines mixed on one invoice (split them and push separately), line quantities/amounts not matching the invoice, and whether the account set has inventory and COGS accounts configured.",
        "th": "ใบซื้อนี้ลงสต๊อกไม่สำเร็จ กรุณาตรวจตามลำดับ: มีสินค้าคงคลังปนกับสินค้าที่ไม่ใช่คงคลังในใบเดียวกันหรือไม่ (ถ้าปนให้แยกเป็นสองใบแล้วส่งแยกกัน) · จำนวนและมูลค่าในรายการตรงกับหน้าใบหรือไม่ · ชุดบัญชีตั้งบัญชีสินค้าคงเหลือและต้นทุนขายแล้วหรือยัง",
        "ja": "この仕入請求書は在庫計上できませんでした。順に確認してください:1 枚に在庫品と非在庫品が混在していないか(混在なら 2 枚に分けて送信)· 明細の数量/金額が請求書と一致しているか · 会計セットに棚卸資産と売上原価の勘定が設定されているか。",
    },
    "STOCK_ITEM_NOT_FOUND": {
        "zh": "这件商品在 Express 里还没有库存档案,或库存为零/不足 · 请先把它的进货票用「库存」模式推一次(或补录期初库存),再推这张销售票",
        "en": "This item has no stock record in Express yet, or its stock is zero/insufficient. Push its purchase invoice in Inventory mode first (or fill in the opening balance), then push this sales invoice again.",
        "th": "สินค้านี้ยังไม่มีทะเบียนสต๊อกใน Express หรือสต๊อกเป็นศูนย์/ไม่เพียงพอ กรุณาส่งใบซื้อของสินค้านี้ด้วยโหมดสินค้า (คงคลัง) ก่อน หรือกรอกยอดยกมา แล้วจึงส่งใบขายนี้อีกครั้ง",
        "ja": "この商品は Express に在庫マスタが未登録、または在庫がゼロ/不足です。先にこの商品の仕入請求書を在庫モードで送信するか期首在庫を登録してから、この売上請求書を再送信してください。",
    },
}


def express_stock_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中 Express 库存过账回执码 → 4 语 dict;否则 None。与 dms_push_friendly 同款:
    按码长度降序子串匹配,新增码进表即生效。"""
    if not error_msg:
        return None
    for code in sorted(_EXPRESS_STOCK_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _EXPRESS_STOCK_FRIENDLY[code]
    return None


# Express 本地小助手「桥接层」回执码 —— READBACK_VERIFY_FAILED 是结构化码(写入后核对
# 行数不符 → 防重复入账已自动撤销);agent_failed / bridge.failed 是小写码,作为 error_msg
# 原样子串出现(不做大小写归一);ERR_EXPRESS_DISABLED 是开关未开的码。
_COMPANION_BRIDGE_FRIENDLY: Dict[str, Dict[str, str]] = {
    "READBACK_VERIFY_FAILED": {
        "zh": "这张单据在 Express 里已有相同明细(写入后核对行数不符)· 为防重复入账已自动撤销本次写入 · 请到 Express 检查该单号:若单据已存在且正确则无需处理;若要重推,请先在 Express 删除旧单",
        "en": "Express already contains matching lines for this document (post-write verification found a line-count mismatch). This write was rolled back to prevent double booking. Check this document number in Express: if it already exists and is correct, no action is needed; to re-push, delete the old document in Express first.",
        "th": "เอกสารนี้มีรายการอยู่ใน Express อยู่แล้ว (ตรวจทานหลังบันทึกพบจำนวนรายการไม่ตรง) ระบบได้ยกเลิกการบันทึกครั้งนี้เพื่อป้องกันการลงบัญชีซ้ำ กรุณาตรวจสอบเลขที่เอกสารนี้ใน Express ถ้ามีอยู่แล้วและถูกต้อง ไม่ต้องทำอะไร ถ้าต้องการส่งใหม่ กรุณาลบเอกสารเดิมใน Express ก่อน",
        "ja": "この伝票は Express に同じ明細が既に存在します(書き込み後の検証で行数不一致)。二重計上を防ぐため今回の書き込みは取り消されました。Express で該当伝票番号を確認し、既に正しく存在する場合は対応不要、再送信する場合は先に旧伝票を削除してください。",
    },
    "agent_failed": {
        "zh": "本地小助手推送失败但未返回原因 · 请在小助手窗口查看这张单的失败详情后重试",
        "en": "The local companion failed to push this document but returned no reason. Check the failure details in the companion window, then retry.",
        "th": "โปรแกรมผู้ช่วยส่งเอกสารนี้ไม่สำเร็จโดยไม่ได้แจ้งสาเหตุ กรุณาดูรายละเอียดในหน้าต่างโปรแกรมผู้ช่วยแล้วลองใหม่",
        "ja": "ローカルアシスタントの送信が失敗しましたが、理由が返されませんでした。アシスタントの画面で詳細を確認して再試行してください。",
    },
    "bridge.failed": {
        "zh": "推送通道返回了未知错误 · 请重试一次;若仍失败请联系支持",
        "en": "The push channel returned an unknown error. Please retry once; contact support if it persists.",
        "th": "ช่องทางการส่งตอบกลับข้อผิดพลาดที่ไม่รู้จัก กรุณาลองใหม่อีกครั้ง หากยังไม่สำเร็จโปรดติดต่อฝ่ายสนับสนุน",
        "ja": "送信チャネルが不明なエラーを返しました。もう一度お試しください。解決しない場合はサポートへご連絡ください。",
    },
    "ERR_EXPRESS_DISABLED": {
        "zh": "Express 推送功能当前未开启 · 请联系支持开通后再推送",
        "en": "Express push is currently not enabled. Please contact support to enable it, then push again.",
        "th": "ฟีเจอร์ส่งไป Express ยังไม่ถูกเปิดใช้งาน กรุณาติดต่อฝ่ายสนับสนุนเพื่อเปิดใช้งานก่อนแล้วจึงส่งใหม่",
        "ja": "Express への送信機能が現在有効になっていません。サポートに連絡して有効化した後、再送信してください。",
    },
}


def companion_bridge_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中 Express 桥接层回执码 → 4 语 dict;否则 None。与 dms_push_friendly 同款:
    按码长降序子串匹配。agent_failed / bridge.failed 是小写码,原样子串匹配,不做大小写归一。"""
    if not error_msg:
        return None
    for code in sorted(_COMPANION_BRIDGE_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _COMPANION_BRIDGE_FRIENDLY[code]
    return None


def _doc_sanity_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """单据防呆码(date_implausible/currency_not_thb 等)四语化 · 复用 routing 唯一目录。
    此前只翻 ERR_*,doc_sanity 码在 LINE 失败消息里裸奔(真机 2026-07-02 截图抓到)。"""
    msg = str(error_msg or "")
    if not msg:
        return None
    try:
        from services.erp.mrerp_http.routing import _DOC_SANITY_FRIENDLY

        return next((tr for pfx, tr in _DOC_SANITY_FRIENDLY.items() if pfx in msg), None)
    except Exception:
        return None


def _tech_fallback_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """纯技术性 error_msg(没有可查码)的技术态 4 语兜底,按序判:
    连不上目标系统 → ERP 建单超时 → 裸 "push failed" → 目标系统返了 HTML 页而不是数据。
    都不中返回 None。"""
    msg = str(error_msg or "").strip()
    if not msg:
        return None
    low = msg.lower()
    if low.startswith("connection error"):
        return {
            "zh": "连不上目标系统(网络错误)· 请确认网络与小助手在线后重试",
            "en": "Could not reach the target system (network error). Check the network and the companion, then retry.",
            "th": "เชื่อมต่อระบบปลายทางไม่สำเร็จ (เครือข่ายขัดข้อง) กรุณาตรวจสอบเครือข่ายและโปรแกรมผู้ช่วยแล้วลองใหม่",
            "ja": "送信先システムに接続できませんでした(ネットワークエラー)。ネットワークとアシスタントを確認して再試行してください。",
        }
    if "timeout while creating erp document" in low:
        return {
            "zh": "在 ERP 建单超时 · 系统会自动重试,无需操作",
            "en": "Creating the ERP document timed out. The system will retry automatically — no action needed.",
            "th": "สร้างเอกสารใน ERP หมดเวลา ระบบจะลองใหม่ให้อัตโนมัติ ไม่ต้องดำเนินการ",
            "ja": "ERP での伝票作成がタイムアウトしました。自動的に再試行されます。操作は不要です。",
        }
    if msg == "push failed":
        return {
            "zh": "推送未成功 · 请重试;若持续失败请联系支持",
            "en": "The push did not succeed. Please retry; contact support if it persists.",
            "th": "ส่งไม่สำเร็จ กรุณาลองใหม่ หากยังไม่สำเร็จโปรดติดต่อฝ่ายสนับสนุน",
            "ja": "送信に失敗しました。再試行し、解決しない場合はサポートへご連絡ください。",
        }
    if low.startswith("<!doctype") or low.startswith("<html"):
        return {
            "zh": "目标系统返回了异常页面而不是数据 · 请稍后重试;若持续出现请联系支持",
            "en": "The target system returned an unexpected web page instead of data. Please retry later; contact support if it persists.",
            "th": "ระบบปลายทางตอบกลับเป็นหน้าเว็บผิดปกติแทนข้อมูล กรุณาลองใหม่ภายหลัง หากยังพบโปรดติดต่อฝ่ายสนับสนุน",
            "ja": "送信先システムがデータではなく異常なページを返しました。後で再試行し、続く場合はサポートへご連絡ください。",
        }
    return None


def friendly_any(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """发票推送 catalog 优先(friendly_for_ui)→ 单据防呆码 → 身份证订车 → Express 库存码
    → Express 桥接层 → 技术态兜底。给 push 日志/详情/异常/LINE 失败消息统一用。
    任一命中即不裸露内部码 / 裸技术文案。"""
    return (
        friendly_for_ui(error_msg)
        or _doc_sanity_friendly(error_msg)
        or dms_push_friendly(error_msg)
        or express_stock_friendly(error_msg)
        or companion_bridge_friendly(error_msg)
        or _tech_fallback_friendly(error_msg)
    )


def friendly_text(error_msg: Optional[str], lang: str, fallback: str = "") -> str:
    """friendly_any 的取词版:命中给 lang(回落 en),未命中给 fallback。
    LINE 侧三处各写一遍"hit.get(lang) or hit['en']"收敛到这(/simplify 2026-07-03)。"""
    hit = friendly_any(error_msg) or {}
    return hit.get(lang) or hit.get("en") or fallback
