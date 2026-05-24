/* ============================================================
 * ADR-006 · 列映射确认面板(通用模板学习层 · S5)
 * 新模板上传后,后端返回 needs_mapping(表头+前20行预览+系统猜测)→ 弹本面板,
 * 让用户把每一列指认为 日期/描述/存入/支出/金额/余额/忽略 → 保存 → 重跑对账。
 * 自包含 IIFE(动态建 DOM + 注入 CSS · 不依赖 home.css/home.html 结构)· 铁律 #23。
 * 用法:window.ReconMapping.show(needsMappingResp, { token, lang, onConfirmed: fn })
 * ============================================================ */
(function () {
    'use strict';

    var L = {
        title: {
            zh: '发现新的文件格式',
            th: 'พบรูปแบบไฟล์ใหม่',
            en: 'New file format detected',
            ja: '新しいファイル形式を検出',
        },
        sub: {
            zh: '请确认每一列的含义。确认一次后,下次同格式会自动读取。',
            th: 'กรุณาระบุความหมายของแต่ละคอลัมน์ ยืนยันครั้งเดียว ครั้งต่อไปรูปแบบเดียวกันจะอ่านอัตโนมัติ',
            en: 'Please confirm what each column means. Confirm once — next time the same format is read automatically.',
            ja: '各列の意味をご確認ください。一度確認すれば、次回同じ形式は自動で読み取ります。',
        },
        file: { zh: '文件', th: 'ไฟล์', en: 'File', ja: 'ファイル' },
        save: {
            zh: '保存并继续',
            th: 'บันทึกและดำเนินการต่อ',
            en: 'Save & continue',
            ja: '保存して続行',
        },
        cancel: { zh: '取消', th: 'ยกเลิก', en: 'Cancel', ja: 'キャンセル' },
        needDate: {
            zh: '请至少指定『日期』列',
            th: 'กรุณาระบุคอลัมน์ « วันที่ »',
            en: 'Please set the Date column',
            ja: '「日付」列を指定してください',
        },
        needAmt: {
            zh: '请至少指定『存入』『支出』或『金额』中的一列',
            th: 'กรุณาระบุอย่างน้อยหนึ่งคอลัมน์: ฝาก / ถอน / จำนวนเงิน',
            en: 'Set at least one of Deposit / Withdrawal / Amount',
            ja: '入金 / 出金 / 金額 のいずれかを指定してください',
        },
        needDrCr: {
            zh: '请至少指定『借方』或『贷方』中的一列',
            th: 'กรุณาระบุอย่างน้อยหนึ่งคอลัมน์: เดบิต / เครดิต',
            en: 'Set at least one of Debit / Credit',
            ja: '借方 / 貸方 のいずれかを指定してください',
        },
        saving: { zh: '保存中…', th: 'กำลังบันทึก…', en: 'Saving…', ja: '保存中…' },
        saveFail: {
            zh: '保存失败,请重试',
            th: 'บันทึกไม่สำเร็จ ลองใหม่',
            en: 'Save failed, please retry',
            ja: '保存に失敗しました',
        },
    };
    var F = {
        ignore: { v: 'ignore', zh: '忽略(不用)', th: 'ไม่ใช้', en: 'Ignore', ja: '使わない' },
        date: { v: 'date', zh: '日期', th: 'วันที่', en: 'Date', ja: '日付' },
        description: {
            v: 'description',
            zh: '描述/摘要',
            th: 'รายละเอียด',
            en: 'Description',
            ja: '摘要',
        },
        deposit: { v: 'deposit', zh: '存入/收入', th: 'ฝาก/รับ', en: 'Deposit', ja: '入金' },
        withdrawal: {
            v: 'withdrawal',
            zh: '支出/取款',
            th: 'ถอน/จ่าย',
            en: 'Withdrawal',
            ja: '出金',
        },
        amount: {
            v: 'amount',
            zh: '金额(含正负)',
            th: 'จำนวนเงิน(±)',
            en: 'Amount (signed)',
            ja: '金額(±)',
        },
        balance: { v: 'balance', zh: '余额', th: 'คงเหลือ', en: 'Balance', ja: '残高' },
        // GL 总账专用
        doc_no: {
            v: 'doc_no',
            zh: '凭证/单据号',
            th: 'เลขที่เอกสาร',
            en: 'Voucher/Doc No',
            ja: '伝票番号',
        },
        account: { v: 'account', zh: '科目/账号', th: 'รหัสบัญชี', en: 'Account', ja: '科目' },
        debit: { v: 'debit', zh: '借方', th: 'เดบิต', en: 'Debit', ja: '借方' },
        credit: { v: 'credit', zh: '贷方', th: 'เครดิต', en: 'Credit', ja: '貸方' },
    };
    // 按文档类型给不同字段选项:账单(statement) vs 总账(gl)
    var FIELDS_BY_TYPE = {
        statement: ['ignore', 'date', 'description', 'deposit', 'withdrawal', 'amount', 'balance'],
        gl: [
            'ignore',
            'date',
            'doc_no',
            'account',
            'description',
            'debit',
            'credit',
            'amount',
            'balance',
        ],
    };

    function t(d, lang) {
        return d[lang] || d.en || d.zh;
    }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function injectCss() {
        if (document.getElementById('recon-mapping-css')) return;
        var st = document.createElement('style');
        st.id = 'recon-mapping-css';
        st.textContent = [
            '.rmap-ov{position:fixed;inset:0;background:rgba(17,17,17,.45);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px}',
            '.rmap-box{background:#fff;border-radius:12px;max-width:920px;width:100%;max-height:88vh;display:flex;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.2);font-size:13px}',
            '.rmap-hd{padding:16px 20px;border-bottom:1px solid #e8e8e3}',
            '.rmap-hd h3{margin:0 0 4px;font-size:16px;color:#111}',
            '.rmap-hd p{margin:0;color:#6b7280;font-size:12px}',
            '.rmap-bd{padding:14px 20px;overflow:auto}',
            '.rmap-file{font-size:12px;color:#374151;margin-bottom:10px}',
            '.rmap-tbl{border-collapse:collapse;width:100%;font-size:12px}',
            '.rmap-tbl th,.rmap-tbl td{border:1px solid #e8e8e3;padding:5px 8px;text-align:left;white-space:nowrap;max-width:180px;overflow:hidden;text-overflow:ellipsis}',
            '.rmap-tbl thead th{background:#f4f4f0;position:sticky;top:0}',
            '.rmap-sel{width:100%;font-size:12px;padding:4px;border:1px solid #d1d5db;border-radius:6px;background:#fff}',
            '.rmap-sel.set{border-color:#111;font-weight:600}',
            '.rmap-ft{padding:14px 20px;border-top:1px solid #e8e8e3;display:flex;justify-content:flex-end;gap:10px;align-items:center}',
            '.rmap-err{color:#b91c1c;font-size:12px;margin-right:auto}',
            '.rmap-btn{padding:8px 16px;border-radius:8px;border:1px solid #d1d5db;background:#fff;cursor:pointer;font-size:13px}',
            '.rmap-btn.primary{background:#111;color:#fff;border-color:#111}',
            '.rmap-btn:disabled{opacity:.5;cursor:default}',
        ].join('');
        document.head.appendChild(st);
    }

    function close(ov) {
        if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
    }

    function show(resp, ctx) {
        injectCss();
        ctx = ctx || {};
        var lang = ctx.lang || 'zh';
        var headers = resp.headers || [];
        var preview = resp.preview_rows || [];
        var suggested = resp.suggested_mapping || {};
        var ncols = headers.length || (preview[0] ? preview[0].length : 0);

        // 按文档类型选字段集(账单 vs 总账)
        var docType = resp.document_type === 'gl' ? 'gl' : 'statement';
        var FIELDS = FIELDS_BY_TYPE[docType].map(function (k) {
            return F[k];
        });
        var SINGLE = FIELDS_BY_TYPE[docType].filter(function (k) {
            return k !== 'ignore';
        }); // 每个字段只能选一列

        // 反查:列 -> 建议字段
        var colField = {};
        SINGLE.forEach(function (f) {
            if (typeof suggested[f] === 'number') colField[suggested[f]] = f;
        });

        var ov = document.createElement('div');
        ov.className = 'rmap-ov';

        var selOpts = function (sel) {
            return FIELDS.map(function (f) {
                return (
                    '<option value="' +
                    f.v +
                    '"' +
                    (f.v === sel ? ' selected' : '') +
                    '>' +
                    esc(t(f, lang)) +
                    '</option>'
                );
            }).join('');
        };
        var headRow = '';
        for (var c = 0; c < ncols; c++) {
            var sug = colField[c] || 'ignore';
            headRow +=
                '<th><div>' +
                esc(headers[c] || '#' + (c + 1)) +
                '</div>' +
                '<select class="rmap-sel" data-col="' +
                c +
                '">' +
                selOpts(sug) +
                '</select></th>';
        }
        var bodyRows = preview
            .slice(0, 12)
            .map(function (row) {
                var tds = '';
                for (var c = 0; c < ncols; c++)
                    tds += '<td>' + esc(row[c] != null ? row[c] : '') + '</td>';
                return '<tr>' + tds + '</tr>';
            })
            .join('');

        ov.innerHTML =
            '<div class="rmap-box">' +
            '<div class="rmap-hd"><h3>' +
            esc(t(L.title, lang)) +
            '</h3><p>' +
            esc(t(L.sub, lang)) +
            '</p></div>' +
            '<div class="rmap-bd">' +
            (resp.file
                ? '<div class="rmap-file">' +
                  esc(t(L.file, lang)) +
                  ': ' +
                  esc(resp.file) +
                  '</div>'
                : '') +
            '<table class="rmap-tbl"><thead><tr>' +
            headRow +
            '</tr></thead><tbody>' +
            bodyRows +
            '</tbody></table>' +
            '</div>' +
            '<div class="rmap-ft"><span class="rmap-err"></span>' +
            '<button class="rmap-btn rmap-cancel">' +
            esc(t(L.cancel, lang)) +
            '</button>' +
            '<button class="rmap-btn primary rmap-save">' +
            esc(t(L.save, lang)) +
            '</button>' +
            '</div></div>';
        document.body.appendChild(ov);

        var errEl = ov.querySelector('.rmap-err');
        var saveBtn = ov.querySelector('.rmap-save');
        var selects = Array.prototype.slice.call(ov.querySelectorAll('.rmap-sel'));
        selects.forEach(function (s) {
            var mark = function () {
                s.classList.toggle('set', s.value !== 'ignore');
            };
            mark();
            s.addEventListener('change', mark);
        });

        ov.querySelector('.rmap-cancel').addEventListener('click', function () {
            close(ov);
        });
        ov.addEventListener('click', function (e) {
            if (e.target === ov) close(ov);
        });

        saveBtn.addEventListener('click', function () {
            // 收集 mapping(同字段多列取最后一个)
            var mapping = {};
            selects.forEach(function (s) {
                if (s.value !== 'ignore') mapping[s.value] = parseInt(s.dataset.col, 10);
            });
            if (typeof mapping.date !== 'number') {
                errEl.textContent = t(L.needDate, lang);
                return;
            }
            var hasAmt =
                docType === 'gl'
                    ? typeof mapping.debit === 'number' ||
                      typeof mapping.credit === 'number' ||
                      typeof mapping.amount === 'number'
                    : typeof mapping.deposit === 'number' ||
                      typeof mapping.withdrawal === 'number' ||
                      typeof mapping.amount === 'number';
            if (!hasAmt) {
                errEl.textContent = t(docType === 'gl' ? L.needDrCr : L.needAmt, lang);
                return;
            }
            errEl.textContent = '';
            saveBtn.disabled = true;
            saveBtn.textContent = t(L.saving, lang);
            fetch('/api/recon/import/save-mapping', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + (ctx.token || ''),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_type: resp.document_type || 'statement',
                    template_signature: resp.template_signature,
                    mapping: mapping,
                    sample_headers: headers,
                }),
            })
                .then(function (r) {
                    return r.json().catch(function () {
                        return null;
                    });
                })
                .then(function (j) {
                    if (j && j.ok) {
                        close(ov);
                        if (typeof ctx.onConfirmed === 'function') ctx.onConfirmed();
                    } else {
                        saveBtn.disabled = false;
                        saveBtn.textContent = t(L.save, lang);
                        errEl.textContent = (j && j.detail) || t(L.saveFail, lang);
                    }
                })
                .catch(function () {
                    saveBtn.disabled = false;
                    saveBtn.textContent = t(L.save, lang);
                    errEl.textContent = t(L.saveFail, lang);
                });
        });
    }

    window.ReconMapping = { show: show };
})();
