/* ============================================================
 * ADR-006 S8 · PDF/扫描件账单「逐行核对纠错」面板
 * 后端 OCR 低信心/不完整 → job 状态 needs_review + review 载荷 → 弹本面板:
 *   展示 OCR 读出的每一行(可编辑)· 低信心行标黄 · 余额链对不上标红(边改边算)·
 *   完整性问题横幅(漏笔/期末对不上)· 用户改完 → POST confirm-rows → 用修正行重对账。
 * 自包含 IIFE(动态建 DOM + 注入 CSS)· 铁律 #23。
 * 用法:window.ReconReview.show(reviewPayload, { token, lang, jobId, onConfirmed: fn(newJobId) })
 * ============================================================ */
(function () {
    'use strict';

    var L = {
        title: { zh: '请核对识别结果', th: 'กรุณาตรวจสอบผลการอ่าน', en: 'Please review the scan', ja: '読み取り結果の確認' },
        sub: {
            zh: '系统对这份账单的部分内容不确定。请核对下表(可直接修改),确认后再对账。',
            th: 'ระบบไม่แน่ใจกับบางส่วนของรายการเดินบัญชีนี้ กรุณาตรวจสอบ/แก้ไขด้านล่างก่อนกระทบยอด',
            en: 'We are unsure about parts of this statement. Please check/edit the rows below, then reconcile.',
            ja: 'この明細の一部が不確実です。下記を確認・修正してから照合します。',
        },
        colDate: { zh: '日期', th: 'วันที่', en: 'Date', ja: '日付' },
        colDesc: { zh: '摘要', th: 'รายการ', en: 'Description', ja: '摘要' },
        colWd: { zh: '支出', th: 'ถอน', en: 'Withdrawal', ja: '出金' },
        colDep: { zh: '存入', th: 'ฝาก', en: 'Deposit', ja: '入金' },
        colBal: { zh: '余额', th: 'คงเหลือ', en: 'Balance', ja: '残高' },
        colChk: { zh: '余额校验', th: 'ตรวจยอด', en: 'Check', ja: '検算' },
        opening: { zh: '期初余额', th: 'ยอดยกมา', en: 'Opening', ja: '期首残高' },
        confirm: { zh: '确认并对账', th: 'ยืนยันและกระทบยอด', en: 'Confirm & reconcile', ja: '確認して照合' },
        cancel: { zh: '取消', th: 'ยกเลิก', en: 'Cancel', ja: 'キャンセル' },
        chainOk: { zh: '余额链全部对上 ✓', th: 'ยอดคงเหลือถูกต้องทั้งหมด ✓', en: 'Balance chain all OK ✓', ja: '残高チェーン全て一致 ✓' },
        chainBad: {
            zh: '还有 {n} 行余额对不上(红色行)· 仍可提交,但建议先核对',
            th: 'ยังมี {n} แถวที่ยอดไม่ตรง (แถวสีแดง) · ส่งได้ แต่ควรตรวจก่อน',
            en: '{n} row(s) still off (red) · you may submit, but please double-check',
            ja: '{n} 行が不一致(赤)· 送信可能ですが確認推奨',
        },
        lowConf: { zh: '系统读这行时不太确定', th: 'ระบบไม่ค่อยแน่ใจกับแถวนี้', en: 'Low confidence on this row', ja: 'この行は信頼度が低い' },
        submitting: { zh: '提交中…', th: 'กำลังส่ง…', en: 'Submitting…', ja: '送信中…' },
        submitFail: { zh: '提交失败,请重试', th: 'ส่งไม่สำเร็จ ลองใหม่', en: 'Submit failed, retry', ja: '送信に失敗' },
        noRows: { zh: '没有可核对的行', th: 'ไม่มีแถวให้ตรวจ', en: 'No rows to review', ja: '確認する行がありません' },
    };

    // 完整性问题 → 大白话 4 语(后端 _audit_completeness 的 issue type)
    var ISSUE = {
        closing_mismatch: {
            zh: '算出来的期末余额和账单上印的对不上(可能漏读了交易)',
            th: 'ยอดคงเหลือสิ้นงวดที่คำนวณไม่ตรงกับที่พิมพ์ (อาจอ่านตกบางรายการ)',
            en: 'Calculated closing balance ≠ printed (some transactions may be missing)',
            ja: '計算した期末残高が印字と不一致(取引の読み落としの可能性)',
        },
        credit_count_mismatch: {
            zh: '账单页脚写的存款笔数,和读到的对不上(可能漏了一笔存款)',
            th: 'จำนวนรายการฝากตามท้ายสลิปไม่ตรงกับที่อ่านได้ (อาจตกรายการฝาก)',
            en: 'Deposit count on footer ≠ rows read (a deposit may be missing)',
            ja: '入金件数(フッター)が読み取りと不一致(入金の漏れの可能性)',
        },
        debit_count_mismatch: {
            zh: '账单页脚写的取款笔数,和读到的对不上(可能漏了一笔取款)',
            th: 'จำนวนรายการถอนตามท้ายสลิปไม่ตรงกับที่อ่านได้ (อาจตกรายการถอน)',
            en: 'Withdrawal count on footer ≠ rows read (a withdrawal may be missing)',
            ja: '出金件数(フッター)が読み取りと不一致(出金の漏れの可能性)',
        },
        credit_sum_mismatch: {
            zh: '存款合计和账单页脚印的对不上',
            th: 'ยอดรวมฝากไม่ตรงกับที่พิมพ์ท้ายสลิป',
            en: 'Total deposits ≠ printed footer total',
            ja: '入金合計が印字と不一致',
        },
        debit_sum_mismatch: {
            zh: '取款合计和账单页脚印的对不上',
            th: 'ยอดรวมถอนไม่ตรงกับที่พิมพ์ท้ายสลิป',
            en: 'Total withdrawals ≠ printed footer total',
            ja: '出金合計が印字と不一致',
        },
    };

    var lang = 'zh';
    function T(k) { return (L[k] && (L[k][lang] || L[k].zh)) || k; }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function num(x) { var v = parseFloat(x); return isNaN(v) ? 0 : Math.round(v * 100) / 100; }

    function injectCSS() {
        if (document.getElementById('recon-review-css')) return;
        var st = document.createElement('style');
        st.id = 'recon-review-css';
        st.textContent =
            '.rrv-ov{position:fixed;inset:0;background:rgba(17,17,17,.55);z-index:10002;display:flex;align-items:center;justify-content:center;padding:24px}' +
            '.rrv-modal{background:#fff;border-radius:12px;max-width:920px;width:100%;max-height:88vh;display:flex;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.25)}' +
            '.rrv-hd{padding:18px 22px;border-bottom:1px solid #e8e8e3}' +
            '.rrv-hd h3{margin:0 0 4px;font-size:17px;color:#111}' +
            '.rrv-hd p{margin:0;font-size:13px;color:#6b7280}' +
            '.rrv-bd{padding:14px 22px;overflow:auto;flex:1}' +
            '.rrv-banner{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;border-radius:8px;padding:10px 12px;font-size:13px;margin-bottom:12px}' +
            '.rrv-banner ul{margin:6px 0 0;padding-left:18px}' +
            '.rrv-open{font-size:13px;color:#374151;margin-bottom:10px}' +
            '.rrv-open input{width:130px;padding:5px 8px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;text-align:right}' +
            '.rrv-tbl{width:100%;border-collapse:collapse;font-size:13px}' +
            '.rrv-tbl th{background:#f4f4f0;color:#475569;font-weight:600;padding:7px 8px;text-align:left;position:sticky;top:0}' +
            '.rrv-tbl td{border-bottom:1px solid #f1f5f9;padding:4px 6px}' +
            '.rrv-tbl input{width:100%;border:1px solid transparent;background:transparent;padding:5px 6px;font-size:13px;border-radius:5px}' +
            '.rrv-tbl input:focus{border-color:#111;background:#fff;outline:none}' +
            '.rrv-tbl input.amt{text-align:right;font-variant-numeric:tabular-nums}' +
            '.rrv-low{background:#fffbeb}' +
            '.rrv-bad{background:#fef2f2}' +
            '.rrv-bad input{color:#b91c1c}' +
            '.rrv-chk{text-align:center;font-size:14px}' +
            '.rrv-chk.ok{color:#16a34a}.rrv-chk.no{color:#dc2626}' +
            '.rrv-ft{padding:14px 22px;border-top:1px solid #e8e8e3;display:flex;align-items:center;justify-content:space-between;gap:12px}' +
            '.rrv-ft .msg{font-size:13px;color:#6b7280}' +
            '.rrv-ft .msg.ok{color:#16a34a}.rrv-ft .msg.no{color:#b45309}' +
            '.rrv-btns{display:flex;gap:8px}' +
            '.rrv-btn{padding:8px 18px;border-radius:8px;border:1px solid #d1d5db;background:#fff;font-size:14px;cursor:pointer}' +
            '.rrv-btn.primary{background:#111;color:#fff;border-color:#111;font-weight:600}' +
            '.rrv-btn[disabled]{opacity:.5;cursor:not-allowed}';
        document.head.appendChild(st);
    }

    function recompute(rows, opening) {
        // 返回 [{idx, ok}]; prev 用 actual 余额承前 · 单行错不级联
        var prev = num(opening);
        var res = [];
        for (var i = 0; i < rows.length; i++) {
            var r = rows[i];
            var expected = Math.round((prev + num(r.deposit) - num(r.withdrawal)) * 100) / 100;
            var actual = num(r.balance);
            res.push({ idx: i, ok: Math.abs(actual - expected) <= 0.02, expected: expected });
            prev = actual;
        }
        return res;
    }

    function show(payload, opts) {
        opts = opts || {};
        lang = opts.lang || window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        injectCSS();
        var rows = (payload.rows || []).map(function (r) {
            return {
                date: r.date || '', description: r.description || '',
                withdrawal: num(r.withdrawal), deposit: num(r.deposit), balance: num(r.balance),
                confidence: r.confidence || 'high',
            };
        });
        var opening = num(payload.opening);

        var old = document.getElementById('recon-review-ov');
        if (old) old.remove();
        var ov = document.createElement('div');
        ov.className = 'rrv-ov';
        ov.id = 'recon-review-ov';

        var issuesHtml = '';
        var issues = payload.completeness_issues || [];
        if (issues.length) {
            var items = issues.map(function (it) {
                var msg = (ISSUE[it.type] && (ISSUE[it.type][lang] || ISSUE[it.type].zh)) || it.type;
                return '<li>' + esc(msg) + '</li>';
            }).join('');
            issuesHtml = '<div class="rrv-banner"><ul>' + items + '</ul></div>';
        }

        var rowsHtml = rows.map(function (r, i) {
            var lowCls = r.confidence === 'low' ? ' rrv-low' : '';
            var lowTitle = r.confidence === 'low' ? ' title="' + esc(T('lowConf')) + '"' : '';
            return '<tr data-row="' + i + '"' + lowTitle + ' class="' + lowCls.trim() + '">' +
                '<td><input data-i="' + i + '" data-f="date" value="' + esc(r.date) + '" placeholder="YYYY-MM-DD"></td>' +
                '<td><input data-i="' + i + '" data-f="description" value="' + esc(r.description) + '"></td>' +
                '<td><input class="amt" data-i="' + i + '" data-f="withdrawal" type="number" step="0.01" value="' + (r.withdrawal || '') + '"></td>' +
                '<td><input class="amt" data-i="' + i + '" data-f="deposit" type="number" step="0.01" value="' + (r.deposit || '') + '"></td>' +
                '<td><input class="amt" data-i="' + i + '" data-f="balance" type="number" step="0.01" value="' + (r.balance || '') + '"></td>' +
                '<td class="rrv-chk" data-chk="' + i + '">—</td>' +
                '</tr>';
        }).join('');

        ov.innerHTML =
            '<div class="rrv-modal">' +
            '<div class="rrv-hd"><h3>' + esc(T('title')) + '</h3><p>' + esc(T('sub')) + '</p></div>' +
            '<div class="rrv-bd">' +
            issuesHtml +
            '<div class="rrv-open">' + esc(T('opening')) + ': <input id="rrv-open-in" type="number" step="0.01" value="' + opening + '"></div>' +
            (rows.length ?
                '<table class="rrv-tbl"><thead><tr>' +
                '<th>' + esc(T('colDate')) + '</th><th>' + esc(T('colDesc')) + '</th>' +
                '<th>' + esc(T('colWd')) + '</th><th>' + esc(T('colDep')) + '</th>' +
                '<th>' + esc(T('colBal')) + '</th><th>' + esc(T('colChk')) + '</th>' +
                '</tr></thead><tbody>' + rowsHtml + '</tbody></table>'
                : '<div style="color:#6b7280;padding:20px;text-align:center">' + esc(T('noRows')) + '</div>') +
            '</div>' +
            '<div class="rrv-ft"><div class="msg" id="rrv-msg"></div><div class="rrv-btns">' +
            '<button class="rrv-btn" id="rrv-cancel">' + esc(T('cancel')) + '</button>' +
            '<button class="rrv-btn primary" id="rrv-ok">' + esc(T('confirm')) + '</button>' +
            '</div></div></div>';
        document.body.appendChild(ov);

        function readRows() {
            ov.querySelectorAll('.rrv-tbl input').forEach(function (inp) {
                var i = +inp.getAttribute('data-i'), f = inp.getAttribute('data-f');
                if (f === 'date' || f === 'description') rows[i][f] = inp.value;
                else rows[i][f] = num(inp.value);
            });
        }
        function refresh() {
            readRows();
            var op = num(ov.querySelector('#rrv-open-in').value);
            var chk = recompute(rows, op);
            var bad = 0;
            chk.forEach(function (c) {
                var cell = ov.querySelector('[data-chk="' + c.idx + '"]');
                var tr = ov.querySelector('tr[data-row="' + c.idx + '"]');
                if (cell) { cell.textContent = c.ok ? '✓' : '✗'; cell.className = 'rrv-chk ' + (c.ok ? 'ok' : 'no'); }
                if (tr) tr.classList.toggle('rrv-bad', !c.ok);
                if (!c.ok) bad++;
            });
            var msg = ov.querySelector('#rrv-msg');
            if (bad === 0) { msg.textContent = T('chainOk'); msg.className = 'msg ok'; }
            else { msg.textContent = T('chainBad').replace('{n}', bad); msg.className = 'msg no'; }
        }
        ov.querySelectorAll('.rrv-tbl input, #rrv-open-in').forEach(function (inp) {
            inp.addEventListener('input', refresh);
        });
        refresh();

        function close() { ov.remove(); }
        ov.querySelector('#rrv-cancel').addEventListener('click', close);
        ov.addEventListener('click', function (e) { if (e.target === ov) close(); });

        ov.querySelector('#rrv-ok').addEventListener('click', async function () {
            readRows();
            var btn = this;
            btn.disabled = true;
            var msg = ov.querySelector('#rrv-msg');
            msg.textContent = T('submitting'); msg.className = 'msg';
            var out = rows.map(function (r, i) {
                return {
                    idx: i, date: r.date, description: r.description,
                    withdrawal: num(r.withdrawal), deposit: num(r.deposit), balance: num(r.balance),
                    confidence: r.confidence,
                };
            });
            try {
                var resp = await fetch('/api/recon/bank-v2/confirm-rows/' + encodeURIComponent(opts.jobId), {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + opts.token, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rows: out }),
                });
                var d = null;
                try { d = await resp.json(); } catch (_) { d = null; }
                if (resp.ok && d && d.ok && d.job_id) {
                    close();
                    if (typeof opts.onConfirmed === 'function') opts.onConfirmed(d.job_id);
                } else {
                    btn.disabled = false;
                    msg.textContent = (d && d.detail) || T('submitFail'); msg.className = 'msg no';
                }
            } catch (e) {
                btn.disabled = false;
                msg.textContent = T('submitFail'); msg.className = 'msg no';
            }
        });
    }

    window.ReconReview = { show: show };
})();
