/* 后台卡点原因码词条(blocked_<code>)· 四份词典已由前置分片初始化,同 ai-i18n-fail.js 先例。
 *
 * 码由 services/workorder/steps/classify.py 的 StepResult.stuck 落进 order_detail.blocked_reasons,
 * 前端此前把它原样 join 上屏,泰国会计看到的是 "insufficient_balance" 这种生标识符。这里是
 * 「码 → 人话 + 现在做什么」的唯一映射表:加新原因码必须同时加这四语,否则 at() 回落原码上屏。
 * 四语齐全(不走 adm-*「只写 zh+th」的内部页先例):卡点卡在真实客户的月度申报上,不是内部规范页。
 * blocked_* = 原因码本身的短标签(列举时用);wo_blocked_* = 工单卡那一屏的三问句(跑了几件 /
 * 为什么停差多少 / 现在点哪),一句一件事,由 ai-blocked-notice.js 按拿没拿到数逐句取舍。
 *
 * 守门测试 tests/unit/test_ai_blocked_reasons.py 锁四语 key 集合一致 + 每个后端真会产出的
 * 原因码都有词条(防「加了码没加词条」的老坑)。 */
Object.assign(window.__AI_I18N_ZH__, {
    blocked_insufficient_balance: 'OCR 余额不足',
    blocked_ocr_cost_cap_exceeded: '这一单的识别成本到了我们这边的预算上限（不是你的余额）',
    blocked_ocr_quota_deferred: '有 {n} 张票撞上识别配额上限',
    // 与 blocked_insufficient_balance 说的必须是两件事:那句是「你没钱」,这句是「我们没查着」。
    // 后端 ocr_balance.LOOKUP_FAILED_REASON 产出,余额未知时绝不推用户去充值。
    blocked_lookup_error: '我们这边查不到你的余额，剩下的票先停住了（不是余额不足）',
    wo_blocked_ran: '这一单已经识别完 {done} 件，共 {total} 件。',
    wo_blocked_credit_why: '余额不够了，剩下 {left} 件停在这里没跑。',
    wo_blocked_credit_rest: '余额不够了，剩下的票停在这里没跑。',
    wo_blocked_credit_need: '把剩下的跑完大约还需 {amount}。',
    wo_blocked_credit_how:
        '去充值，回来点下面的「重试」，就从停住的地方接着跑；已经识别过的不再收第二次钱。',
    wo_blocked_cap_why:
        '这一单的识别成本到了我们这边的预算上限，不是你的余额问题，剩下的先停住了。',
    wo_blocked_cap_how: '点下面的「重试」再跑一次；还停在这里就找我们放预算，你不用充值。',
    wo_blocked_also: '另外还有：{list}。',
    // 指到侧栏真有的那一项:充值在「设置」页里,「计费」不是一个能点开的地方。
    err_insufficient_balance: 'OCR 余额不足 · 到「设置」充值后再传',
});

Object.assign(window.__AI_I18N_TH__, {
    blocked_insufficient_balance: 'เครดิต OCR ไม่พอ',
    blocked_ocr_cost_cap_exceeded: 'ต้นทุนการอ่านของใบงานนี้ชนเพดานงบฝั่งเรา (ไม่ใช่เครดิตของคุณ)',
    blocked_ocr_quota_deferred: 'มีบิล {n} ใบชนโควตาการอ่าน',
    blocked_lookup_error: 'ฝั่งเราตรวจสอบยอดคงเหลือของคุณไม่ได้ บิลที่เหลือจึงหยุดไว้ก่อน (ไม่ใช่เครดิตไม่พอ)',
    wo_blocked_ran: 'ใบงานนี้อ่านไปแล้ว {done} ใบ จากทั้งหมด {total} ใบ',
    wo_blocked_credit_why: 'เครดิตไม่พอ อีก {left} ใบจึงหยุดค้างอยู่',
    wo_blocked_credit_rest: 'เครดิตไม่พอ บิลที่เหลือจึงหยุดค้างอยู่',
    wo_blocked_credit_need: 'ถ้าจะอ่านส่วนที่เหลือให้จบ ต้องเติมอีกประมาณ {amount}',
    wo_blocked_credit_how:
        'ไปเติมเงิน แล้วกลับมากด「ลองใหม่」ด้านล่าง ระบบจะทำต่อจากจุดที่หยุด ใบที่อ่านไปแล้วไม่คิดเงินซ้ำ',
    wo_blocked_cap_why:
        'ต้นทุนการอ่านของใบงานนี้ชนเพดานงบฝั่งเรา ไม่ใช่เครดิตของคุณ ส่วนที่เหลือจึงหยุดไว้ก่อน',
    wo_blocked_cap_how:
        'กด「ลองใหม่」ด้านล่างอีกครั้ง ถ้ายังหยุดอยู่ให้ติดต่อเรา เราจะเพิ่มงบให้ คุณไม่ต้องเติมเงิน',
    wo_blocked_also: 'นอกจากนี้ยังมี: {list}',
    err_insufficient_balance: 'เครดิต OCR ไม่พอ · ไปเติมเงินที่「ตั้งค่า」ก่อนแล้วค่อยอัปโหลด',
});

Object.assign(window.__AI_I18N_EN__, {
    blocked_insufficient_balance: 'OCR credits ran out',
    blocked_ocr_cost_cap_exceeded:
        'this order hit our own recognition budget cap (not your balance)',
    blocked_ocr_quota_deferred: '{n} document(s) hit the recognition quota',
    blocked_lookup_error:
        'we could not read your balance on our side, so the rest is paused (not a credit shortage)',
    wo_blocked_ran: 'This order finished reading {done} of {total} documents.',
    wo_blocked_credit_why: 'Credits ran out — the remaining {left} document(s) stopped here.',
    wo_blocked_credit_rest: 'Credits ran out — the remaining documents stopped here.',
    wo_blocked_credit_need: 'Finishing the rest costs about {amount}.',
    wo_blocked_credit_how:
        'Top up, then come back and hit Retry below — it resumes from where it stopped, and what was already read is not charged twice.',
    wo_blocked_cap_why:
        'This order hit our own recognition budget cap, not your balance, so the rest is paused.',
    wo_blocked_cap_how:
        'Hit Retry below to run it again; if it still stops, contact us to raise the budget — no top-up needed on your side.',
    wo_blocked_also: 'Also: {list}.',
    err_insufficient_balance:
        'OCR credits ran out · top up under Settings · Billing, then upload again',
});

Object.assign(window.__AI_I18N_JA__, {
    blocked_insufficient_balance: 'OCR残高が不足しています',
    blocked_ocr_cost_cap_exceeded:
        'この案件の読取コストが当社側の予算上限に達しました（残高の問題ではありません）',
    blocked_ocr_quota_deferred: '{n} 件が読取クォータに達しました',
    blocked_lookup_error: '当社側で残高を確認できず、残りは一時停止しています（残高不足ではありません）',
    wo_blocked_ran: 'この案件は {total} 件中 {done} 件の読取が完了しています。',
    wo_blocked_credit_why: '残高が不足し、残り {left} 件がここで止まっています。',
    wo_blocked_credit_rest: '残高が不足し、残りの書類がここで止まっています。',
    wo_blocked_credit_need: '残りを読み切るには約 {amount} が必要です。',
    wo_blocked_credit_how:
        'チャージ後、下の「再試行」を押すと中断地点から再開します。読取済みの分が二重に課金されることはありません。',
    wo_blocked_cap_why:
        'この案件の読取コストが当社側の予算上限に達しました。残高の問題ではないため、残りは一時停止しています。',
    wo_blocked_cap_how:
        '下の「再試行」をもう一度押してください。それでも止まる場合はご連絡ください。当社側で予算を上げます（チャージは不要です）。',
    wo_blocked_also: 'このほか：{list}。',
    err_insufficient_balance:
        'OCR残高が不足しています · 「設定 · 請求」でチャージしてから再度アップロードしてください',
});
