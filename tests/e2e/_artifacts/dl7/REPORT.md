# DL-7 · DMS LINE 聊天逐问订车 · 全链 E2E 报告(2026-08-09)

模拟签名 webhook 事件流驱动完整销售旅程(召唤菜单→选2→OCR 建档→逐问 8 步→预览→确认),
真打 DMS 测试站建单、挂附件、回读断言。六场景全 PASS(测试站当日多次网络抖动,
G-QA1/6 于收官轮通过,其余场景在全量轮通过;抖动轮次只造成重试,无假绿)。

- **G-QA1 PASS** 转账全链:booking=BK000002608000003 · 预览四标签齐 · nonce 在卡 ·
  附件=['สำเนาบัตรประชาชน', 'ใบโอนเงินจอง'] · txtmoneytfmon/txtearnestmoney=1,500.00 ·
  บัญชีต้นทาง/ปลายทาง 原文落 txtaccountnumtffrom/tfmon
- **G-QA2 PASS** ทิ้ง 零写入:丢弃回执到,erp_push_logs 前后不变
- **G-QA3 PASS** 现金路:booking=BK000002608000002 · txtmoneycash=2,000.00 · 附件仅身份证复印件
- **G-QA4 PASS** 补凭证闸:含转账无凭证 → TXT_NEED_SLIP 拦住预览;此时打 เงินสด 仍拦;补图后预览放行
- **G-QA5 PASS** 中途乱图零扣费:car_search 步发图 → 仅提示不进 OCR(ocr_delta=0),会话原步保持
- **G-QA6 PASS** nonce 防重:同 nonce 重放 → TXT_EXPIRED,测试站单数不变

## 本役在测试站新建的订车单(留档不删)
- BK000002608000001(抖动轮 G-QA3)
- BK000002608000002(G-QA3)
- BK000002608000003(G-QA1)

## 证据文件
- dms-booking-attachments.png / dms-booking-payment.png —— 真浏览器登录测试站拍的
  编辑页附件区(两个指定显示名的 JPG)与登记/附件整区
- qa1-dms-readback.json / qa3-dms-readback.json —— 编辑表单全字段回读
- qa-preview-transfer.json / qa-preview-cash.json —— LINE 预览卡原文
- qa1-customer-review.json / qa1-receipt.json / results.json / dms-booking-numbers.json
