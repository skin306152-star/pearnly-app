// UI 设计合规扫描器 · 确定性扫描每个源文件每一行,列出不符合 DESIGN_SYSTEM 的地方。
// 跑法: node scripts/ui_design_lint.mjs   (报告同时写 docs/ui/UI_LINT_REPORT.txt)
//       node scripts/ui_design_lint.mjs --gate              棘轮闸:任一类命中数超 baseline 即 exit 1
//       node scripts/ui_design_lint.mjs --update-baseline   命中数下降后收紧 baseline(升级须显式跑这条)
// 目的: 替代肉眼/窗口自报,100% 不漏。存量(POS/admin/i18n 文字强调)在 baseline 里,只许降不许升。
import fs from 'fs';
import path from 'path';

const BASELINE_FILE = 'scripts/ui_lint_baseline.json';
const MODE_GATE = process.argv.includes('--gate');
const MODE_UPDATE = process.argv.includes('--update-baseline');

// 'static' 已含 'static/pos',单列会让 static/pos/* 被走两遍(基线双计含水分)→ 只留 'static'。
const ROOTS = ['src/home', 'static'];
// 设计系统"实物源/令牌定义"文件——允许裸 hex(它们就是令牌来源),扫描时跳过 hex 检查
const TOKEN_SOURCE =
    /kit-final\.html|templates\.html|dashboard-final\.html|a\.html|b\.html|c\.html|kit\.html|i18n-data|sales-wizard-i18n|home-01-base\.css|console-theme\.css|home-48-recon-redesign\.css|ai-theme\.css/i;
const SKIP_DIR = /node_modules|[\\/]dist[\\/]|_mock|\.map$/i;
// vendor/ 是自托管的第三方运行时(React/THREE/GSAP/support.js/字体),不是 Pearnly 应用设计
// 系统的一部分,且成百上千个 minified 文件无法逐个加标记 → 只能按目录整块排除。
// 单文件的营销页/自包含独立页(portal.dc / *-login / reset)改走文件头标记(见 STANDALONE_MARKER)。
const MARKETING_EXCLUDE = /static[\\/]landing[\\/]vendor[\\/]/i;
// 文件头标记豁免:自包含独立页(登录/重置/门户营销稿)页内自带局部 :root 令牌,不接应用设计
// 系统的 CSS 变量基建,整版配色/emoji 即设计稿本身。在文件前 5 行放 `<!-- ui-lint: standalone -->`
// 即整文件跳过——比文件名正则稳:文件挪目录/改名不会意外落回扫描(reset.html 从此不再靠"住仓库根"侥幸)。
const STANDALONE_MARKER = /<!--\s*ui-lint:\s*standalone\s*-->/;
const EXT = /\.(ts|js|css|html)$/i;

const CHECKS = [
    { key: '旧色/旧蓝(应改令牌)', re: /#2563EB|#1D4ED8|#1e40af/gi },
    {
        key: '旧token名(应用全局emerald)',
        re: /--(blue|rep-blue|c-blue|invp|pur-blue|brand-blue)\b/gi,
    },
    { key: 'emoji当图标(应换Lucide)', re: /\p{Extended_Pictographic}/gu, skipToken: false },
    // 只抓"固定 max-width"(非响应式):@media 查询里的 max-width 是正确的响应式断点,
    // 类名"查是否@media"本就承诺只看 @media 之外的固定宽度 → skipLineRe 跳过 @media 行。
    {
        key: '小固定max-width(查是否@media)',
        re: /max-width:\s*([1-9]\d{2})px/gi,
        skipLineRe: /@media/i,
    },
    // `.drawer\b` 会误匹配 `.drawer-decision-zone` 等子元素选择器(已存在抽屉的内部结构,
    // 非新弹窗)→ 收紧成"drawer 作为完整类名"(后面不接 - 或字母数字),只抓真正的抽屉容器。
    {
        key: '内联旧弹窗/抽屉',
        re: /class=["']modal["'][^>]*style=|\.drawer(?![-\w])|class=["']drawer/gi,
    },
    { key: '自曝/AI文案', re: /抽不准|อ่านไม่แม่น|人工智能/gi },
    { key: '原生弹窗(禁)', re: /(?<![.\w])(alert|confirm|prompt)\s*\(/g },
    { key: '超高z-index', re: /z-index:\s*9{3,}/gi },
    { key: 'i18n原始键残留', re: /-ago-suffix|time-hour|time-day/gi },
];
// 裸 hex 单列(量大,单独统计;TOKEN_SOURCE 跳过)
const HEX = /#[0-9a-fA-F]{6}\b/g;

function walk(dir, out) {
    let ents;
    try {
        ents = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
        return;
    }
    for (const e of ents) {
        const p = path.join(dir, e.name);
        if (SKIP_DIR.test(p) || MARKETING_EXCLUDE.test(p)) continue;
        if (e.isDirectory()) walk(p, out);
        else if (EXT.test(e.name) && !hasStandaloneMarker(p)) out.push(p);
    }
}

// 文件头(前 5 行内)带 standalone 标记 → 整文件豁免扫描(见 STANDALONE_MARKER)。
function hasStandaloneMarker(f) {
    try {
        return STANDALONE_MARKER.test(fs.readFileSync(f, 'utf8').split('\n', 5).join('\n'));
    } catch {
        return false;
    }
}

const files = [];
for (const r of ROOTS) walk(r, files);

const results = {}; // check -> [{file, count, sampleLines}]
for (const c of CHECKS) results[c.key] = [];
const hexResult = [];

for (const f of files) {
    let txt;
    try {
        txt = fs.readFileSync(f, 'utf8');
    } catch {
        continue;
    }
    const lines = txt.split('\n');
    const isTokenSrc = TOKEN_SOURCE.test(f);
    for (const c of CHECKS) {
        let cnt = 0;
        const samples = [];
        lines.forEach((ln, i) => {
            if (c.skipLineRe && c.skipLineRe.test(ln)) return;
            const m = ln.match(c.re);
            if (m) {
                cnt += m.length;
                if (samples.length < 2) samples.push(i + 1 + ': ' + ln.trim().slice(0, 90));
            }
        });
        if (cnt) results[c.key].push({ file: f, count: cnt, samples });
    }
    if (!isTokenSrc) {
        const hx = (txt.match(HEX) || []).length;
        if (hx) hexResult.push({ file: f, count: hx });
    }
}

let report = `# UI 设计合规扫描报告 · ${files.length} 个源文件全扫\n\n`;
for (const c of CHECKS) {
    const rows = results[c.key].sort((a, b) => b.count - a.count);
    const total = rows.reduce((s, r) => s + r.count, 0);
    report += `\n## ${c.key} — 命中 ${total}(${rows.length} 文件)\n`;
    for (const r of rows) {
        report += `  ${String(r.count).padStart(4)}  ${r.file}\n`;
        for (const s of r.samples) report += `        └ ${s}\n`;
    }
    if (!rows.length) report += `  ✅ 无\n`;
}
const hexRows = hexResult.sort((a, b) => b.count - a.count);
const hexTotal = hexRows.reduce((s, r) => s + r.count, 0);
report += `\n## 裸 hex 色值(应改令牌·已排除令牌定义文件)— 命中 ${hexTotal}(${hexRows.length} 文件)\n`;
for (const r of hexRows) report += `  ${String(r.count).padStart(4)}  ${r.file}\n`;

fs.mkdirSync('docs/ui', { recursive: true });
fs.writeFileSync('docs/ui/UI_LINT_REPORT.txt', report);
// 控制台打印汇总
console.log(`扫了 ${files.length} 个源文件。各类违规汇总:`);
for (const c of CHECKS) {
    const rows = results[c.key];
    const total = rows.reduce((s, r) => s + r.count, 0);
    console.log(`  ${total ? '❌' : '✅'} ${c.key}: ${total} 命中 / ${rows.length} 文件`);
}
console.log(`  ⚠ 裸hex: ${hexTotal} 命中 / ${hexRows.length} 文件`);
console.log(`\n完整报告: docs/ui/UI_LINT_REPORT.txt`);

// ---- 棘轮闸:与 baseline 比对,只许降不许升 ----
const totals = {};
for (const c of CHECKS) totals[c.key] = results[c.key].reduce((s, r) => s + r.count, 0);
totals['裸hex'] = hexTotal;

if (MODE_UPDATE) {
    fs.writeFileSync(BASELINE_FILE, JSON.stringify(totals, null, 2) + '\n');
    console.log(`baseline 已写入 ${BASELINE_FILE}`);
} else if (MODE_GATE) {
    let base;
    try {
        base = JSON.parse(fs.readFileSync(BASELINE_FILE, 'utf8'));
    } catch {
        console.error(`❌ 缺 ${BASELINE_FILE} · 先跑 --update-baseline 建立基线`);
        process.exit(1);
    }
    const ups = Object.keys(totals).filter((k) => totals[k] > (base[k] ?? 0));
    if (ups.length) {
        console.error(
            `\n❌ UI lint 棘轮闸:以下类别命中数超过 baseline(新增违规 · 看上方报告定位):`
        );
        for (const k of ups) console.error(`   ${k}: ${base[k] ?? 0} → ${totals[k]}`);
        process.exit(1);
    }
    const downs = Object.keys(totals).filter((k) => totals[k] < (base[k] ?? 0));
    if (downs.length)
        console.log(`\n命中数已下降(${downs.join(' / ')})· 跑 --update-baseline 收紧基线防回潮`);
    console.log('✅ UI lint 棘轮闸通过');
}
