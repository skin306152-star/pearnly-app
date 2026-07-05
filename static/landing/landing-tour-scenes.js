// 着陆页产品导览 · 拟真手机 + LINE 聊天剧情播放器 · window.PearnlyTourScenes
// 每屏一台手机,进屏时按时间轴播对应剧情(OCR 扫描/汇总柱生长/对账打勾),切屏即清定时器。
(function () {
    const PHONE_HTML = `
<div class="phone">
  <span class="sidebtn sb-l1"></span><span class="sidebtn sb-l2"></span><span class="sidebtn sb-l3"></span><span class="sidebtn sb-r1"></span>
  <div class="scr">
    <div class="sbar">
      <span class="tm">9:41</span>
      <span class="isl"></span>
      <span class="sic">
        <span class="sig"><i></i><i></i><i></i><i></i></span>
        <span class="wifi"></span>
        <span class="bat"></span>
      </span>
    </div>
    <div class="chat-head">
      <span class="back">‹</span>
      <div class="av">P</div><span class="nm">Pearnly</span><span class="ai">AI</span>
      <span class="hic">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.5-3.5"></path></svg>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="4" y="3" width="16" height="18" rx="2"></rect><path d="M8 8h8M8 12h8M8 16h5"></path></svg>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"></path></svg>
      </span>
    </div>
    <div class="chat-body"></div>
    <div class="chat-foot">
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"></path></svg>
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z"></path><circle cx="12" cy="13" r="3.2"></circle></svg>
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="4" width="18" height="16" rx="2"></rect><circle cx="9" cy="10" r="1.8"></circle><path d="M3 17l5-4 4 3 5-5 4 4"></path></svg>
      <span class="aa">Aa</span>
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"></circle><path d="M8.5 14.5c.9 1.2 2.1 1.8 3.5 1.8s2.6-.6 3.5-1.8"></path><circle cx="9" cy="10" r=".6" fill="currentColor"></circle><circle cx="15" cy="10" r=".6" fill="currentColor"></circle></svg>
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"></rect><path d="M5.5 11.5a6.5 6.5 0 0013 0M12 18v3"></path></svg>
    </div>
    <div class="homebar"></div>
  </div>
</div>`;

    function el(html) {
        const t = document.createElement('template');
        t.innerHTML = html.trim();
        return t.content.firstChild;
    }
    function push(body, node) {
        body.appendChild(node);
        body.scrollTop = body.scrollHeight;
        return node;
    }
    function meta(c, time) {
        return `<div class="meta"><span>${c.read}</span><span>${time}</span></div>`;
    }
    function dateChip(c) {
        return el(`<div class="datechip">${c.today}</div>`);
    }
    function userText(c, txt, time) {
        return el(`<div class="msg user">${meta(c, time)}<div class="bub">${txt}</div></div>`);
    }
    function userVoice(c, time) {
        return el(
            `<div class="msg user">${meta(c, time)}<div class="bub voice"><span class="pl"></span><span class="wave"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span><span class="tm">0:03</span></div></div>`
        );
    }
    function receiptEl() {
        return el(`<div class="rcpt">
  <div class="rlogo"><b>SABAI MART</b></div>
  <div class="rl c">TAX INVOICE (ABB)</div>
  <div class="rl c">POS#03 · 05/07/26 09:41</div>
  <div class="rsep"></div>
  <div class="rl"><span>PAPER A4 x1</span><span>95.00</span></div>
  <div class="rl"><span>PEN BLUE x2</span><span>40.00</span></div>
  <div class="rl"><span>TAPE 18mm x1</span><span>37.90</span></div>
  <div class="rl"><span>VAT 7%</span><span>12.10</span></div>
  <div class="rl tt"><span>TOTAL</span><span>185.00</span></div>
  <div class="rbar"></div>
</div>`);
    }
    function userReceipt(c, time) {
        const m = el(`<div class="msg user">${meta(c, time)}</div>`);
        m.appendChild(receiptEl());
        return m;
    }
    function typing() {
        return el(
            `<div class="msg bot typing"><div class="bav">P</div><div class="bub"><span class="d"></span><span class="d"></span><span class="d"></span></div></div>`
        );
    }
    function botText(txt) {
        return el(
            `<div class="msg bot"><div class="bav">P</div><div class="bub">${txt.replace(/\n/g, '<br>')}</div></div>`
        );
    }
    function entryCard(c) {
        return el(`<div class="msg bot"><div class="bav">P</div><div class="card">
  <div class="ttl"><span class="ck">✓</span>${c.booked}</div>
  <div class="bd">
    <div class="row"><span>${c.rStore}</span><b>${c.vStore}</b></div>
    <div class="row"><span>${c.rDate}</span><b>${c.vDate}</b></div>
    <div class="row"><span>${c.rCat}</span><b>${c.vCat}</b></div>
    <div class="row"><span>${c.rVat}</span><b>฿12.10</b></div>
    <div class="row tot"><span>${c.rTot}</span><b>฿185.00</b></div>
    <div class="cbtns"><span class="v">${c.btnEdit}</span><span class="e">${c.btnCancel}</span></div>
  </div></div></div>`);
    }
    function summaryCard(c) {
        return el(`<div class="msg bot"><div class="bav">P</div><div class="card">
  <div class="bd" style="padding-top:12px">
    <div class="bar"><span>${c.b1}</span><i data-w="92%" style="background:#7655F6"></i><em>32,400</em></div>
    <div class="bar"><span>${c.b2}</span><i data-w="52%" style="background:#3B82F6"></i><em>15,800</em></div>
    <div class="bar"><span>${c.b3}</span><i data-w="33%" style="background:#06C755"></i><em>10,040</em></div>
  </div></div></div>`);
    }
    function reconCard(c) {
        return el(`<div class="msg bot"><div class="bav">P</div><div class="card">
  <div class="strip">${c.reconT}</div>
  <div class="bd">
    <div class="rrow"><span class="st">✓</span><span class="rn">${c.r1}</span><span class="ra">฿12,400</span></div>
    <div class="rrow"><span class="st">✓</span><span class="rn">${c.r2}</span><span class="ra">฿3,150</span></div>
    <div class="rrow" data-warn><span class="st">!</span><span class="rn">${c.r3}</span><span class="ra">฿2,890</span></div>
    <div class="rrow"><span class="st">✓</span><span class="rn">${c.r4}</span><span class="ra">฿18,600</span></div>
    <div class="warnnote">${c.mismatch}</div>
  </div></div></div>`);
    }

    function growBars(card) {
        card.querySelectorAll('.bar i').forEach((b) => {
            b.style.width = b.dataset.w;
        });
    }
    function playRecon(card, t) {
        card.querySelectorAll('.rrow').forEach((r, i) => {
            t(
                () => {
                    r.classList.add(r.hasAttribute('data-warn') ? 'warn' : 'ok');
                    if (r.hasAttribute('data-warn'))
                        card.querySelector('.warnnote').classList.add('on');
                },
                500 + i * 550
            );
        });
    }

    let timers = [];
    let chatBodies = [];
    function T(fn, ms) {
        timers.push(setTimeout(fn, ms));
    }
    function stop() {
        timers.forEach(clearTimeout);
        timers = [];
    }

    function mount(slots) {
        slots.forEach((slot) => {
            slot.innerHTML = PHONE_HTML;
        });
        chatBodies = [...slots].map((s) => s.querySelector('.chat-body'));
    }

    function play(i, dict) {
        stop();
        const body = chatBodies[i];
        if (!body) return;
        chatBodies.forEach((b) => {
            b.innerHTML = '';
        });
        const c = dict.chat;
        let tp;

        if (i === 0) {
            const loop = () => {
                body.innerHTML = '';
                push(body, dateChip(c));
                T(() => {
                    const r = push(body, userReceipt(c, '09:41'));
                    r.querySelector('.rcpt').classList.add('scan');
                }, 500);
                T(() => {
                    tp = push(body, typing());
                }, 1900);
                T(() => {
                    tp.remove();
                    const rc = body.querySelector('.rcpt');
                    if (rc) rc.classList.remove('scan');
                    push(body, entryCard(c));
                }, 3200);
                T(() => {
                    push(body, userText(c, c.askText, '09:43'));
                }, 4900);
                T(() => {
                    tp = push(body, typing());
                }, 5600);
                T(() => {
                    tp.remove();
                    push(body, botText(c.sumBub));
                    const s = push(body, summaryCard(c));
                    requestAnimationFrame(() => requestAnimationFrame(() => growBars(s)));
                }, 6900);
                T(loop, 10800);
            };
            loop();
        }
        if (i === 1) {
            push(body, dateChip(c));
            T(() => {
                const r = push(body, userReceipt(c, '09:41'));
                T(() => r.querySelector('.rcpt').classList.add('scan'), 400);
            }, 600);
            T(() => {
                tp = push(body, typing());
            }, 2400);
            T(() => {
                tp.remove();
                body.querySelector('.rcpt').classList.remove('scan');
                push(body, entryCard(c));
            }, 4200);
        }
        if (i === 2) {
            push(body, dateChip(c));
            T(() => {
                push(body, userVoice(c, '09:42'));
            }, 600);
            T(() => {
                push(body, userText(c, c.askText, '09:43'));
            }, 1500);
            T(() => {
                tp = push(body, typing());
            }, 2200);
            T(() => {
                tp.remove();
                push(body, botText(c.sumBub));
                const s = push(body, summaryCard(c));
                requestAnimationFrame(() => requestAnimationFrame(() => growBars(s)));
            }, 3600);
        }
        if (i === 3) {
            push(body, dateChip(c));
            T(() => {
                push(body, userText(c, c.erpCmd, '09:45'));
            }, 600);
            T(() => {
                tp = push(body, typing());
            }, 1300);
            T(() => {
                tp.remove();
                const r = push(body, reconCard(c));
                playRecon(r, T);
            }, 2600);
            T(() => {
                tp = push(body, typing());
            }, 5600);
            T(() => {
                tp.remove();
                push(body, botText(c.erpOk));
            }, 6600);
        }
    }

    window.PearnlyTourScenes = { mount, play, stop };
})();
