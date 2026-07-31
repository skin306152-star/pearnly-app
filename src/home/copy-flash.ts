// 「复制 → 按钮闪一下『已复制』→ 还原原文」· /home 这一份。
//
// 与 static/shared/copy-flash.js 是同一套语义的两份实现,不是漏抽的重复:/home 走 Vite 的
// ESM/TS 构建图,/ai 与 /dms 走 scripts/build-home-js.mjs 的 esbuild 拼接(浏览器全局,
// 无模块解析),两棵树之间没有共享的 import 图。硬接需要让 src/** 反向 import static/**,
// 那会把一个 root.CopyFlash 全局塞进 /home 的模块世界,比多这 20 行更难维护。
// 行为契约由 tests/unit/test_copy_flash.py 一并钉死,两份一起测,漂了就红。
//
// 两个坑各自都真出过事:
//   ① 原文在点击时才抓 —— 1.5 秒内连点第二次抓到的已经是「已复制」,还原就还原成
//      「已复制」,按钮再也变不回来。原文只在第一次闪时记一次,连点只顺延计时器。
//   ② 非安全上下文(http 访问 + 非 localhost)下 navigator.clipboard 整个不存在。原先
//      `if (!navigator.clipboard) return;` 直接吞掉,点了什么都不发生,用户只会再点一次。
//      现在照样闪 —— 闪的是「点到了」,不谎称写成功。

const HOLD_MS = 1500;
// 状态挂在按钮元素上,不进模块级 Map:按钮被重渲染换掉时状态跟着一起没,不留悬挂条目。
const PREV = '_copyFlashPrev';
const TIMER = '_copyFlashTimer';

type FlashBtn = HTMLElement & { [PREV]?: string | null; [TIMER]?: number | null };

export function flash(btn: HTMLElement | null, doneLabel: string): void {
    if (!btn) return;
    const el = btn as FlashBtn;
    if (el[TIMER]) window.clearTimeout(el[TIMER]);
    else el[PREV] = el.textContent;
    el.textContent = doneLabel;
    el[TIMER] = window.setTimeout(() => {
        el.textContent = el[PREV] ?? '';
        el[TIMER] = null;
    }, HOLD_MS);
}

export function copy(btn: HTMLElement | null, text: string, doneLabel: string): void {
    const done = () => flash(btn, doneLabel);
    try {
        navigator.clipboard.writeText(String(text ?? '')).then(done, done);
    } catch {
        done();
    }
}
