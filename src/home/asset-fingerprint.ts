// ============================================================
// 页面产物指纹 · 前端唯一的发版号。
//
// home.html 里 `main.js?v=` 那串是全站手写一次的版本号(scripts/check_cachebust.py 守着它
// 必随产物 bump)。凡是不写在 HTML 里、由 JS 运行时现拼 URL 去取的资源(教程正文 JSON、
// 教程配图),都从这里抠同一个值当自己的 ?v —— 各造一套版本号必然漂,总有一套忘了 bump,
// 而 CDN 只按 URL 缓存:URL 不变,文件换了也永远发旧的(2026-07-26 教程 JSON 真事故)。
// ============================================================

function fingerprint(): string {
    const el = document.querySelector<HTMLScriptElement>('script[src*="/dist/main.js"]');
    const m = el && el.src.match(/[?&]v=([^&]+)/);
    return m ? m[1] : '';
}

// 抠不到指纹(单测页、直开静态文件)就原样返回,不挂一个空的 ?v= 上去污染 URL。
export function withFingerprint(url: string): string {
    const v = fingerprint();
    return v ? `${url}${url.includes('?') ? '&' : '?'}v=${v}` : url;
}
