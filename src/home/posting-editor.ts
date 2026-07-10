// ============================================================
// src/home/posting-editor.ts · 过账人工改判共用组件(P3c)
//
// 抽自 erp-express-detail.ts 的 F5 单别人工可选(_doctypeCell/_saveDoctype/_srcBadge)·
// 加第二轴「货/费」(item_type)后两条推送车道(Express + MR.ERP)共用同一套改判控件:
//   现/赊(payment · doctype 展示层用 HP/RR)· 货/费(item_type · goods/expense)。
// 后端 PATCH /api/history/{id}/posting 语义:缺省键=不动 · null=清除人工裁决。保存做脏轴
// 追踪(select 渲染时记初值 data-initial),只把用户实际改动过的轴放进 body——动过且选
// 「自动」→ 该键=null(显式清除);没动过 → 键不发。否则 MR.ERP 入口(初值恒「自动」·
// 载荷无 src 可读)只改现/赊也会连带发 item_type:null,把此前设过的人工货/费裁决静默清掉。
// 两轴都没动 → 不发请求,就地提示无改动。保存成功后初值同步为当前值,连点不重发。
//
// 来源徽标(SRC axis):doctype 轴读 doctype_src(manual/explicit/doc_type/profile/bank/
// config_default);item 轴读 item_src(manual/judge_direction=<kind>)· 值域外不渲染徽标,
// 不伪造「已经手动定过」。调用方(Express/MR.ERP)各自算好 select 初值再传入——是否把某个
// src 当「人工回填」不是本组件的业务判断,留给调用方(两处判据略有出入,见各自调用点注释)。
//
// document 级委派(一次性绑定)· 不借宿主 erp-log-detail 的 [data-receipt-action] 链路
// (那条链路末尾无条件 closeAll 会把抽屉关掉)· 抽屉每次重开都是新 DOM,元素级监听会失效。
// ============================================================
/* global escapeHtml, token */
(function () {
    'use strict';

    function _esc(s: any) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _t(k: string, vars?: any) {
        try {
            var v = typeof t === 'function' ? t(k, vars) : k;
            return v || k;
        } catch (e) {
            return k;
        }
    }

    interface PostingEditorOpts {
        doctype?: 'HP' | 'RR' | null;
        doctypeSrc?: string | null;
        doctypeSelVal?: 'auto' | 'HP' | 'RR';
        itemType?: 'goods' | 'expense' | null;
        itemSrc?: string | null;
        itemSelVal?: 'auto' | 'goods' | 'expense';
    }

    // 来源徽标 · 复用 .log-tag 既有两色令牌:manual(人工)醒目 · 其余系统推定态柔和。
    var DOCTYPE_SRC_KEYS: Record<string, string> = {
        manual: 'expd-src-manual',
        explicit: 'expd-src-explicit',
        doc_type: 'expd-src-doc_type',
        profile: 'expd-src-profile',
        bank: 'expd-src-bank',
        config_default: 'expd-src-config_default',
    };
    function badge(axis: 'doctype' | 'item', src: any): string {
        var s = String(src || '');
        if (!s) return '';
        var key = '';
        var manual = s === 'manual';
        if (axis === 'item') {
            if (manual) key = 'expd-src-manual';
            else if (s.indexOf('judge_direction=') === 0) key = 'expd-item-src-auto';
        } else {
            key = DOCTYPE_SRC_KEYS[s];
        }
        if (!key) return '';
        var cls = manual ? 'manual' : 'auto';
        return '<span class="log-tag ' + cls + ' posting-src-badge">' + _esc(_t(key)) + '</span>';
    }

    function _selectOpts(current: string, list: string[][]): string {
        return list
            .map(function (o) {
                return (
                    '<option value="' +
                    o[0] +
                    '"' +
                    (o[0] === current ? ' selected' : '') +
                    '>' +
                    _esc(o[1]) +
                    '</option>'
                );
            })
            .join('');
    }

    function _axisBlock(
        label: string,
        valueText: string,
        badgeHtml: string,
        selectHtml: string
    ): string {
        return (
            '<div class="posting-axis"><label>' +
            _esc(label) +
            '</label><strong>' +
            _esc(valueText) +
            badgeHtml +
            '</strong>' +
            selectHtml +
            '</div>'
        );
    }

    // 一个 posting-editor-cell = 两轴展示(现/赊 + 货/费)+ 两个 select + 一个共享保存按钮。
    // 无 historyId(理论不该发生 · 兜底)不渲染任何控件,退回纯展示。
    function cell(historyId: any, opts?: PostingEditorOpts): string {
        var o = opts || {};
        var doctypeText =
            o.doctype === 'HP'
                ? _t('expd-doctype-hp')
                : o.doctype === 'RR'
                  ? _t('expd-doctype-rr')
                  : '-';
        var itemText =
            o.itemType === 'goods'
                ? _t('expd-item-goods')
                : o.itemType === 'expense'
                  ? _t('expd-item-expense')
                  : '-';
        var docSelVal = o.doctypeSelVal || 'auto';
        var itemSelVal = o.itemSelVal || 'auto';

        // data-initial=渲染时初值 · 保存时脏轴比对用(只发用户实际改动过的轴)。
        var docSelect = historyId
            ? '<select class="posting-select" data-axis="doctype" data-initial="' +
              docSelVal +
              '">' +
              _selectOpts(docSelVal, [
                  ['auto', _t('expd-doctype-auto')],
                  ['HP', _t('expd-doctype-hp')],
                  ['RR', _t('expd-doctype-rr')],
              ]) +
              '</select>'
            : '';
        var itemSelect = historyId
            ? '<select class="posting-select" data-axis="item" data-initial="' +
              itemSelVal +
              '">' +
              _selectOpts(itemSelVal, [
                  ['auto', _t('expd-item-auto')],
                  ['goods', _t('expd-item-goods')],
                  ['expense', _t('expd-item-expense')],
              ]) +
              '</select>'
            : '';

        var body =
            _axisBlock(
                _t('expd-f-doctype'),
                doctypeText,
                badge('doctype', o.doctypeSrc),
                docSelect
            ) + _axisBlock(_t('expd-f-itemtype'), itemText, badge('item', o.itemSrc), itemSelect);

        var footer = historyId
            ? '<div class="posting-edit-actions">' +
              '<button type="button" class="btn btn-ghost btn-tiny posting-save" data-history-id="' +
              _esc(String(historyId)) +
              '">' +
              _esc(_t('expd-doctype-save')) +
              '</button>' +
              '<span class="posting-msg"></span>' +
              '</div>'
            : '';

        return '<div class="erp-detail-cell posting-editor-cell">' + body + footer + '</div>';
    }

    // 独立成段(MR.ERP 详情用 · 没有现成识别字段网格可挂)· Express 卡继续用 cell() 直接
    // 嵌进它自己的 erp-detail-grid,不再套一层标题。
    function section(historyId: any, opts?: PostingEditorOpts): string {
        return (
            '<section class="erp-detail-sec"><h3>' +
            _esc(_t('posting-editor-title')) +
            '</h3>' +
            cell(historyId, opts) +
            '</section>'
        );
    }

    // 保存脏轴裁决 → PATCH /api/history/{id}/posting。只发用户实际改动过的轴(与 data-initial
    // 比对):动过且选「自动」→ 该键=null(显式清除人工裁决);没动过 → 键不发(后端缺省键=
    // 不动,不误清另一轴此前的人工裁决)。两轴都没动 → 不发请求,就地提示无改动。
    // 三态文案(保存中/已保存/失败)就地更新触发按钮同格的 .posting-msg,不重渲整个抽屉——
    // 详情数据留在闭包外,重渲要靠人手动重新打开详情,状态诚实不假装同步。
    function _dirty(sel: HTMLSelectElement | null): boolean {
        return !!sel && sel.value !== sel.getAttribute('data-initial');
    }
    async function _save(btn: HTMLElement): Promise<void> {
        var cellEl = btn.closest('.posting-editor-cell');
        var docSel = cellEl
            ? (cellEl.querySelector(
                  '.posting-select[data-axis="doctype"]'
              ) as HTMLSelectElement | null)
            : null;
        var itemSel = cellEl
            ? (cellEl.querySelector(
                  '.posting-select[data-axis="item"]'
              ) as HTMLSelectElement | null)
            : null;
        var msg = cellEl ? (cellEl.querySelector('.posting-msg') as HTMLElement | null) : null;
        var historyId = btn.getAttribute('data-history-id');
        if (!historyId) return;
        var payload: Record<string, string | null> = {};
        if (_dirty(docSel)) {
            var docVal = docSel!.value;
            payload.payment = docVal === 'HP' ? 'cash' : docVal === 'RR' ? 'credit' : null;
        }
        if (_dirty(itemSel)) {
            var itemVal = itemSel!.value;
            payload.item_type = itemVal === 'goods' || itemVal === 'expense' ? itemVal : null;
        }
        if (!Object.keys(payload).length) {
            if (msg) {
                msg.textContent = _t('posting-no-change');
                msg.className = 'posting-msg mid';
            }
            return;
        }
        (btn as HTMLButtonElement).disabled = true;
        if (docSel) docSel.disabled = true;
        if (itemSel) itemSel.disabled = true;
        if (msg) {
            msg.textContent = _t('expd-doctype-saving');
            msg.className = 'posting-msg mid';
        }
        try {
            var resp = await fetch('/api/history/' + encodeURIComponent(historyId) + '/posting', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: 'Bearer ' + token,
                },
                body: JSON.stringify(payload),
            });
            var j: any = {};
            try {
                j = await resp.json();
            } catch (e) {
                /* 空体也可能是成功(理论不会 · 兜底不炸) */
            }
            if (!resp.ok || !j.ok) throw new Error('save failed');
            // 初值同步为已保存值 · 连点保存不重发,后续脏轴比对以最新已存状态为基准。
            if (docSel) docSel.setAttribute('data-initial', docSel.value);
            if (itemSel) itemSel.setAttribute('data-initial', itemSel.value);
            if (msg) {
                msg.textContent = _t('expd-doctype-saved');
                msg.className = 'posting-msg ok';
            }
        } catch (e) {
            if (msg) {
                msg.textContent = _t('expd-doctype-save-fail');
                msg.className = 'posting-msg fail';
            }
        } finally {
            (btn as HTMLButtonElement).disabled = false;
            if (docSel) docSel.disabled = false;
            if (itemSel) itemSel.disabled = false;
        }
    }

    var _bound = false;
    function _bindOnce(): void {
        if (_bound) return;
        _bound = true;
        document.addEventListener('click', function (e: Event) {
            var tgt = e.target as HTMLElement;
            var btn = tgt.closest && (tgt.closest('.posting-save') as HTMLElement | null);
            if (!btn) return;
            _save(btn);
        });
    }
    _bindOnce();

    (window as any).PostingEditor = { cell: cell, section: section, badge: badge };
})();
