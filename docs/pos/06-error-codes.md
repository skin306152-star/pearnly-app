# POS 项目 · 06 错误码字典(4 语)

> 后端所有 POS/库存错误返 `error.code`(见 04 信封);前端**只映射此表文案,绝不裸露 code**(销项踩过裸码坑)。
> 4 语:th(首发)/ en / zh / ja。施工时这些 key 进 i18n 数据(`check_i18n --strict` 闸)。文案=通知体、用户能懂、无技术词。

## 业务错误(用户操作可触发 · 必须友好)

| code | HTTP | th | en | zh | ja |
|---|---|---|---|---|---|
| pos.pin_invalid | 401 | PIN ไม่ถูกต้อง | Incorrect PIN | PIN 不正确 | PINが正しくありません |
| pos.cashier_inactive | 403 | บัญชีแคชเชียร์ถูกปิดใช้งาน | This cashier account is disabled | 该收银员账号已停用 | このレジ係アカウントは無効です |
| pos.product_not_found | 404 | ไม่พบสินค้านี้ | Product not found | 找不到该商品 | 商品が見つかりません |
| pos.out_of_stock | 409 | สินค้าคงเหลือไม่พอ | Not enough stock | 库存不足 | 在庫が不足しています |
| pos.shift_already_open | 409 | มีกะที่เปิดอยู่แล้ว | A shift is already open | 已有未结束的班次 | 開始済みのシフトがあります |
| pos.shift_closed | 409 | กะนี้ปิดแล้ว | This shift is closed | 班次已交班 | このシフトは締め済みです |
| pos.line_invalid | 422 | รายการสินค้าไม่ถูกต้อง | Invalid item in the order | 商品行有误 | 明細に誤りがあります |
| pos.void_not_allowed | 409 | ไม่สามารถยกเลิกบิลนี้ได้ | This receipt cannot be voided | 该小票不可作废 | このレシートは取消できません |
| pos.tax_id_invalid | 422 | เลขประจำตัวผู้เสียภาษีไม่ถูกต้อง | Invalid tax ID | 税号无效 | 税番号が無効です |
| pos.already_upgraded | 409 | บิลนี้ออกใบกำกับเต็มรูปแล้ว | A full tax invoice was already issued | 该单已开过正式税票 | 既に正式税額票を発行済みです |
| pos.over_refund | 409 | จำนวนคืนเกินที่ซื้อ | Refund exceeds purchased quantity | 退货量超过购买量 | 返品数が購入数を超えています |
| pos.module_disabled | 403 | ยังไม่ได้เปิดใช้งานระบบขายหน้าร้าน | The POS module is not enabled | 尚未开通收银模块 | POS機能が有効化されていません |
| pos.forbidden | 403 | คุณไม่มีสิทธิ์ทำรายการนี้ | You don't have permission for this | 你没有此操作权限 | この操作の権限がありません |

## 系统/网络错误(兜底 · 不暴露内部)

| code | HTTP | th | en | zh | ja |
|---|---|---|---|---|---|
| pos.offline_saved | — | บันทึกออฟไลน์แล้ว จะซิงค์อัตโนมัติ | Saved offline, will sync automatically | 已离线保存,联网自动同步 | オフライン保存しました。自動同期します |
| pos.sync_partial | 207 | ซิงค์บางรายการไม่สำเร็จ จะลองใหม่ | Some items failed to sync, will retry | 部分单据同步失败,将重试 | 一部の同期に失敗、再試行します |
| pos.server_busy | 503 | ระบบไม่ว่างชั่วคราว ลองใหม่อีกครั้ง | Server busy, please try again | 系统繁忙,请重试 | サーバー混雑中、再試行してください |
| pos.unexpected | 500 | เกิดข้อผิดพลาด ลองใหม่อีกครั้ง | Something went wrong, please try again | 出错了,请重试 | エラーが発生しました。再試行してください |

## 规则
- 后端只返 `code`;前端按当前语言查此表。缺翻译=`check_i18n` 红,不许上。
- `out_of_stock` 等可带 `error.detail`(哪个品/缺多少)给前端拼进文案,但**基础文案来自此表**。
- 离线类(offline_saved/sync_partial)是前端本地态提示,不是后端返回,但文案同此表统一管理。
