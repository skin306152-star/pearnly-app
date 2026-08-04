/*
 * Pearnly POS · pos-receipt.js · 本地兜底小票(离线 / 取不到服务端 PDF 时)· G1 同轴
 *
 * 与服务端 PDF(services/pos/receipt_render.py)同一套法定要素:法定抬头按 vat_registered
 * 切(ABB / 普通收据)、税号、含税声明、收银员、VAT 拆行、Register No. 有号才印、页脚。
 * 票面法定文案是法规文本(泰文为主),不吃 UI 语言切换。
 * 二维码(G4)不做本地兜底:离线造不出可用码,印死码不如不印。
 */
(function () {
    const POS = window.POS;
    const state = POS.state;
    const fmt = POS.fmt;
    const KEY = 'pos_store_receipt';

    // bootstrap 店档 → 合规字段缓存(pos.js cacheStoreInfo 调)。
    // 合规字段没下发(老后端)时保留旧缓存,别把 vat_registered 抹成 false 改掉票面身份。
    POS.receiptInfo = {
        save(store) {
            if (!store || !('vat_registered' in store)) return;
            try {
                localStorage.setItem(
                    KEY,
                    JSON.stringify({
                        tax_id: store.tax_id || '',
                        phone: store.phone || '',
                        vat_registered: !!store.vat_registered,
                        register_no: store.pos_register_no || '',
                        footer_text: store.footer_text || '',
                    })
                );
            } catch (_) {}
        },
        load() {
            try {
                return JSON.parse(localStorage.getItem(KEY) || 'null');
            } catch (_) {
                return null;
            }
        },
    };

    function headBlock(sale, info, isVat, inclVat) {
        const dt = sale.sold_at ? new Date(sale.sold_at) : new Date();
        const thaiDate =
            String(dt.getDate()).padStart(2, '0') +
            '/' +
            String(dt.getMonth() + 1).padStart(2, '0') +
            '/' +
            (dt.getFullYear() + 543) +
            ' ' +
            POS.hm(dt);
        return [
            state.storeAddress
                ? '<div class="meta c">' + POS.esc(state.storeAddress) + '</div>'
                : '',
            info && info.phone ? '<div class="meta c">โทร ' + POS.esc(info.phone) + '</div>' : '',
            info && info.tax_id
                ? '<div class="c">เลขประจำตัวผู้เสียภาษี ' + POS.esc(info.tax_id) + '</div>'
                : '',
            info && info.register_no
                ? '<div class="meta c">เครื่องบันทึกเงินสดเลขที่ (Register No.): ' +
                  POS.esc(info.register_no) +
                  '</div>'
                : '',
            '<hr>',
            isVat
                ? '<div class="ttl">ใบกำกับภาษีอย่างย่อ</div><div class="c">Receipt / Tax Invoice (ABB)</div>' +
                  (inclVat
                      ? '<div class="meta c">ราคารวมภาษีมูลค่าเพิ่มแล้ว (VAT Included)</div>'
                      : '')
                : '<div class="ttl">ใบเสร็จรับเงิน</div><div class="c">Receipt</div>',
            '<hr>',
            '<div>เลขที่ (No.) <b>' + POS.esc(sale.receipt_no || '-') + '</b></div>',
            '<div>วันที่ (Date) ' + thaiDate + '</div>',
            state.cashier && state.cashier.display_name
                ? '<div>พนักงาน (Cashier) ' + POS.esc(state.cashier.display_name) + '</div>'
                : '',
        ].join('');
    }

    function tableRows(sale, isVat, inclVat) {
        const rows = (sale.lines || [])
            .map(
                (l) =>
                    '<tr><td>' +
                    POS.esc(POS.nm(l.name)) +
                    ' ×' +
                    l.qty +
                    '</td><td class="r">฿' +
                    fmt(l.price * l.qty) +
                    '</td></tr>'
            )
            .join('');
        const vatLine =
            isVat && sale.vat_amount != null
                ? '<tr><td>ภาษีมูลค่าเพิ่ม 7%' +
                  (inclVat ? ' (รวมใน)' : ' (VAT)') +
                  '</td><td class="r">' +
                  fmt(sale.vat_amount) +
                  '</td></tr>'
                : '';
        const methodLine = (sale.payments || [])
            .map(
                (p) =>
                    '<tr><td>' +
                    POS.t('posui.pay.' + (p.method === 'qr' ? 'promptpay' : p.method)) +
                    (p.ref ? ' · ' + POS.esc(p.ref) : '') +
                    '</td><td class="r">฿' +
                    fmt(p.amount) +
                    '</td></tr>'
            )
            .join('');
        const changeLine =
            sale.change_amount != null && Number(sale.change_amount) > 0
                ? '<tr><td>เงินทอน (Change)</td><td class="r">฿' +
                  fmt(sale.change_amount) +
                  '</td></tr>'
                : '';
        return (
            rows +
            // 合计标签同服务端 PDF 固定写法(票面法规文本不跟 UI 语言走)
            '<tr class="tot"><td>ยอดสุทธิ (Total)</td><td class="r">฿' +
            fmt(sale.grand_total) +
            '</td></tr>' +
            vatLine +
            methodLine +
            changeLine
        );
    }

    // 弹窗即打印。lastSale 数据来自成交结果(在线单)或离线 outbox 回执。
    POS.receipt = {
        printLocal(sale) {
            const info = POS.receiptInfo.load();
            // 缓存缺失时按票号前缀兜底,方向安全:宁印普通收据,不给未注册户冒印税票字样。
            const isVat = info ? !!info.vat_registered : /^ABB-/.test(sale.receipt_no || '');
            const inclVat = !state.payment || state.payment.price_includes_vat !== false;
            const foot =
                '<hr><div class="c">ขอบคุณค่ะ / Thank You</div>' +
                (info && info.footer_text
                    ? '<div class="meta c">' + POS.esc(info.footer_text) + '</div>'
                    : '') +
                '<div class="meta c">Powered by Pearnly POS</div>';
            const html =
                '<!doctype html><html><head><meta charset="utf-8"><title>' +
                POS.esc(sale.receipt_no || '') +
                '</title><style>body{font:12px monospace;width:280px;margin:0 auto;padding:12px;color:#111}' +
                'h3{text-align:center;margin:0 0 4px}table{width:100%;border-collapse:collapse}' +
                'td{padding:2px 0}.r{text-align:right}.tot td{border-top:1px dashed #000;padding-top:6px;font-weight:700}' +
                '.meta{color:#555}.c{text-align:center}.ttl{text-align:center;font-weight:700;font-size:14px}' +
                'hr{border:none;border-top:1px dashed #777;margin:6px 0}</style></head><body><h3>' +
                POS.esc(state.store || 'Pearnly POS') +
                '</h3>' +
                headBlock(sale, info, isVat, inclVat) +
                '<table>' +
                tableRows(sale, isVat, inclVat) +
                '</table>' +
                foot +
                '<scr' +
                'ipt>window.onload=function(){window.print()}</scr' +
                'ipt></body></html>';
            const w = window.open('', '_blank', 'width=320,height=620');
            if (!w) {
                POS.toast(POS.t('posui.done.print'));
                return;
            }
            w.document.write(html);
            w.document.close();
        },
    };
})();
