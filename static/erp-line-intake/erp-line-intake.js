(function () {
    'use strict';

    var R = window.lineIntakeBatchReview;
    var S = window.lineIntakeSourcePage;
    var I = window.erpLineIntakeI18n;
    var F = window.erpLineFieldRenderer;
    var lang = (
        new URLSearchParams(location.search).get('lang') ||
        localStorage.getItem('pearnly_lang') ||
        'th'
    ).slice(0, 2);
    var state = document.getElementById('state');
    var form = document.getElementById('editor');
    var model = null;
    var draftId = '';
    var busy = false;
    var review = null;
    var manual = null;
    var manualAttachments = {};
    var stateKey = 'loading';
    var stateKind = '';

    var COMMON_ORDER = ['invoice_number', 'date', 'document_type'];
    var PURCHASE_ORDER = [
        'seller_name',
        'seller_tax',
        'seller_branch',
        'seller_addr',
        'seller_address',
        'buyer_name',
        'buyer_tax',
        'buyer_branch',
        'buyer_addr',
        'buyer_address',
    ];
    var SALES_ORDER = [
        'buyer_name',
        'buyer_tax',
        'buyer_branch',
        'buyer_addr',
        'buyer_address',
        'seller_name',
        'seller_tax',
        'seller_branch',
        'seller_addr',
        'seller_address',
    ];
    var AMOUNT_ORDER = ['subtotal', 'discount', 'vat', 'total_amount', 'payment_received', 'notes'];
    var HIDDEN_FIELDS = new Set([
        'document_number',
        'bill_number',
        'date_calendar',
        'items',
        'additional_invoices',
        'source_refs',
        'direction',
        'document_type_source',
    ]);

    function t(key, values) {
        var labels = {
            confirmBatch: { th: 'บันทึก', en: 'Save', zh: '保存', ja: '保存' },
            failed: {
                th: 'ดำเนินการไม่สำเร็จ ข้อมูลยังอยู่ กรุณาลองใหม่',
                en: 'Could not complete. Your entries are retained; please retry.',
                zh: '操作失败，内容已保留，请重试。',
                ja: '操作できませんでした。入力内容は保持されています。再試行してください。',
            },
            amountMismatch: {
                th: 'ยอดสินค้า ส่วนลด และภาษีไม่ตรงกับยอดรวม กรุณาตรวจสอบก่อนบันทึก',
                en: 'Items, discount and tax do not match the total. Review the amounts before saving.',
                zh: '商品明细、折扣和税额与总额不一致，请核对后保存。',
                ja: '明細・割引・税額と合計が一致しません。確認してから保存してください。',
            },
            duplicate: {
                th: 'เอกสารนี้บันทึกแล้ว กรุณาทิ้งรายการซ้ำ',
                en: 'This invoice is already recorded. Discard this duplicate.',
                zh: '这张票据已经入账，请丢弃重复单据。',
                ja: 'この伝票は登録済みです。重複分を破棄してください。',
            },
            saved: { th: 'บันทึกแล้ว', en: 'Saved', zh: '已保存', ja: '保存しました' },
            addItem: { th: 'เพิ่มรายการ', en: 'Add a line', zh: '添加一行', ja: '行を追加' },
            removeItem: { th: 'ลบ', en: 'Remove', zh: '移除', ja: '削除' },
        };
        return labels[key] ? labels[key][lang] || labels[key].th : I.text(lang, key, values);
    }

    function label(key) {
        if (key === 'payment_received') {
            return (
                { th: 'ยอดชำระจริง', en: 'Amount paid', zh: '实际收付款金额', ja: '実際の支払額' }[
                    lang
                ] || 'Amount paid'
            );
        }
        if (key === 'date') {
            return (
                { th: 'วันที่ พ.ศ.', en: 'Date (B.E.)', zh: '日期（佛历）', ja: '日付（仏暦）' }[
                    lang
                ] || 'วันที่ พ.ศ.'
            );
        }
        return I.label(lang, key);
    }

    function token() {
        return sessionStorage.getItem('erp_line_token') || '';
    }

    function api(path, options) {
        options = options || {};
        options.headers = Object.assign(
            { 'Content-Type': 'application/json' },
            token() ? { Authorization: 'Bearer ' + token() } : {},
            options.headers || {}
        );
        return fetch(path, options).then(window.lineIntakeLiff.responseJson);
    }

    function rows() {
        return model && Array.isArray(model.records) ? model.records : [];
    }

    function direction() {
        return (model && (model.direction || model.mode)) || 'purchase';
    }

    function expressTarget() {
        return false;
    }

    function moveAlias(target, canonical, alias) {
        if (!target[canonical] && target[alias]) target[canonical] = target[alias];
        if (alias !== canonical) delete target[alias];
    }

    function fieldsOf(record) {
        var fields = R.canonicalFields(record);
        moveAlias(fields, 'invoice_number', 'invoice_no');
        moveAlias(fields, 'date', 'invoice_date');
        if (!Array.isArray(fields.items) || !fields.items.length) {
            fields.items = [{ name: '', qty: '', price: '', subtotal: '', posting_kind: '' }];
        }
        fields.items.forEach(function (item) {
            moveAlias(item, 'name', 'description');
            moveAlias(item, 'qty', 'quantity');
            moveAlias(item, 'price', 'unit_price');
            moveAlias(item, 'subtotal', 'amount');
        });
        return fields;
    }

    function section(title, body) {
        return '<section class="section"><h2>' + R.escape(title) + '</h2>' + body + '</section>';
    }

    function preferredKeys(fields) {
        var preferred = COMMON_ORDER.concat(
            direction() === 'sales' ? SALES_ORDER : PURCHASE_ORDER,
            AMOUNT_ORDER
        );
        return preferred
            .filter(function (key) {
                return Object.prototype.hasOwnProperty.call(fields, key);
            })
            .concat(
                Object.keys(fields).filter(function (key) {
                    return !HIDDEN_FIELDS.has(key) && preferred.indexOf(key) < 0;
                })
            );
    }

    function requiredField(key) {
        return key === 'date';
    }

    function renderOriginals(record) {
        return S.originalsHtml(record, t);
    }

    function renderDetail(record, recordIndex) {
        var fields = fieldsOf(record);
        if (record.filename === 'manual') {
            return (
                '<label class="field"><span>' +
                R.escape(t('workspace')) +
                '</span><select data-manual-workspace>' +
                (model.workspaces || [])
                    .map(function (w) {
                        return (
                            '<option value="' +
                            Number(w.id) +
                            '"' +
                            (Number(w.id) === Number(model.selection.workspace_client_id)
                                ? ' selected'
                                : '') +
                            '>' +
                            R.escape(w.name) +
                            '</option>'
                        );
                    })
                    .join('') +
                '</select></label>' +
                manual.manualHtml(fields, direction(), lang)
            );
        }
        var fieldGrid = preferredKeys(fields)
            .map(function (key) {
                return F.render(
                    key,
                    fields[key],
                    requiredField(key),
                    recordIndex + ':field:' + key,
                    lang,
                    label,
                    R.escape,
                    S.fieldPage(record, key)
                );
            })
            .join('');
        var items = fields.items
            .map(function (item, itemIndex) {
                var keys = ['name', 'qty', 'unit', 'price', 'subtotal'].filter(function (key) {
                    return Object.prototype.hasOwnProperty.call(item, key);
                });
                Object.keys(item).forEach(function (key) {
                    if (key !== 'posting_kind' && keys.indexOf(key) < 0) keys.push(key);
                });
                var posting = expressTarget()
                    ? '<div class="field item-field item-field--posting"><label>' +
                      R.escape(t('kind')) +
                      ' *</label><select data-kind="' +
                      recordIndex +
                      ':' +
                      itemIndex +
                      '" data-source-page="' +
                      S.fieldPage(record, '', itemIndex) +
                      '"><option value="">' +
                      R.escape(t('pick')) +
                      '</option><option value="stock"' +
                      (item.posting_kind === 'stock' ? ' selected' : '') +
                      '>' +
                      R.escape(t('stock')) +
                      '</option><option value="service"' +
                      (item.posting_kind === 'service' ? ' selected' : '') +
                      '>' +
                      R.escape(t('service')) +
                      '</option></select></div>'
                    : '';
                return (
                    '<div class="item"><div class="grid">' +
                    keys
                        .map(function (key) {
                            return F.render(
                                key,
                                item[key],
                                ['name', 'qty'].indexOf(key) >= 0,
                                recordIndex + ':item:' + itemIndex + ':' + key,
                                lang,
                                label,
                                R.escape,
                                S.fieldPage(record, key, itemIndex)
                            );
                        })
                        .join('') +
                    posting +
                    '</div><button type="button" class="pu-btn pu-btn--secondary" data-remove-item="' +
                    itemIndex +
                    '">' +
                    R.escape(t('removeItem')) +
                    '</button></div>'
                );
            })
            .join('');
        return (
            (record.filename === 'manual' ? '' : section(t('original'), renderOriginals(record))) +
            section(t('fields'), '<div class="grid">' + fieldGrid + '</div>') +
            section(
                t('items'),
                items +
                    '<button type="button" class="pu-btn pu-btn--secondary" data-add-item>' +
                    R.escape(t('addItem')) +
                    '</button>'
            )
        );
    }

    function applyField(element) {
        var parts = element.dataset.field.split(':');
        var fields = fieldsOf(rows()[Number(parts[0])]);
        var target = fields;
        var key = parts[2];
        if (parts[1] === 'item') {
            target = fields.items[Number(parts[2])];
            key = parts[3];
        }
        var value = element.value;
        if (typeof target[key] === 'boolean') value = value === 'true';
        if (element.tagName === 'TEXTAREA' && target[key] && typeof target[key] === 'object') {
            try {
                value = JSON.parse(value);
            } catch {
                return;
            }
        }
        target[key] = value;
    }

    function bindDetail(root, _recordIndex, changed) {
        if (rows()[_recordIndex].filename === 'manual') {
            var workspaceSelect = root.querySelector('[data-manual-workspace]');
            workspaceSelect.onchange = function () {
                var previous = model.selection.workspace_client_id;
                var unsavedFields = JSON.parse(JSON.stringify(fieldsOf(rows()[_recordIndex])));
                model.selection.workspace_client_id = Number(workspaceSelect.value);
                busy = true;
                workspaceSelect.disabled = true;
                review.setBusy(true);
                save(true)
                    .then(function () {
                        var savedFields = fieldsOf(rows()[_recordIndex]);
                        var party = direction() === 'purchase' ? 'buyer' : 'seller';
                        unsavedFields[party + '_tax'] = savedFields[party + '_tax'];
                        unsavedFields[party + '_name'] = savedFields[party + '_name'];
                        unsavedFields.items.forEach(function (item) {
                            delete item.product_id;
                            delete item.code;
                        });
                        rows()[_recordIndex].pages[0].fields = unsavedFields;
                        state.hidden = true;
                        review.render();
                    })
                    .catch(function () {
                        model.selection.workspace_client_id = previous;
                        workspaceSelect.value = String(previous);
                        show('failed', 'error');
                    })
                    .finally(function () {
                        busy = false;
                        workspaceSelect.disabled = false;
                        review.setBusy(false);
                    });
            };
            var fieldRoot = root.querySelector('[data-manual-document]');
            manual.bindManual(
                fieldRoot,
                function () {
                    return fieldsOf(rows()[_recordIndex]);
                },
                function (fields) {
                    rows()[_recordIndex].pages[0].fields = fields;
                    review.render();
                }
            );
            var files = fieldRoot.querySelector('[data-md-files]');
            files.innerHTML =
                '<button type="button" class="pu-btn pu-btn--secondary" data-manual-choose>' +
                R.escape(manual.manualLabel('choose', lang)) +
                '</button><span data-manual-filename></span><input type="file" accept="application/pdf,image/*" hidden data-manual-file>';
            files.querySelector('[data-manual-choose]').onclick = function () {
                files.querySelector('[data-manual-file]').click();
            };
            files.querySelector('[data-manual-filename]').textContent =
                (manualAttachments[rows()[_recordIndex].id] || {}).name || '';
            files.querySelector('[data-manual-file]').onchange = function (event) {
                var file = event.target.files[0];
                if (file) {
                    manualAttachments[rows()[_recordIndex].id] = file;
                    files.querySelector('[data-manual-filename]').textContent = file.name;
                }
            };
            fieldRoot.addEventListener('input', function () {
                rows()[_recordIndex].pages[0].fields = manual.readManual(
                    fieldRoot,
                    fieldsOf(rows()[_recordIndex])
                );
                changed();
            });
            return;
        }
        root.querySelectorAll('[data-field]').forEach(function (input) {
            if (!/:item:\d+:name$/.test(input.dataset.field)) return;
            manual.bindProductInput(input, function (product) {
                var index = Number(input.dataset.field.split(':')[2]);
                Object.assign(fieldsOf(rows()[_recordIndex]).items[index], {
                    code: product.code,
                    unit: product.unit || '',
                    product_id: product.product_id,
                });
                input.value = product.name_zh || product.name_th || product.name_en || '';
                input.dispatchEvent(new Event('input', { bubbles: true }));
            });
        });
        root.querySelector('[data-add-item]').onclick = function () {
            fieldsOf(rows()[_recordIndex]).items.push({
                name: '',
                qty: '1',
                price: '',
                subtotal: '',
            });
            review.render();
        };
        root.querySelectorAll('[data-remove-item]').forEach(function (button) {
            button.onclick = function () {
                fieldsOf(rows()[_recordIndex]).items.splice(Number(button.dataset.removeItem), 1);
                review.render();
            };
        });
        root.querySelectorAll('[data-field]').forEach(function (element) {
            element.oninput = function (event) {
                if (event.isTrusted && /:item:\d+:name$/.test(element.dataset.field)) {
                    var item = fieldsOf(rows()[_recordIndex]).items[
                        Number(element.dataset.field.split(':')[2])
                    ];
                    delete item.code;
                    delete item.product_id;
                }
                applyField(element);
                if (/:item:\d+:(qty|price)$/.test(element.dataset.field)) {
                    var fields = fieldsOf(rows()[_recordIndex]);
                    fields.items.forEach(function (item, i) {
                        item.subtotal = (Number(item.qty || 0) * Number(item.price || 0)).toFixed(
                            2
                        );
                        var input = root.querySelector(
                            '[data-field="' + _recordIndex + ':item:' + i + ':subtotal"]'
                        );
                        if (input) input.value = item.subtotal;
                    });
                }
                changed();
            };
        });
        root.querySelectorAll('[data-kind]').forEach(function (element) {
            element.onchange = function () {
                var parts = element.dataset.kind.split(':');
                fieldsOf(rows()[Number(parts[0])]).items[Number(parts[1])].posting_kind =
                    element.value;
                changed();
            };
        });
    }

    function show(key, kind) {
        stateKey = key;
        stateKind = kind || '';
        state.className = 'state ' + (kind || '');
        state.textContent = t(key);
        state.hidden = false;
    }

    function save(workspaceOnly) {
        return api('/api/line/erp/draft/' + encodeURIComponent(draftId), {
            method: 'PUT',
            body: JSON.stringify({
                records: rows(),
                workspace_client_id: model.selection.workspace_client_id,
                direction: direction(),
            }),
        }).then(function (updated) {
            if (updated) model = Object.assign(model, updated);
            if (workspaceOnly) return updated;
            return Promise.all(
                rows().map(function (record) {
                    var file = manualAttachments[record.id];
                    if (!file) return null;
                    var data = new FormData();
                    data.append('file', file);
                    return fetch(
                        '/api/line/erp/draft/' +
                            encodeURIComponent(draftId) +
                            '/attachment/' +
                            encodeURIComponent(record.id),
                        {
                            method: 'POST',
                            headers: { Authorization: 'Bearer ' + token() },
                            body: data,
                        }
                    )
                        .then(window.lineIntakeLiff.responseJson)
                        .then(function () {
                            delete manualAttachments[record.id];
                        });
                })
            ).then(function () {
                return updated;
            });
        });
    }

    function act(action) {
        if (busy || (action === 'confirm' && !review.canConfirm())) return;
        busy = true;
        review.setBusy(true);
        var base = '/api/line/erp/draft/' + encodeURIComponent(draftId);
        var request =
            action === 'discard'
                ? api(base + '/discard', { method: 'POST' })
                : save().then(function () {
                      return action === 'confirm'
                          ? api(base + '/confirm', { method: 'POST' })
                          : null;
                  });
        request
            .then(function (result) {
                if (action === 'save') {
                    show('saved');
                    review.render();
                    return;
                }
                if (action === 'discard') {
                    form.hidden = true;
                    show('discarded');
                    return;
                }
                if (!result || result.ok !== true) {
                    show('failed', 'error');
                    return;
                }
                form.hidden = true;
                show('saved');
            })
            .catch(function (error) {
                var duplicate = JSON.stringify(error.body || {}).indexOf('"duplicate"') >= 0;
                var amountMismatch =
                    JSON.stringify(error.body || {}).indexOf('amount_mismatch') >= 0;
                show(
                    amountMismatch
                        ? 'amountMismatch'
                        : duplicate
                          ? 'duplicate'
                          : error.status === 401 || error.status === 403
                            ? 'expired'
                            : 'failed',
                    'error'
                );
            })
            .finally(function () {
                busy = false;
                if (!form.hidden) review.setBusy(false);
            });
    }

    function buildReview() {
        if (rows().length === 1 && rows()[0].filename === 'manual') {
            window.t = function (key, values) {
                var text = ((window.I18N || {})[lang] || {})[key] || key;
                Object.keys(values || {}).forEach(function (name) {
                    text = text.replace('{' + name + '}', values[name]);
                });
                return text;
            };
            window.escapeHtml = R.escape;
            window.showToast = function (message) {
                state.textContent = message;
                state.hidden = false;
            };
            manual.setPurchaseTransport(function (method, path, body) {
                if (path.indexOf('/api/sales/products') === 0) {
                    return api(
                        '/api/line/erp/draft/' +
                            encodeURIComponent(draftId) +
                            '/products' +
                            (path.split('?')[1] ? '?' + path.split('?')[1] : '')
                    ).then(function (data) {
                        return {
                            products: (data.products || []).map(function (p) {
                                return Object.assign({}, p, { id: p.product_id, sku: p.code });
                            }),
                        };
                    });
                }
                var kind = path.replace('/api/purchase/', '').split('?')[0];
                return api(
                    '/api/line/erp/draft/' +
                        encodeURIComponent(draftId) +
                        '/form-reference/' +
                        encodeURIComponent(kind),
                    {
                        method: method,
                        body: body === undefined ? undefined : JSON.stringify(body),
                    }
                );
            });
            review = {
                render: function () {
                    form.innerHTML = renderDetail(rows()[0], 0);
                    manual.bindManual(
                        form,
                        function () {
                            return fieldsOf(rows()[0]);
                        },
                        function () {},
                        {
                            cancel: function () {
                                act('discard');
                            },
                            save: async function (fields, status) {
                                rows()[0].pages[0].fields = fields;
                                act(status === 'posted' ? 'confirm' : 'save');
                            },
                        }
                    );
                    form.addEventListener(
                        'document-attachment',
                        function (event) {
                            manualAttachments[rows()[0].id] = event.detail;
                        },
                        { once: true }
                    );
                    form.querySelector('[data-manual-workspace]').onchange = async function (
                        event
                    ) {
                        var previous = model.selection.workspace_client_id;
                        var unsaved = manual.readManual(form, fieldsOf(rows()[0]));
                        model.selection.workspace_client_id = Number(event.target.value);
                        try {
                            await save(true);
                            var own = direction() === 'purchase' ? 'buyer' : 'seller';
                            var saved = fieldsOf(rows()[0]);
                            unsaved[own + '_tax'] = saved[own + '_tax'];
                            unsaved[own + '_name'] = saved[own + '_name'];
                            (unsaved.items || []).forEach(function (item) {
                                delete item.product_id;
                                delete item.code;
                            });
                            ((unsaved.pos_form || {}).lines || []).forEach(function (line) {
                                line.product_id = null;
                                line.code = '';
                                line.product_matched = false;
                            });
                            rows()[0].pages[0].fields = unsaved;
                            review.render();
                        } catch (_) {
                            model.selection.workspace_client_id = previous;
                            event.target.value = String(previous);
                            show('failed', 'error');
                        }
                    };
                    form.hidden = false;
                    state.hidden = true;
                },
                canConfirm: function () {
                    return true;
                },
                setBusy: function (on) {
                    form.querySelectorAll('button,input,select').forEach(function (el) {
                        el.disabled = on;
                    });
                },
            };
            review.render();
            return;
        }
        review = R.create({
            root: form,
            records: rows,
            direction: direction,
            text: t,
            title: function () {
                return t(
                    direction() === 'sales'
                        ? 'salesTitle'
                        : direction() === 'purchase'
                          ? 'purchaseTitle'
                          : 'title'
                );
            },
            issues: function (record) {
                fieldsOf(record);
                var invalidItems = (fieldsOf(record).items || []).some(function (item) {
                    return (
                        !Number.isFinite(Number(item.qty)) ||
                        Number(item.qty) <= 0 ||
                        !Number.isFinite(Number(item.price)) ||
                        Number(item.price) <= 0
                    );
                });
                var problems = R.documentIssues(record, direction(), {
                    requirePostingKind: false,
                }).filter(function (issue) {
                    return ['invoice_number', 'seller_name', 'total_amount'].indexOf(issue) < 0;
                });
                if (invalidItems && problems.indexOf('items') < 0) problems.push('items');
                return problems;
            },
            previewPlaceholder: function (record) {
                return record.filename === 'manual'
                    ? { th: 'กรอกเอง', zh: '手动录入', en: 'Manual entry', ja: '手動入力' }[lang] ||
                          'กรอกเอง'
                    : t('loadingPreview');
            },
            globalReady: function () {
                return true;
            },
            renderPrefix: function () {
                return '';
            },
            renderDetail: renderDetail,
            bindDetail: bindDetail,
            onAction: act,
            authHeaders: function () {
                return { Authorization: 'Bearer ' + token() };
            },
        });
        review.render();
        if (rows().length === 1) form.querySelector('[data-open-record]').click();
        state.hidden = true;
    }

    document.documentElement.lang = lang;
    document.getElementById('lang').value = lang;
    document.getElementById('lang').onchange = function (event) {
        if (manual && rows().length === 1 && rows()[0].filename === 'manual' && !form.hidden)
            rows()[0].pages[0].fields = manual.readManual(form, fieldsOf(rows()[0]));
        lang = event.target.value;
        document.documentElement.lang = lang;
        localStorage.setItem('pearnly_lang', lang);
        if (review) review.render();
        if (!state.hidden) show(stateKey, stateKind);
    };
    show('loading');
    Promise.all([
        import('/static/dist/erp-manual-document.js?v=pos-profile-3').then(function (module) {
            manual = module;
            manual.setProductLookup(function (query) {
                return api(
                    '/api/line/erp/draft/' +
                        encodeURIComponent(draftId) +
                        '/products?q=' +
                        encodeURIComponent(query)
                ).then(function (data) {
                    return data.products || [];
                });
            });
        }),
        window.lineIntakeReviewI18n.load(),
        window.lineIntakeLiff.boot({
            flow: 'erp-intake',
            configUrl: '/api/line/erp/liff/config',
            authUrl: '/api/line/erp/liff/auth',
            tokenKey: 'erp_line_token',
        }),
    ])
        .then(function (values) {
            var auth = values[2];
            draftId = auth.draftId;
            return api('/api/line/erp/draft/' + encodeURIComponent(draftId));
        })
        .then(function (value) {
            model = value;
            buildReview();
        })
        .catch(function (error) {
            show(error.status === 401 || error.status === 403 ? 'expired' : 'failed', 'error');
        });
})();
