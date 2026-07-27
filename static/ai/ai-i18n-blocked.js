/* 后台卡点原因码词条(blocked_<code>)· 四份词典已由前置分片初始化,同 ai-i18n-fail.js 先例。
 *
 * 码由 services/workorder/steps/classify.py 的 StepResult.stuck 落进 order_detail.blocked_reasons,
 * 前端此前把它原样 join 上屏,泰国会计看到的是 "insufficient_balance" 这种生标识符。这里是
 * 「码 → 人话 + 现在做什么」的唯一映射表:加新原因码必须同时加这四语,否则 at() 回落原码上屏。
 * 四语齐全(不走 adm-*「只写 zh+th」的内部页先例):卡点卡在真实客户的月度申报上,不是内部规范页。
 *
 * 守门测试 tests/unit/test_ai_blocked_reasons.py 锁四语 key 集合一致 + 每个后端真会产出的
 * 原因码都有词条(防「加了码没加词条」的老坑)。 */
Object.assign(window.__AI_I18N_ZH__, {
    blocked_insufficient_balance: 'OCR 余额不足',
    blocked_ocr_cost_cap_exceeded: '这一单的识别成本到了我们这边的预算上限（不是你的余额）',
    blocked_ocr_quota_deferred: '有 {n} 张票撞上识别配额上限',
    system_blocked_topup:
        '后台在这里停住：{list}。已完成的数据已保留，充值后点「重试」就从断点接着跑。',
    err_insufficient_balance: 'OCR 余额不足 · 到「设置 · 计费」充值后再传',
});

Object.assign(window.__AI_I18N_TH__, {
    blocked_insufficient_balance: 'เครดิต OCR ไม่พอ',
    blocked_ocr_cost_cap_exceeded: 'ต้นทุนการอ่านของใบงานนี้ชนเพดานงบฝั่งเรา (ไม่ใช่เครดิตของคุณ)',
    blocked_ocr_quota_deferred: 'มีบิล {n} ใบชนโควตาการอ่าน',
    system_blocked_topup:
        'ระบบหยุดที่นี่: {list} ข้อมูลที่ทำเสร็จแล้วยังอยู่ครบ เติมเงินแล้วกด「ลองใหม่」จะทำต่อจากจุดที่หยุด',
    err_insufficient_balance:
        'เครดิต OCR ไม่พอ · ไปเติมเงินที่「ตั้งค่า · การเรียกเก็บเงิน」ก่อนแล้วค่อยอัปโหลด',
});

Object.assign(window.__AI_I18N_EN__, {
    blocked_insufficient_balance: 'OCR credits ran out',
    blocked_ocr_cost_cap_exceeded:
        'this order hit our own recognition budget cap (not your balance)',
    blocked_ocr_quota_deferred: '{n} document(s) hit the recognition quota',
    system_blocked_topup:
        'The backend stopped here: {list}. Everything already done is kept — top up, then hit Retry to resume from where it stopped.',
    err_insufficient_balance:
        'OCR credits ran out · top up under Settings · Billing, then upload again',
});

Object.assign(window.__AI_I18N_JA__, {
    blocked_insufficient_balance: 'OCR残高が不足しています',
    blocked_ocr_cost_cap_exceeded:
        'この案件の読取コストが当社側の予算上限に達しました（残高の問題ではありません）',
    blocked_ocr_quota_deferred: '{n} 件が読取クォータに達しました',
    system_blocked_topup:
        'バックエンドはここで停止しました：{list}。完了済みのデータは保持されています。チャージ後に「再試行」を押すと中断地点から再開します。',
    err_insufficient_balance:
        'OCR残高が不足しています · 「設定 · 請求」でチャージしてから再度アップロードしてください',
});
