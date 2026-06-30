// Pearnly E2E · 续步记忆小工具 · UI-UNIFY
// 各续步 spec 共用:种入/读回 localStorage 里的步号记忆。
// 键前缀镜像 src/home/step-resume.ts 的 PREFIX(测试侧独立副本 · 改前缀两边同步)。
/* global window */

const PREFIX = 'pearnly_step_';

function memoKey(flow) {
    return PREFIX + flow;
}

async function seedStepMemo(page, flow, memo) {
    await page.evaluate(
        ([k, v]) => window.localStorage.setItem(k, v),
        [memoKey(flow), JSON.stringify(memo)]
    );
}

async function readStepMemo(page, flow) {
    return page.evaluate(([k]) => window.localStorage.getItem(k), [memoKey(flow)]);
}

module.exports = { memoKey, seedStepMemo, readStepMemo };
