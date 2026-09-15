"""Messages shared by DMS booking execution and push history."""

BOOKING_MAPPING_ERRORS = {
    "ERR_DMS_BOOKING_ATTEMPT_BLOCKED": {
        "zh": "本次订车草稿已改变，或已有提交记录，已停止再次发送。请查看当前草稿和推送记录。",
        "zh_TW": "本次訂車草稿已改變，或已有提交紀錄，已停止再次送出。請查看目前草稿和推送紀錄。",
        "en": "This booking draft changed or already has a submission attempt. No new request was sent. Check the current draft and push history.",
        "th": "ร่างใบจองนี้เปลี่ยนไปหรือมีประวัติส่งแล้ว จึงไม่ได้ส่งคำขอใหม่ กรุณาตรวจสอบร่างปัจจุบันและประวัติการส่ง",
        "ja": "下書きが変更されたか、既に送信記録があるため、新たなリクエストは送信していません。現在の下書きと送信履歴をご確認ください。",
    },
    "ERR_DMS_BOOKING_OUTCOME_UNKNOWN": {
        "zh": "订车请求已发送，但尚未核实 DMS 单据结果。请勿重复提交，请联系管理员按本次单号核对。",
        "zh_TW": "訂車請求已送出，但尚未核實 DMS 單據結果。請勿重複提交，請聯絡管理員按本次單號核對。",
        "en": "The booking request was sent, but the DMS result is unverified. Do not submit again. Ask an administrator to check this booking number.",
        "th": "ส่งคำขอจองแล้ว แต่ยังตรวจสอบผลใน DMS ไม่ได้ กรุณาอย่าส่งซ้ำ ให้ผู้ดูแลตรวจสอบตามเลขที่รายการนี้",
        "ja": "予約リクエストは送信されましたが、DMS の登録結果を確認できません。再送信せず、管理者に今回の番号で確認を依頼してください。",
    },
    "ERR_DMS_PAYMENT_INCOMPLETE": {
        "zh": "订车尚未提交：收款资料不完整。草稿已保留，请补齐账户信息后重新确认。",
        "zh_TW": "訂車尚未提交：收款資料不完整。草稿已保留，請補齊帳戶資訊後重新確認。",
        "en": "Booking was not submitted: payment details are incomplete. Your draft is saved. Complete the account details and confirm again.",
        "th": "ยังไม่ได้ส่งใบจอง: ข้อมูลรับเงินไม่ครบ เก็บร่างไว้แล้ว กรุณากรอกข้อมูลบัญชีให้ครบและยืนยันอีกครั้ง",
        "ja": "予約は未送信です。入金情報が不足しています。下書きは保存されています。口座情報を補完して再度確認してください。",
    },
}
