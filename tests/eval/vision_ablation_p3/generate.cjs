const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium } = require('playwright');

const OUT = __dirname;
const ROOT = path.resolve(OUT, '../../..');
const FONT = `file:///${path.join(ROOT, 'services/export/fonts/Sarabun-Regular.ttf').replace(/\\/g, '/')}`;
const FONT_B = `file:///${path.join(ROOT, 'services/export/fonts/Sarabun-Bold.ttf').replace(/\\/g, '/')}`;
const SEED = 73031;

const sellers = [
    ['บริษัท เอเชีย ออฟฟิศ ซัพพลาย จำกัด', tax('010556203310')],
    ['ร้านวัสดุก่อสร้าง เจริญทรัพย์', tax('073555900124')],
    ['บริษัท เมืองไทยโลจิสติกส์ จำกัด', tax('010555812345')],
    ['หจก. พีพี โปรเคียวเมนท์', tax('090356300778')],
    ['CP ALL, 7-Eleven สาขาสีลม', tax('010754200001')],
    ["Lotus's สาขาพระราม 4", tax('010754300012')],
];
const buyers = [
    ['บริษัท ดาต้าทูลส์ จำกัด', tax('073552700028')],
    ['บริษัท เพิร์นลี่ เทค จำกัด', tax('010556406152')],
    ['หจก. สกิน แอนด์ โค', tax('090356300778')],
];
const items = [
    ['กระดาษ A4', 3, 12000],
    ['หมึกพิมพ์', 2, 79000],
    ['ค่าขนส่ง', 1, 8500],
    ['แฟ้มเอกสาร', 6, 3500],
    ['กาแฟเย็น', 2, 4500],
    ['ข้าวกล่อง', 1, 10900],
    ['น้ำดื่ม', 1, 1000],
    ['สายชาร์จ USB-C', 2, 19900],
];
const idNames = [
    ['นาย', 'สมชาย', 'ใจดี', 'Somchai Jaidee'],
    ['นางสาว', 'กมลวรรณ', 'ศรีสุข', 'Kamonwan Srisuk'],
    ['นาย', 'ธีรภัทร', 'บุญมี', 'Teerapat Boonmee'],
    ['นาง', 'อรทัย', 'แสงทอง', 'Orathai Saengthong'],
    ['นาย', 'ปกรณ์', 'วงศ์ชัย', 'Pakorn Wongchai'],
    ['นางสาว', 'ณัฐธิดา', 'จันทร์เพ็ญ', 'Nattida Chanpen'],
];
const addresses = [
    ['99/1', '3', '', '', 'บางรัก', 'บางรัก', 'กรุงเทพมหานคร', '10500'],
    ['12/7', '5', 'ลาดพร้าว 71', '', 'ลาดพร้าว', 'ลาดพร้าว', 'กรุงเทพมหานคร', '10230'],
    ['45', '2', '', 'สุขุมวิท', 'ปากน้ำ', 'เมืองสมุทรปราการ', 'สมุทรปราการ', '10270'],
    ['8/88', '9', '', '', 'ช้างเผือก', 'เมืองเชียงใหม่', 'เชียงใหม่', '50300'],
    ['301', '1', '', 'มิตรภาพ', 'ในเมือง', 'เมืองขอนแก่น', 'ขอนแก่น', '40000'],
];

function tax(prefix12) {
    const s = String(prefix12).padEnd(12, '0').slice(0, 12);
    let sum = 0;
    for (let i = 0; i < 12; i++) sum += Number(s[i]) * (13 - i);
    return s + ((11 - (sum % 11)) % 10);
}
function idNo(i) {
    return tax(String(100000000000 + ((SEED + i * 7919) % 89999999999)).padStart(12, '0'));
}
function money(cents) {
    return (Math.round(cents) / 100).toFixed(2);
}
function esc(s) {
    return String(s ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
    );
}
function writeJson(file, data) {
    fs.writeFileSync(file, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
}
function formatJsonOutputs() {
    const args = [
        'prettier',
        '--write',
        'summary.json',
        'ground_truth/**/*.json',
        'id_card/ground_truth/**/*.json',
    ];
    const command =
        process.platform === 'win32' ? ['cmd.exe', ['/c', 'npx.cmd', ...args]] : ['npx', args];
    spawnSync(command[0], command[1], { cwd: OUT, stdio: 'ignore' });
}
function reset() {
    for (const rel of ['images', 'ground_truth', 'id_card/images', 'id_card/ground_truth']) {
        const p = path.join(OUT, rel);
        if (fs.existsSync(p)) fs.rmSync(p, { recursive: true, force: true });
        fs.mkdirSync(p, { recursive: true });
    }
}
function baseCss() {
    return `<style>
@font-face{font-family:Sarabun;src:url("${FONT}")}@font-face{font-family:Sarabun;font-weight:700;src:url("${FONT_B}")}
*{box-sizing:border-box}body{margin:0;font-family:Sarabun,Arial,sans-serif;color:#202020}.stage{width:1280px;min-height:1680px;padding:84px;background:linear-gradient(25deg,#6f492d,#b48354 38%,#815838 62%,#c39a6c);position:relative}.stage:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(92deg,rgba(255,255,255,.05) 0 7px,rgba(0,0,0,.04) 7px 14px)}#shot{position:relative;z-index:1}.paper{background:#fffef7;box-shadow:0 22px 44px rgba(0,0,0,.33);position:relative;overflow:hidden}.a4{width:930px;min-height:1280px;margin:auto;padding:46px 56px}.receipt{width:560px;margin:auto;padding:30px 34px;background:#fbf8ea}.idcard{width:980px;height:620px;margin:auto;padding:34px 42px;border-radius:30px;background:linear-gradient(135deg,#e8f1fb,#f8fbff 45%,#ddeaf7);box-shadow:0 22px 46px rgba(0,0,0,.38);overflow:hidden;position:relative}.title{text-align:center;font-weight:700;font-size:40px}.sub{text-align:center;font-size:23px}.row{display:flex;justify-content:space-between;gap:18px}.line{border-top:2px solid #444;margin:14px 0}table{width:100%;border-collapse:collapse;font-size:22px}th,td{border-bottom:1px solid #aaa;padding:7px 5px;text-align:left}td.num,th.num{text-align:right}.total{font-size:30px;font-weight:700}.small{font-size:20px}.muted{color:#555}.crease:after{content:"";position:absolute;inset:-20px;background:linear-gradient(82deg,transparent 30%,rgba(40,40,40,.25) 32%,rgba(255,255,255,.58) 33%,transparent 36%),linear-gradient(101deg,transparent 52%,rgba(35,35,35,.22) 53%,rgba(255,255,255,.5) 54%,transparent 56%);mix-blend-mode:multiply;pointer-events:none}.crumple:before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(172deg,transparent 0 55px,rgba(0,0,0,.08) 56px,rgba(255,255,255,.22) 60px,transparent 66px);pointer-events:none}.lowres{filter:blur(.42px) contrast(.9)}.jpeg{filter:contrast(.9) saturate(.82)}.blur08{filter:blur(.8px)}.glare:after{content:"";position:absolute;inset:-80px;background:linear-gradient(116deg,transparent 34%,rgba(255,255,255,.1) 42%,rgba(255,255,255,.9) 50%,rgba(255,255,255,.32) 58%,transparent 70%),radial-gradient(ellipse at 70% 28%,rgba(255,255,255,.82),rgba(255,255,255,.28) 25%,transparent 43%);pointer-events:none}.skew{transform:rotate(-13deg) perspective(900px) rotateX(6deg)}.photocopy{filter:grayscale(1) contrast(.72);background:#eee}.watermark{position:absolute;left:300px;top:265px;font-size:92px;font-weight:700;color:rgba(0,0,0,.16);transform:rotate(-18deg)}.photo{width:148px;height:188px;background:linear-gradient(#bbb,#888);border:2px solid #777}.idrow{font-size:30px;margin-top:10px}.en{font-size:24px;color:#334}.addr{font-size:23px;margin-top:18px;line-height:1.25}.chip{font-size:20px;color:#475}.seal{position:absolute;right:42px;bottom:34px;border:2px solid #78a;border-radius:50%;width:96px;height:96px;opacity:.45}.heavyTitle{position:relative}.heavyTitle:after{content:"";position:absolute;left:-40px;right:-40px;top:18px;height:18px;background:linear-gradient(90deg,rgba(80,80,80,.35),rgba(255,255,255,.85),rgba(80,80,80,.22))}
</style>`;
}
async function shot(page, inner, out, cls = '') {
    const html = `<!doctype html><html><head><meta charset="utf-8">${baseCss()}</head><body><div class="stage"><div id="shot" class="${cls}">${inner}</div></div></body></html>`;
    await page.setViewportSize({ width: 1280, height: 1680 });
    await page.setContent(html, { waitUntil: 'load' });
    await page.locator('#shot').screenshot({ path: out, type: 'jpeg', quality: 82 });
}
function invoiceGt(c) {
    const { html, rows, docTitle, titleOnCrease, shuffled, ...gt } = c;
    return gt;
}
function preCase(i) {
    const kinds = [
        ['po', 'ใบสั่งซื้อ / PURCHASE ORDER', 'order_evidence'],
        ['quote', 'ใบเสนอราคา / QUOTATION', 'other'],
        ['delivery', 'DELIVERY NOTE', 'other'],
    ];
    const [kind, title, dtype] = kinds[i % 3];
    const seller = sellers[i % sellers.length],
        buyer = buyers[i % buyers.length];
    const rows = [0, 1, 2 + (i % 3)].map((n, k) => {
        const it = items[(i + n) % items.length],
            sub = it[1] * it[2];
        return { name: it[0], qty: String(it[1]), price: money(it[2]), subtotal: money(sub) };
    });
    const sub = rows.reduce((a, r) => a + Math.round(Number(r.subtotal) * 100), 0);
    const vat = i % 2 ? Math.round(sub * 0.07) : 0,
        total = sub + vat;
    const deg = ['fold_crease', 'low_res', 'jpeg_artifact'];
    if (i < 5) deg.push('crumple');
    if (i < 6) deg.push('title_line_creased');
    const id = `pretx_heavy_${kind}_${String(i + 1).padStart(3, '0')}`;
    return {
        id,
        file: `${id}.jpg`,
        document_type: dtype,
        is_not_invoice: true,
        is_copy_or_duplicate: false,
        invoice_number: `${kind.toUpperCase()}-69-${String(3100 + i)}`,
        date: '2026-07-06',
        date_raw: '06/07/2569',
        seller_name: seller[0],
        seller_tax: seller[1],
        seller_addr: 'กรุงเทพมหานคร',
        buyer_name: buyer[0],
        buyer_tax: buyer[1],
        buyer_addr: 'กรุงเทพมหานคร',
        subtotal: money(sub),
        vat: money(vat),
        wht_rate: '',
        wht_amount: '',
        discount: '0.00',
        total_amount: money(total),
        cash_amount: '',
        change_amount: '',
        payment_method: '',
        currency: '',
        items: rows,
        items_count: rows.length,
        notes: '',
        category: 'เอกสาร',
        additional_invoices: [],
        scenario: 'pretransaction_decoy_heavy_degrade',
        traps: ['po_quote_delivery_copy'],
        degradation: deg,
        corpus: 'p3',
        _note: 'not an invoice; heavy folds obscure document title',
        docTitle: title,
        titleOnCrease: i < 6,
    };
}
function preHtml(c) {
    const titleCls = c.titleOnCrease ? 'title heavyTitle' : 'title';
    const rows = c.items
        .map(
            (r, idx) =>
                `<tr><td>${idx + 1}</td><td>${esc(r.name)}</td><td class="num">${r.qty}</td><td class="num">${r.price}</td><td class="num">${r.subtotal}</td></tr>`
        )
        .join('');
    return `<div class="paper a4 crease crumple lowres jpeg"><div class="${titleCls}">${esc(c.docTitle)}</div><div class="sub">${esc(c.seller_name)} · TAX ${c.seller_tax}</div><div class="line"></div><div class="row small"><div>Buyer: ${esc(c.buyer_name)}<br>Buyer Tax: ${c.buyer_tax}</div><div>No. ${c.invoice_number}<br>${c.date_raw}</div></div><table><thead><tr><th>#</th><th>รายการ</th><th class="num">Qty</th><th class="num">Price</th><th class="num">Amount</th></tr></thead><tbody>${rows}</tbody></table><div class="line"></div><div class="row total"><span>Total</span><span>${c.total_amount}</span></div><p class="small muted">เอกสารก่อนซื้อขาย ไม่ใช่ใบกำกับภาษี / This document is not a tax invoice.</p></div>`;
}
function cashBase(i) {
    const combos = [
        [18700, 16700],
        [16700, 18700],
        [8700, 11300],
        [165700, 16700],
        [19900, 10100],
        [9700, 9700],
    ];
    const [total, change] = combos[i % combos.length].map(
        (v, k) => v + Math.floor(i / combos.length) * (k ? 300 : 500)
    );
    const cash = total + change,
        seller = sellers[(i + 4) % sellers.length];
    const a = Math.max(1000, Math.floor(total * 0.62)),
        b = total - a;
    const rows = [
        { name: items[(i + 4) % items.length][0], qty: '1', price: money(a), subtotal: money(a) },
        { name: items[(i + 5) % items.length][0], qty: '1', price: money(b), subtotal: money(b) },
    ];
    const id = `cash_change_p3_${String(i + 1).padStart(3, '0')}`;
    const traps = ['cash_gt_total', 'change_line'];
    if (change > total) traps.push('change_gt_total');
    if (String(Math.floor(total / 100))[0] === String(Math.floor(change / 100))[0])
        traps.push('similar_leading_digits');
    if (i % 2) traps.push('row_order_shuffled');
    return {
        id,
        file: `${id}.jpg`,
        document_type: 'simplified_tax_invoice',
        is_not_invoice: false,
        is_copy_or_duplicate: false,
        invoice_number: `RCP69-${String(8000 + i)}`,
        date: '2026-07-06',
        date_raw: '06/07/69 13:27',
        seller_name: seller[0],
        seller_tax: seller[1],
        seller_addr: 'กรุงเทพมหานคร',
        buyer_name: '',
        buyer_tax: '',
        buyer_addr: '',
        subtotal: money(total),
        vat: '0.00',
        wht_rate: '',
        wht_amount: '',
        discount: '0.00',
        total_amount: money(total),
        cash_amount: money(cash),
        change_amount: money(change),
        payment_method: 'cash',
        currency: '',
        items: rows,
        items_count: rows.length,
        notes: '',
        category: 'ค่าใช้จ่าย',
        additional_invoices: [],
        scenario: 'cash_change_trap',
        traps,
        degradation: [],
        corpus: 'p3',
        base_id: id,
        _note: 'cash tendered minus true total equals change',
        shuffled: i % 2 === 1,
    };
}
function cashHtml(c, blur) {
    const rows = c.items
        .map(
            (r) =>
                `<tr><td>${esc(r.name)}</td><td class="num">${r.qty}</td><td class="num">${r.subtotal}</td></tr>`
        )
        .join('');
    const lines = [
        ['TOTAL / ยอดสุทธิ', c.total_amount, 'total'],
        ['CASH / เงินสด', c.cash_amount, ''],
        ['CHANGE / เงินทอน', c.change_amount, ''],
    ];
    if (c.shuffled) lines.splice(0, 3, lines[1], lines[2], lines[0]);
    return `<div class="paper receipt ${blur ? 'blur08' : ''}"><div class="title">${esc(c.seller_name)}</div><div class="sub">TAX ${c.seller_tax}</div><div class="line"></div><div class="row small"><span>No. ${c.invoice_number}</span><span>${c.date_raw}</span></div><table><tbody>${rows}</tbody></table><div class="line"></div>${lines.map((x) => `<div class="row ${x[2]}"><span>${x[0]}</span><span>${x[1]}</span></div>`).join('')}<div class="sub">ขอบคุณค่ะ</div></div>`;
}
function idCase(i) {
    const band =
        i < 10
            ? 'id_card_clean'
            : i < 20
              ? 'id_card_skewed'
              : i < 30
                ? 'id_card_glare'
                : i < 35
                  ? 'id_card_expired'
                  : 'id_card_photocopy';
    const name = idNames[i % idNames.length],
        addr = addresses[i % addresses.length],
        exp = band === 'id_card_expired' ? '2567-05-11' : '2573-05-11';
    const id = `${band}_${String((i % 10) + 1).padStart(3, '0')}`;
    const raw = `${addr[0]} หมู่ ${addr[1]} ${addr[2] ? `ซ.${addr[2]} ` : ''}${addr[3] ? `ถ.${addr[3]} ` : ''}ต.${addr[4]} อ.${addr[5]} จ.${addr[6]} ${addr[7]}`;
    return {
        id,
        file: `id_card/images/${id}.jpg`,
        people_id: idNo(i),
        prefix_name: name[0],
        first_name: name[1],
        last_name: name[2],
        first_name_en: name[3].split(' ')[0],
        last_name_en: name[3].split(' ')[1],
        birthday_be: `25${30 + (i % 20)}-${String((i % 12) + 1).padStart(2, '0')}-${String((i % 27) + 1).padStart(2, '0')}`,
        issue_date_be: `2563-${String((i % 12) + 1).padStart(2, '0')}-15`,
        expiry_date_be: exp,
        address: {
            house_no: addr[0],
            moo: addr[1],
            soi: addr[2],
            road: addr[3],
            subdistrict: addr[4],
            district: addr[5],
            province: addr[6],
            zipcode: addr[7],
            address_raw: raw,
        },
        scenario: band,
        traps:
            band === 'id_card_expired'
                ? ['expired']
                : band === 'id_card_photocopy'
                  ? ['copy_watermark']
                  : [],
        degradation:
            band === 'id_card_skewed'
                ? ['skew_8_20']
                : band === 'id_card_glare'
                  ? ['glare']
                  : band === 'id_card_photocopy'
                    ? ['grayscale_copy']
                    : [],
        _note: 'synthetic Thai ID card, no real person data',
    };
}
function idHtml(c) {
    const cls = `${c.scenario === 'id_card_skewed' ? 'skew' : ''} ${c.scenario === 'id_card_glare' ? 'glare' : ''} ${c.scenario === 'id_card_photocopy' ? 'photocopy' : ''}`;
    return `<div class="idcard ${cls}"><div class="row"><div><div class="chip">บัตรประจำตัวประชาชน / Thai National ID Card</div><div class="idrow">${c.people_id.replace(/(\d)(?=(\d{4})+$)/g, '$1 ')}</div><div class="idrow">${c.prefix_name} ${esc(c.first_name)} ${esc(c.last_name)}</div><div class="en">${esc(c.first_name_en)} ${esc(c.last_name_en)}</div><div class="addr">${esc(c.address.address_raw)}</div><div class="row small"><span>เกิด ${c.birthday_be}</span><span>ออก ${c.issue_date_be}</span><span>หมดอายุ ${c.expiry_date_be}</span></div></div><div class="photo"></div></div>${c.scenario === 'id_card_photocopy' ? '<div class="watermark">สำเนา</div>' : ''}<div class="seal"></div></div>`;
}
async function main() {
    reset();
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    const manifest = [];
    for (let i = 0; i < 20; i++) {
        const c = preCase(i),
            img = path.join(OUT, 'images', c.file);
        await shot(page, preHtml(c), img, '');
        writeJson(path.join(OUT, 'ground_truth', `${c.id}.json`), invoiceGt(c));
        manifest.push({
            id: c.id,
            file: `images/${c.file}`,
            gt: `ground_truth/${c.id}.json`,
            scenario: c.scenario,
            traps: c.traps,
            degradation: c.degradation,
            corpus: 'p3',
        });
    }
    for (let i = 0; i < 30; i++) {
        const base = cashBase(i);
        for (const [suffix, blur] of [
            ['clear', false],
            ['blur08', true],
        ]) {
            const c = {
                ...base,
                id: `${base.id}_${suffix}`,
                file: `${base.id}_${suffix}.jpg`,
                degradation: blur ? ['blur0.8'] : [],
            };
            await shot(page, cashHtml(c, blur), path.join(OUT, 'images', c.file), '');
            writeJson(path.join(OUT, 'ground_truth', `${c.id}.json`), invoiceGt(c));
            manifest.push({
                id: c.id,
                file: `images/${c.file}`,
                gt: `ground_truth/${c.id}.json`,
                scenario: c.scenario,
                traps: c.traps,
                degradation: c.degradation,
                corpus: 'p3',
            });
        }
    }
    for (let i = 0; i < 40; i++) {
        const c = idCase(i),
            img = path.join(OUT, 'id_card/images', `${c.id}.jpg`);
        await shot(page, idHtml(c), img, '');
        writeJson(path.join(OUT, 'id_card/ground_truth', `${c.id}.json`), c);
        manifest.push({
            id: c.id,
            file: c.file,
            gt: `id_card/ground_truth/${c.id}.json`,
            scenario: c.scenario,
            traps: c.traps,
            degradation: c.degradation,
            doc_type: 'id_card',
        });
    }
    await browser.close();
    fs.writeFileSync(
        path.join(OUT, 'manifest.jsonl'),
        manifest.map((x) => JSON.stringify(x)).join('\n') + '\n',
        'utf8'
    );
    const summary = {
        seed: SEED,
        pretransaction_count: 20,
        cash_change_variants: 30,
        cash_change_images: 60,
        id_card_count: 40,
        image_count: manifest.length,
        scenarios: manifest.reduce((a, x) => ((a[x.scenario] = (a[x.scenario] || 0) + 1), a), {}),
    };
    writeJson(path.join(OUT, 'summary.json'), summary);
    formatJsonOutputs();
    console.log(JSON.stringify(summary, null, 2));
}
main().catch((e) => {
    console.error(e);
    process.exit(1);
});
