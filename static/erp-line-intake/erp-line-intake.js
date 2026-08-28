(function () {
    'use strict';
    var L = {
        th: {
            title: 'ตรวจสอบเอกสาร ERP',
            loading: 'กำลังโหลดร่างเอกสาร…',
            failed: 'โหลดเอกสารไม่สำเร็จ',
            expired: 'รายการหมดอายุ',
            preview: 'เอกสารต้นฉบับ',
            header: 'ข้อมูลหัวเอกสาร',
            items: 'รายการสินค้า/บริการ',
            kind: 'ประเภทการลงสต๊อก',
            pick: 'เลือกประเภท',
            stock: 'สินค้าในสต๊อก',
            service: 'บริการ (ไม่กระทบสต๊อก)',
            save: 'บันทึก',
            confirm: 'ยืนยันและลงบัญชี',
            discard: 'ทิ้งฉบับร่าง',
            saved: 'บันทึกแล้ว',
            confirmed: 'ยืนยันแล้ว',
            discarded: 'ทิ้งแล้ว',
            required: 'กรุณากรอกข้อมูลที่จำเป็นและเลือกประเภทให้ครบทุกรายการ',
            confirmDiscard: 'ทิ้งฉบับร่างนี้หรือไม่',
            purchase: 'ซื้อ',
            sales: 'ขาย',
        },
        en: {
            title: 'Review ERP document',
            loading: 'Loading draft…',
            failed: 'Could not load document',
            expired: 'Draft expired',
            preview: 'Original document',
            header: 'Document fields',
            items: 'Items',
            kind: 'Posting kind',
            pick: 'Choose type',
            stock: 'Inventory',
            service: 'Service (non-stock)',
            save: 'Save',
            confirm: 'Confirm and post',
            discard: 'Discard draft',
            saved: 'Saved',
            confirmed: 'Confirmed',
            discarded: 'Discarded',
            required: 'Complete required fields and choose a type for every item',
            confirmDiscard: 'Discard this draft?',
            purchase: 'Purchase',
            sales: 'Sales',
        },
        zh: {
            title: '复核 ERP 单据',
            loading: '正在加载草稿…',
            failed: '无法加载单据',
            expired: '草稿已过期',
            preview: '原始票据',
            header: '票头字段',
            items: '明细',
            kind: '过账类型',
            pick: '选择类型',
            stock: '库存',
            service: '服务（不动库存）',
            save: '保存',
            confirm: '确认并过账',
            discard: '丢弃草稿',
            saved: '已保存',
            confirmed: '已确认',
            discarded: '已丢弃',
            required: '请补齐必填字段并为每条明细选择类型',
            confirmDiscard: '丢弃这份草稿？',
            purchase: '采购',
            sales: '销售',
        },
        ja: {
            title: 'ERP 書類を確認',
            loading: '下書きを読み込み中…',
            failed: '書類を読み込めません',
            expired: '下書きの期限切れ',
            preview: '原本',
            header: 'ヘッダー項目',
            items: '明細',
            kind: '計上種別',
            pick: '種別を選択',
            stock: '在庫',
            service: 'サービス（在庫なし）',
            save: '保存',
            confirm: '確認して計上',
            discard: '下書きを破棄',
            saved: '保存しました',
            confirmed: '確認しました',
            discarded: '破棄しました',
            required: '必須項目と全明細の種別を入力してください',
            confirmDiscard: 'この下書きを破棄しますか？',
            purchase: '仕入',
            sales: '売上',
        },
    };
    var M = {
        invoice_number: {
            th: 'เลขที่ใบแจ้งหนี้',
            en: 'Invoice no.',
            zh: '发票号',
            ja: '請求書番号',
        },
        date: { th: 'วันที่', en: 'Date', zh: '日期', ja: '日付' },
        seller_name: { th: 'ผู้ขาย', en: 'Seller', zh: '卖方', ja: '売り手' },
        seller_tax: {
            th: 'เลขประจำตัวผู้เสียภาษีผู้ขาย',
            en: 'Seller tax ID',
            zh: '卖方税号',
            ja: '売り手税番号',
        },
        buyer_name: { th: 'ผู้ซื้อ', en: 'Buyer', zh: '买方', ja: '買い手' },
        buyer_tax: {
            th: 'เลขประจำตัวผู้เสียภาษีผู้ซื้อ',
            en: 'Buyer tax ID',
            zh: '买方税号',
            ja: '買い手税番号',
        },
        seller_address: {
            th: 'ที่อยู่ผู้ขาย',
            en: 'Seller address',
            zh: '卖方地址',
            ja: '売り手住所',
        },
        buyer_address: {
            th: 'ที่อยู่ผู้ซื้อ',
            en: 'Buyer address',
            zh: '买方地址',
            ja: '買い手住所',
        },
        subtotal: { th: 'ยอดก่อนภาษี', en: 'Subtotal', zh: '小计', ja: '小計' },
        vat: { th: 'ภาษีมูลค่าเพิ่ม', en: 'VAT', zh: 'VAT', ja: 'VAT' },
        total_amount: { th: 'ยอดรวม', en: 'Total', zh: '总额', ja: '合計' },
        name: { th: 'ชื่อสินค้า', en: 'Item name', zh: '商品名', ja: '商品名' },
        qty: { th: 'จำนวน', en: 'Quantity', zh: '数量', ja: '数量' },
        unit: { th: 'หน่วย', en: 'Unit', zh: '单位', ja: '単位' },
        price: { th: 'ราคาต่อหน่วย', en: 'Unit price', zh: '单价', ja: '単価' },
        amount: { th: 'จำนวนเงิน', en: 'Amount', zh: '金额', ja: '金額' },
        description: { th: 'รายละเอียด', en: 'Description', zh: '说明', ja: '摘要' },
    };
    var CANCEL = { th: 'ยกเลิก', en: 'Cancel', zh: '取消', ja: 'キャンセル' };
    function draftFromLocation() {
        var match = location.pathname.match(/\/liff\/erp\/([^/?#]+)/);
        if (match && match[1]) return match[1];
        var query = new URLSearchParams(location.search);
        var direct = query.get('draft');
        if (direct) return direct;
        var state = query.get('liff.state');
        if (state) {
            state = state.charAt(0) === '?' ? state.slice(1) : state;
            return new URLSearchParams(state).get('draft') || '';
        }
        return '';
    }
    var lang = (localStorage.getItem('pearnly_lang') || 'th').slice(0, 2),
        state = document.getElementById('state'),
        form = document.getElementById('editor'),
        model,
        busy = false,
        draft = draftFromLocation();
    function t(k) {
        return (L[lang] || L.th)[k] || L.en[k] || k;
    }
    function label(k) {
        return (M[k] && M[k][lang]) || k;
    }
    function esc(v) {
        var d = document.createElement('div');
        d.textContent = v == null ? '' : String(v);
        return d.innerHTML;
    }
    function dat(x) {
        return x && x.data !== undefined ? x.data : x;
    }
    function rows() {
        var x = dat(model);
        return Array.isArray(x.records) ? x.records : Array.isArray(x.invoices) ? x.invoices : [x];
    }
    function moveAlias(target, canonical, alias) {
        if (!target[canonical] && target[alias]) target[canonical] = target[alias];
        if (alias !== canonical) delete target[alias];
    }
    function fieldsOf(record) {
        var f = record.fields || (record.pages && record.pages[0] && record.pages[0].fields) || {};
        moveAlias(f, 'invoice_number', 'invoice_no');
        moveAlias(f, 'date', 'invoice_date');
        if (!Array.isArray(f.items) || !f.items.length) {
            // 空白编辑行只提供人工补录入口，不从票头金额猜数量、单价或行金额。
            f.items = [{ name: '', qty: '', price: '', subtotal: '', posting_kind: '' }];
        }
        if (Array.isArray(f.items)) {
            f.items.forEach(function (item) {
                moveAlias(item, 'name', 'description');
                moveAlias(item, 'qty', 'quantity');
                moveAlias(item, 'price', 'unit_price');
                moveAlias(item, 'subtotal', 'amount');
            });
        }
        return f;
    }
    function api(p, o) {
        o = o || {};
        var tok = sessionStorage.getItem('erp_line_token');
        o.headers = Object.assign(
            { 'Content-Type': 'application/json' },
            tok ? { Authorization: 'Bearer ' + tok } : {},
            o.headers || {}
        );
        return fetch(p, o).then(function (r) {
            if (!r.ok) {
                var e = new Error(String(r.status));
                e.status = r.status;
                throw e;
            }
            return r.json();
        });
    }
    function boot() {
        return api('/api/line/erp/liff/config').then(function (x) {
            var id = dat(x).liff_id;
            if (!id || !window.liff) throw Error('liff_config_missing');
            return liff.init({ liffId: id }).then(function () {
                if (!liff.isLoggedIn()) {
                    liff.login();
                    throw Error('liff_login_required');
                }
                var it = liff.getIDToken && liff.getIDToken();
                if (!it) throw Error('liff_token_missing');
                return api('/api/line/erp/liff/auth', {
                    method: 'POST',
                    body: JSON.stringify({ id_token: it, draft_id: draft }),
                }).then(function (x) {
                    var tok = dat(x).token;
                    if (!tok) throw Error('erp_token_missing');
                    sessionStorage.setItem('erp_line_token', tok);
                });
            });
        });
    }
    function sec(h, b) {
        return '<section class="section"><h2>' + esc(h) + '</h2>' + b + '</section>';
    }
    function fld(k, v, req, ri) {
        return window.erpLineFieldRenderer.render(k, v, req, ri, label, esc);
    }
    function prev(r) {
        var fallback = r.preview_url || r.original_url || r.source_url || r.pdf_url || '',
            urls =
                Array.isArray(r.preview_urls) && r.preview_urls.length
                    ? r.preview_urls
                    : fallback
                      ? [fallback]
                      : [];
        return urls.length
            ? urls
                  .map(function (u) {
                      return (
                          '<div class="preview-holder" data-preview="' +
                          esc(u) +
                          '">' +
                          esc(t('loading')) +
                          '</div>'
                      );
                  })
                  .join('')
            : '<p class="hint">—</p>';
    }
    function render() {
        var all = rows(),
            dir = dat(model).direction || '';
        form.innerHTML =
            '<h1>' +
            t('title') +
            '</h1><p class="hint">' +
            esc(t(dir)) +
            '</p>' +
            all
                .map(function (r, ri) {
                    var f = fieldsOf(r),
                        it = Array.isArray(f.items) ? f.items : [],
                        keys = Object.keys(f).filter(function (k) {
                            return k !== 'items';
                        });
                    return (
                        '<article data-record="' +
                        ri +
                        '">' +
                        sec(t('preview'), prev(r)) +
                        sec(
                            t('header'),
                            '<div class="grid">' +
                                keys
                                    .map(function (k) {
                                        return fld(
                                            k,
                                            f[k],
                                            dir === 'sales'
                                                ? ['invoice_number', 'date'].indexOf(k) >= 0
                                                : ['seller_name', 'date', 'total_amount'].indexOf(
                                                      k
                                                  ) >= 0,
                                            ri
                                        );
                                    })
                                    .join('') +
                                '</div>'
                        ) +
                        sec(
                            t('items'),
                            it.length
                                ? it
                                      .map(function (x, ii) {
                                          return (
                                              '<div class="item"><div class="grid">' +
                                              Object.keys(x)
                                                  .filter(function (k) {
                                                      return k !== 'posting_kind';
                                                  })
                                                  .map(function (k) {
                                                      return fld(
                                                          'item.' + ii + '.' + k,
                                                          x[k],
                                                          k === 'name' || k === 'qty',
                                                          ri
                                                      );
                                                  })
                                                  .join('') +
                                              '<div class="field"><label>' +
                                              t('kind') +
                                              ' *</label><select required data-kind="' +
                                              ri +
                                              ':' +
                                              ii +
                                              '"><option value="">' +
                                              t('pick') +
                                              '</option><option value="stock"' +
                                              (x.posting_kind === 'stock' ? ' selected' : '') +
                                              '>' +
                                              t('stock') +
                                              '</option><option value="service"' +
                                              (x.posting_kind === 'service' ? ' selected' : '') +
                                              '>' +
                                              t('service') +
                                              '</option></select></div></div></div>'
                                          );
                                      })
                                      .join('')
                                : '<p class="hint">—</p>'
                        ) +
                        '</article>'
                    );
                })
                .join('') +
            '<div class="actions"><button class="btn" type="button" data-action="save">' +
            t('save') +
            '</button><button class="btn primary" type="button" data-action="confirm">' +
            t('confirm') +
            '</button><button class="btn danger" type="button" data-action="discard">' +
            t('discard') +
            '</button></div>';
        form.hidden = false;
        state.hidden = true;
        form.querySelectorAll('[data-field]').forEach(function (e) {
            e.oninput = sync;
        });
        form.querySelectorAll('[data-kind]').forEach(function (e) {
            e.onchange = kind;
        });
        form.querySelectorAll('[data-action]').forEach(function (e) {
            e.onclick = act;
        });
        window.erpLinePreviews.hydrate(form, t('preview'), t('failed'));
    }
    function sync(e) {
        var p = e.target.dataset.field.split(':'),
            r = rows()[+p[0]],
            f = fieldsOf(r),
            k = p.slice(1).join(':'),
            m = k.match(/^item\.(\d+)\.(.+)$/);
        var value = e.target.value;
        if (e.target.tagName === 'TEXTAREA') {
            try {
                value = JSON.parse(value);
            } catch (_) {
                // Invalid JSON keeps the last valid value until the user completes the object.
                return;
            }
        }
        if (m) (f.items || [])[+m[1]][m[2]] = value;
        else f[k] = value;
    }
    function kind(e) {
        var p = e.target.dataset.kind.split(':'),
            r = rows()[+p[0]],
            f = fieldsOf(r);
        (f.items || [])[+p[1]].posting_kind = e.target.value;
    }
    function valid() {
        var dir = dat(model).direction || 'purchase',
            bad = rows().some(function (r) {
                var f = fieldsOf(r),
                    h =
                        dir === 'sales'
                            ? !f.invoice_number || !f.date
                            : !f.seller_name || !f.date || !f.total_amount;
                return (
                    h ||
                    !Array.isArray(f.items) ||
                    !f.items.length ||
                    f.items.some(function (i) {
                        return !i.name || !i.qty || !['stock', 'service'].includes(i.posting_kind);
                    })
                );
            });
        if (bad) {
            state.className = 'state error';
            state.textContent = t('required');
            state.hidden = false;
            return false;
        }
        return true;
    }
    function act(e) {
        var a = e.currentTarget.dataset.action;
        if (busy) return;
        if (a === 'discard' && !e.confirmed) {
            return window.erpDiscardDialog.open(
                t('confirmDiscard'),
                CANCEL[lang],
                t('discard'),
                e,
                act
            );
        }
        if (!e.confirmed && !valid()) return;
        var base = '/api/line/erp/draft/' + encodeURIComponent(draft),
            save = function () {
                return api(base, {
                    method: 'PUT',
                    body: JSON.stringify({ records: rows() }),
                });
            },
            request =
                a === 'discard'
                    ? api(base + '/discard', { method: 'POST' })
                    : a === 'confirm'
                      ? save().then(function () {
                            return api(base + '/confirm', { method: 'POST' });
                        })
                      : save();
        busy = true;
        form.querySelectorAll('[data-action]').forEach(function (button) {
            button.disabled = true;
        });
        request
            .then(function () {
                state.className = 'state';
                state.textContent = t(
                    a === 'save' ? 'saved' : a === 'confirm' ? 'confirmed' : 'discarded'
                );
                state.hidden = false;
                if (a !== 'save') form.hidden = true;
            })
            .catch(function (e) {
                state.className = 'state error';
                state.textContent =
                    e.status === 401 || e.status === 403 ? t('expired') : t('failed');
                state.hidden = false;
            })
            .finally(function () {
                busy = false;
                form.querySelectorAll('[data-action]').forEach(function (button) {
                    button.disabled = false;
                });
            });
    }
    document.getElementById('lang').value = lang;
    document.getElementById('lang').onchange = function (e) {
        lang = e.target.value;
        localStorage.setItem('pearnly_lang', lang);
        if (model) render();
    };
    state.textContent = t('loading');
    boot()
        .then(function () {
            return api('/api/line/erp/draft/' + encodeURIComponent(draft));
        })
        .then(function (x) {
            model = dat(x);
            render();
        })
        .catch(function (e) {
            state.className = 'state error';
            state.textContent = e.status === 409 ? t('expired') : t('failed');
            state.hidden = false;
        });
})();
