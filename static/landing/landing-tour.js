// 着陆页产品导览:登录页=第 1 页 + 5 屏卖点横向滑动(循环) · Zihao 2026-07-06 拍板版式
// 依赖 landing-tour-i18n.js(文案)+ landing-tour-scenes.js(手机剧情);语言跟登录页切换器
// (监听 <html lang>,landing-i18n.js 的 applyLanguage 会写它)。滑动=箭头/圆点/键盘/横划。
(function () {
    const LINE_URL = 'https://line.me/R/ti/p/@pearnly';
    const QR_SRC =
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALoAAAC6CAIAAACWbMCmAAAD50lEQVR4nO3dwW3cMBAFUDtILTmpr9SUvnRKM04BOoSfniG5i/eOxlqS4Q9qBySHn19fXx8w5sfg50BcyBhdCIgLAXEh8PP5o+vX74997r9//vuZkSccuc7IlaueZ8TzXqf9L4wuBMSFgLgQEBcC4sL3KqOqKmPEyDf/uWpl7u5zV76nKpqqe1UZeWajCwFxISAuBMSFgLhQXRk9zc1l9NUdc5+Zmw+6B36r78oj1xkxdy+jCwFxISAuBMSFgLjQXxntNVcHPc1VT9fWFW57GV0IiAsBcSEgLgTEhfeqjOYqkb41eHtX0+1ldCEgLgTEhYC4EBAX+iujld/q+3ogVM0HXVOr+/p2OfUxuhAQFwLiQkBcCIgL1ZXR3vVjVTt9Vl7nmvrM+f8LowsBcSEgLgTEhYC4EPh8xfOMVq6Uq6qD9v4VVYwuBMSFgLgQEBcC4kL1eUYr5036ziHqmzPaO9ezsi4zuhAQFwLiQkBcCIgL1XNGfSeZzulbq9bXie7euluqqlYyuhAQFwLiQkBcCIgLOzowzJ3ZOnLlEXvroHthPTXXyaHqeYwuBMSFgLgQEBcC4sL35oz6Tg5d+R2+ao6mqiP3VfS3r5x3ezK6EBAXAuJCQFwIiAvVc0anVRlzd597nlfsMndZTccJvIwIiAsBcSEgLpzRtbtq3mRvzVXlbpsdW/k8RhcC4kJAXAiICwFxob8Dw96dNX17kVbWStfCXVdVlaPRhYC4EBAXAuJCQFyo7to98pm9fefm7v6Ke6OeVt7d6EJAXAiICwFxISAunNq1e8TKXUVzrq0d9lZWc+aM+BYvIwLiQkBcCIgL/R0YVq6dq9K3X2nOynqzqlYyuhAQFwLiQkBcCIgL1V279646W9kB+7SzVuf09RI0uhAQF8SFHkYXAuLCGavpTltRNuc9qqe76O5GFwLiQkBcCIgLAXFhx5zRiNNOL6q68mk9uvs67BldCIgLAXEhIC4ExIXqOaO9Vp5ntHcv0r21R/fI8xhdCIgLAXEhIC4ExIX+rt19nt/GV54Gu/I8oxGn7fkyuhAQFwLiQkBcCIgL/b3pquxdF1dVZTz1zdpU0ZuOdl5GBMSFgLgQEBeqK6PTejKcNrMzomrma+5eTzow0M7LiIC4EBAXAuJCf2W00srOCa/YU25ldWl0ISAuBMSFgLgQEBfeqzI6f37qGvitlbuc+v4KowsBcSEgLgTEhYC40F8ZrVzP1ncu0si9Vs5G9e2WGrmy84wo5mVEQFwIiAsBcaG6MtrbrW6uOth7otArVmrmjCjmZURAXAiICwFx4b3OM+IcRhcC4kJAXAiICwFx4WPcPw/9NwE9PaGzAAAAAElFTkSuQmCC';
    const PAGES = 6;

    const IC = {
        spark: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" stroke="url(#ptlgA)" stroke-width="2"/><path d="M19 16.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z" stroke="#F59E0B" stroke-width="1.6"/></svg>',
        camera: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5h3.2L9 6h6l1.8 2.5H20a1 1 0 011 1V18a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5a1 1 0 011-1z" stroke="url(#ptlgA)" stroke-width="2"/><circle cx="12" cy="13.3" r="3.4" stroke="url(#ptlgB)" stroke-width="2"/></svg>',
        mic: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="3" width="6" height="11" rx="3" stroke="url(#ptlgA)" stroke-width="2"/><path d="M5.5 11.5a6.5 6.5 0 0013 0" stroke="url(#ptlgB)" stroke-width="2"/><path d="M12 18v3" stroke="url(#ptlgB)" stroke-width="2"/></svg>',
        sync: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11a8 8 0 00-14.5-3.5M4 13a8 8 0 0014.5 3.5" stroke="url(#ptlgA)" stroke-width="2"/><path d="M5.5 4v3.5H9" stroke="#06C755" stroke-width="2"/><path d="M18.5 20v-3.5H15" stroke="#06C755" stroke-width="2"/></svg>',
        party: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10l7 7-10 3z" stroke="url(#ptlgA)" stroke-width="2" stroke-linejoin="round"/><path d="M13 8.5c1.8-1.8 3.8-2 5.5-.6M11 5.2c.3-1.4 1.3-2.3 2.8-2.4" stroke="#F59E0B" stroke-width="1.8"/><circle cx="18.5" cy="12.5" r="1" fill="#F04FBD" stroke="none"/><circle cx="15.5" cy="4" r="1" fill="#06C755" stroke="none"/><circle cx="20.5" cy="6.5" r="1" fill="#3B82F6" stroke="none"/></svg>',
        check: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="url(#ptlgA)" stroke-width="2"/><path d="M8.2 12.4l2.6 2.6 5-5.4" stroke="#06C755" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        left: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
        right: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7"/></svg>',
    };

    function pts(keys) {
        return keys
            .map((k) => `<div class="pt">${IC.check}<span data-tour-i18n="${k}"></span></div>`)
            .join('');
    }
    function copyScreen(n, icon, pointKeys, extra, flip) {
        return `<section class="ptour-screen${flip ? ' flip' : ''}">
  <div class="copy">
    <div class="fx"><span class="kicker">${icon}<span data-tour-i18n="s${n}k"></span></span></div>
    <h1 class="fx"><span data-tour-i18n="s${n}t1"></span><br><span class="grad" data-tour-i18n="s${n}t2"></span></h1>
    <p class="sub fx" data-tour-i18n="s${n}s"></p>
    <div class="points fx">${pts(pointKeys)}</div>
    ${extra}
  </div>
  <div class="demo"><div class="phone-slot"></div></div>
</section>`;
    }
    const ctaLine = (key) =>
        `<a class="cta line" href="${LINE_URL}" target="_blank" rel="noopener"><span class="lineic">LINE</span><span data-tour-i18n="${key}"></span></a>`;

    const html = `<div class="ptour" id="ptour">
  <div class="ptour-bg"><span class="pglow pg1"></span><span class="pglow pg2"></span><span class="pglow pg3"></span></div>
  <svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
    <linearGradient id="ptlgA" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7655F6"/><stop offset="1" stop-color="#F04FBD"/></linearGradient>
    <linearGradient id="ptlgB" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#06C755"/><stop offset="1" stop-color="#3B82F6"/></linearGradient>
  </defs></svg>
  <div class="ptour-track" id="ptour-track">
    ${copyScreen(1, IC.spark, ['p1a', 'p1b', 'p1c'], `<div class="ctarow fx">${ctaLine('ctaAdd')}</div>`, false)}
    ${copyScreen(2, IC.camera, ['p2a', 'p2b'], '', true)}
    ${copyScreen(3, IC.mic, ['p3a', 'p3b'], '', false)}
    ${copyScreen(4, IC.sync, ['p4a', 'p4b'], '', true)}
    <section class="ptour-screen solo">
      <div class="copy">
        <div class="fx"><span class="kicker">${IC.party}<span data-tour-i18n="s5k"></span></span></div>
        <h1 class="fx"><span data-tour-i18n="s5t1"></span> <span class="grad" data-tour-i18n="s5t2"></span></h1>
        <p class="sub fx" data-tour-i18n="s5s"></p>
        <div class="ctarow fx">
          <div class="ctacol">
            ${ctaLine('ctaAdd')}
            <a class="cta ghost" href="#" id="ptour-signup" data-tour-i18n="ctaSign"></a>
          </div>
          <div class="qrcard">
            <img class="qrimg" alt="LINE QR" src="${QR_SRC}">
            <div class="qrlab" data-tour-i18n="qrT"></div>
            <div><span class="qrline">@pearnly</span></div>
          </div>
        </div>
      </div>
    </section>
  </div>
</div>
<button class="ptour-arrow l" id="ptour-prev" aria-label="previous page">${IC.left}</button>
<button class="ptour-arrow r" id="ptour-next" aria-label="next page">${IC.right}</button>
<div class="ptour-dots" id="ptour-dots"></div>`;

    const host = document.createElement('div');
    host.innerHTML = html;
    while (host.firstChild) document.body.appendChild(host.firstChild);

    const track = document.getElementById('ptour-track');
    const dots = document.getElementById('ptour-dots');
    const screens = document.querySelectorAll('.ptour-screen');
    const scenes = window.PearnlyTourScenes;
    scenes.mount(document.querySelectorAll('.ptour .phone-slot'));

    function curLang() {
        return window.PearnlyCurrentLang || localStorage.getItem('mrpilot_lang') || 'th';
    }
    function dict() {
        const all = window.PearnlyTourI18N;
        return all[curLang()] || all.th;
    }
    function applyTexts() {
        const d = dict();
        document.querySelectorAll('[data-tour-i18n]').forEach((n) => {
            const v = d[n.dataset.tourI18n];
            if (v) n.textContent = v;
        });
    }

    let cur = 0;
    let busy = false;
    for (let i = 0; i < PAGES; i += 1) {
        const b = document.createElement('button');
        b.setAttribute('aria-label', `page ${i + 1}`);
        b.onclick = () => go(i);
        dots.appendChild(b);
    }

    const railX = (i) => (1 - i) * 20;
    const authRoot = () => document.getElementById('pearnly-auth-root');
    // 对齐 landing-tour.css 的 .ptour-track / #pearnly-auth-root 过渡(0.72s),收尾留 40ms 余量
    const SLIDE_MS = 720;
    function move(el, transform, instant) {
        if (!el) return;
        if (instant) el.style.transition = 'none';
        el.style.transform = transform;
        if (instant) {
            void el.offsetWidth;
            el.style.transition = '';
        }
    }
    // 页 i 的规范停靠位(轨道 + 登录页);相邻切换/圆点跳转/环绕收尾/初始化共用
    function settle(i, instant) {
        move(track, `translateX(${railX(i)}%)`, instant);
        move(authRoot(), i === 0 ? 'translateX(0)' : 'translateX(-100vw)', instant);
    }
    function paint(i) {
        document.documentElement.classList.toggle('ptour-on', i > 0);
        dots.querySelectorAll('button').forEach((b, j) => b.classList.toggle('on', j === i));
        screens.forEach((s, j) => s.classList.toggle('active', j === i - 1));
        if (i > 0) scenes.play(i - 1, dict());
        else scenes.stop();
    }

    // 相邻切换与圆点跳转走绝对定位。仅首尾环绕(末屏→登录页 / 登录页→末屏)需先把登录页与
    // 卖点轨道预置到屏外再同向滑入 —— 否则 translateX 从 -80% 直接跳回 +20% 会反向甩一整屏。
    function wrap(forward) {
        busy = true;
        const target = forward ? 0 : PAGES - 1;
        if (forward) {
            move(authRoot(), 'translateX(100vw)', true);
            requestAnimationFrame(() => {
                move(track, 'translateX(-100%)');
                move(authRoot(), 'translateX(0)');
            });
        } else {
            move(track, 'translateX(-100%)', true);
            requestAnimationFrame(() => {
                move(track, `translateX(${railX(target)}%)`);
                move(authRoot(), 'translateX(100vw)');
            });
        }
        cur = target;
        paint(target);
        setTimeout(() => {
            settle(target, true);
            busy = false;
        }, SLIDE_MS + 40);
    }
    function go(i) {
        if (busy) return;
        const target = ((i % PAGES) + PAGES) % PAGES;
        if (target === cur) return;
        if (cur === PAGES - 1 && target === 0) return wrap(true);
        if (cur === 0 && target === PAGES - 1) return wrap(false);
        cur = target;
        settle(target);
        paint(target);
    }

    document.getElementById('ptour-prev').onclick = () => go(cur - 1);
    document.getElementById('ptour-next').onclick = () => go(cur + 1);
    document.getElementById('ptour-signup').onclick = (e) => {
        e.preventDefault();
        go(0);
    };
    addEventListener('keydown', (e) => {
        const t = e.target;
        if (t && (t.matches('input, textarea, select') || t.isContentEditable)) return;
        if (e.key === 'ArrowRight') go(cur + 1);
        if (e.key === 'ArrowLeft') go(cur - 1);
    });
    let sx = null;
    let sy = null;
    addEventListener('pointerdown', (e) => {
        if (e.target.closest('input, textarea, select, button, a, label, [contenteditable]')) {
            sx = null;
            return;
        }
        sx = e.clientX;
        sy = e.clientY;
    });
    addEventListener('pointerup', (e) => {
        if (sx === null) return;
        const dx = e.clientX - sx;
        const dy = e.clientY - sy;
        if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) go(cur + (dx < 0 ? 1 : -1));
        sx = null;
    });

    // 登录页语言切换器写 <html lang> → 导览文案跟着换,当前屏剧情重播换语言台词
    new MutationObserver(() => {
        applyTexts();
        if (cur > 0) scenes.play(cur - 1, dict());
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

    applyTexts();
    settle(0, true);
    paint(0);
})();
