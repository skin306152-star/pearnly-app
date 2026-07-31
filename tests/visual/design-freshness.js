/*
 * 基准过期检测 · 视觉照搬闸的第二把尺(治"尺子自己是旧的")。
 *
 * 2026-07-31 起因:pur-settings.html 基准里那面费用科目 chip 墙,生产在 0f5a5fad(7-07)就
 * 搬去「商品 › 费用数据」删光了,基准原样留了三周没有任何东西报过 —— 主闸只比对 MAPPINGS
 * 点名的那几个选择器,点不到的地方烂掉没人知道,而人改页时是照着基准改的。
 *
 * 判据(射程收窄,防误报):基准 <body> 用到的一个 class 算"过期",要同时满足两条 ——
 *   ① 生产该页容器(mapping.layout.sel)渲染出的 DOM 里没有它;
 *   ② 生产文档加载的全部样式表里也没有任何规则提到它。
 * 只满足①不算:那多半是本次 stub 数据没渲染到那一态(空列表/未展开),生产还给它留着样式
 * 就当它还在 —— 宁可漏报也不误报。两条都中 = 生产连样式都不再有,基准该改。
 * 判过期后仍要人看一眼,因为剩两种情况得登记 design/_freshness-allow.json(逐条写理由):
 * 设计稿的装饰件/说明水印,以及稿画了而生产从没实现的示意件。
 * 登记表里已经不再是孤儿的条目同样报红:否则登记表自己会烂成一张免死金牌。
 * 登记豁免的条目在 --list 下逐条打印(带理由),正常模式也打计数 —— 不静默跳过。
 * 闸自己会不会瞎:主闸每次跑先做自检(往基准里塞一个毒 class,必须只逮住它)。
 *
 * 为什么按 class 名比而不是整份 HTML diff:基准是手写设计稿,标签结构/文案/内联样式
 * 跟生产必然不同(生产还带 i18n 与四态),整份比对必然天天红;class 名是两边唯一
 * 共享的词汇表 —— 它正是"这块东西还在不在"的最小可判信号。
 */
/* eslint-disable no-undef */
const fs = require('fs');
const path = require('path');

const ALLOW_FILE = path.join(__dirname, 'design', '_freshness-allow.json');

function loadAllow() {
    const raw = JSON.parse(fs.readFileSync(ALLOW_FILE, 'utf8'));
    const pages = raw.pages || {};
    return { global: raw.global || {}, pages };
}

// 收 root 子树(含 root 自身)上出现过的全部 class 名。root 传 null = 整份 body。
async function classesOf(page, rootSel) {
    return page.evaluate((sel) => {
        const root = sel ? document.querySelector(sel) : document.body;
        if (!root) return null;
        const seen = new Set();
        const take = (el) => el.classList.forEach((c) => seen.add(c));
        take(root);
        root.querySelectorAll('*').forEach(take);
        return [...seen];
    }, rootSel);
}

// 生产文档当前加载的全部样式表里,选择器提到过的 class 名(含各页 loader 运行时 inject 的 <style>)。
// 用途:某个 class 这次没渲染出来,只要生产还给它留着样式,就当"还存在",不判过期(保守挡误报)。
async function styledClassesOf(page) {
    return page.evaluate(() => {
        const seen = new Set();
        const eat = (rules) => {
            for (const r of rules) {
                if (r.selectorText) {
                    for (const m of r.selectorText.matchAll(/\.([A-Za-z_][\w-]*)/g)) seen.add(m[1]);
                }
                if (r.cssRules) eat(r.cssRules); // @media / @supports 内层
            }
        };
        for (const sh of document.styleSheets) {
            try {
                eat(sh.cssRules);
            } catch {
                // 跨源样式表读不到 cssRules — 本闸全同源,真读不到就当没有(只会更保守)
            }
        }
        return [...seen];
    });
}

/*
 * designClasses/prodClasses 为 classesOf 的返回。返回:
 *   orphans  基准有、生产没有、也没登记豁免 → 报红(基准过期或该登记)
 *   dead     登记了豁免但生产已经有了 → 报红(登记表过期,删掉这条)
 *   skipped  本页真正没判的条目(含理由),供 --list 打印
 */
function checkFreshness(designFile, designClasses, prodClasses, styledClasses, allow) {
    const exempt = { ...allow.global, ...(allow.pages[designFile] || {}) };
    const prod = new Set([...prodClasses, ...styledClasses]);
    const orphans = designClasses.filter((c) => !prod.has(c) && !(c in exempt)).sort();
    const design = new Set(designClasses);
    const dead = Object.keys(exempt)
        .filter((c) => design.has(c) && prod.has(c))
        .sort();
    const skipped = Object.keys(exempt)
        .filter((c) => design.has(c) && !prod.has(c))
        .sort()
        .map((c) => ({ cls: c, why: exempt[c] }));
    return { orphans, dead, skipped, judged: designClasses.length - skipped.length };
}

module.exports = { ALLOW_FILE, loadAllow, classesOf, styledClassesOf, checkFreshness };
