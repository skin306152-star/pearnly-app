// 用户引导闭环 · 向导壳的样式 + 静态模板 + 图标(从 onboarding-flow 抽出控行数)。
// 作用域 .onb · 全用全局令牌 var(--*) · 主色走 var(--accent)(对齐 acct 模块已上线范式)。
// 交互基准:桌面 Pearnly_用户引导闭环_UI预览/01-交互原型.html(stepper / 业态卡 / 绿卡 / 完成清单)。

// lucide 风线性图标(禁 emoji 当图标 · 铁律 UI)。
const ICON: Record<string, string> = {
    check: '<path d="M20 6 9 17l-5-5"/>',
    chev: '<path d="m9 18 6-6-6-6"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    edit: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/>',
    user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
};

export function onbIcon(name: string, cls = ''): string {
    return (
        `<svg class="onb-i ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
        `stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">` +
        (ICON[name] || '') +
        '</svg>'
    );
}

// 业态卡图标(stroke-width 2 · 复用 onboarding-business 的 path)。
export function onbBizIcon(path: string): string {
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' +
        path +
        '"/></svg>'
    );
}

export const ONB_CSS = `
.onb-root{position:fixed;inset:0;z-index:1300;background:var(--bg);overflow:auto;color:var(--ink);
  font-size:13.5px;-webkit-font-smoothing:antialiased;display:flex;flex-direction:column;}
.onb-root *{box-sizing:border-box;}
.onb-top{height:60px;display:flex;align-items:center;padding:0 24px;gap:10px;flex:none;}
.onb-brand{display:flex;align-items:center;gap:9px;font-weight:800;font-size:15px;letter-spacing:-.2px;}
.onb-brand .onb-logo{width:26px;height:26px;border-radius:8px;object-fit:cover;flex:none;}
:root.dark .onb-brand .onb-logo{background:#fff;padding:2px;}
.onb-skip{margin-left:auto;background:none;border:0;color:var(--ink3);font-size:12.5px;cursor:pointer;
  display:inline-flex;align-items:center;gap:5px;}
.onb-skip:hover{color:var(--accent);}
.onb-body{flex:1;display:flex;align-items:flex-start;justify-content:center;padding:8px 20px 60px;}
.onb-pane{width:100%;max-width:min(600px,100%);}
.onb-i{width:18px;height:18px;flex:none;}
.onb-steps{display:flex;align-items:center;margin:6px auto 30px;max-width:min(440px,100%);}
.onb-step{display:flex;align-items:center;}
.onb-step .dot{width:26px;height:26px;border-radius:50%;background:var(--card);border:2px solid var(--line);
  color:var(--ink3);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex:none;}
.onb-step.on .dot{border-color:var(--accent);color:var(--accent);}
.onb-step.done .dot{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);}
.onb-step .lb{font-size:11px;color:var(--ink3);margin-left:7px;white-space:nowrap;}
.onb-step.on .lb{color:var(--accent);font-weight:650;}
.onb-bar{height:2px;flex:1;background:var(--line);margin:0 4px;border-radius:2px;min-width:24px;}
.onb-bar.done{background:var(--accent);}
.onb-h1{font-size:23px;font-weight:740;letter-spacing:-.4px;text-align:center;}
.onb-sub{color:var(--ink2);font-size:13.5px;text-align:center;margin-top:8px;line-height:1.65;}
.onb-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-top:26px;}
.onb-biz{display:flex;gap:13px;align-items:flex-start;border:1.5px solid var(--line);border-radius:14px;
  padding:15px 16px;background:var(--card);transition:.12s;text-align:left;cursor:pointer;width:100%;}
.onb-biz:hover{border-color:var(--accent);}
.onb-biz.on{border-color:var(--accent);background:var(--accent-weak);}
.onb-biz .ic{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;
  flex:none;background:var(--bg);color:var(--accent);}
.onb-biz .ic svg{width:21px;height:21px;}
.onb-biz.on .ic{background:var(--card);}
.onb-biz .t{font-weight:680;font-size:14px;}
.onb-biz .d{color:var(--ink2);font-size:12px;margin-top:3px;line-height:1.5;}
.onb-biz .chk{margin-left:auto;width:18px;height:18px;border-radius:50%;border:1.5px solid var(--line);flex:none;position:relative;}
.onb-biz.on .chk{background:var(--accent);border-color:var(--accent);}
.onb-biz.on .chk::after{content:"";position:absolute;left:5px;top:2px;width:5px;height:8px;
  border:solid var(--accent-ink);border-width:0 2px 2px 0;transform:rotate(45deg);}
.onb-fgrid{margin-top:24px;display:flex;flex-direction:column;gap:16px;}
.onb-fld label{display:block;font-size:12.5px;color:var(--ink);font-weight:600;margin-bottom:7px;}
.onb-fld label .opt{color:var(--ink3);font-weight:400;font-size:11.5px;margin-left:6px;}
.onb-inp{height:44px;border:1.5px solid var(--line);border-radius:11px;padding:0 14px;font-size:14px;
  width:100%;background:var(--card);color:var(--ink);transition:.12s;}
.onb-inp:focus{outline:none;border-color:var(--accent);}
.onb-inp.tnum{font-variant-numeric:tabular-nums;letter-spacing:.3px;}
.onb-pulled{margin-top:9px;display:flex;gap:10px;align-items:flex-start;background:var(--green-weak);
  border:1px solid var(--green-weak);border-radius:11px;padding:11px 13px;}
.onb-pulled .ic{color:var(--green);flex:none;margin-top:1px;}
.onb-pulled .nm{font-weight:650;font-size:13.5px;}
.onb-pulled .ad{color:var(--ink2);font-size:12px;margin-top:2px;line-height:1.5;}
.onb-pulled .re{margin-left:auto;background:none;border:0;color:var(--ink3);font-size:12px;cursor:pointer;}
.onb-seg{display:inline-flex;background:var(--bg);border:1px solid var(--line);border-radius:11px;padding:4px;margin:24px auto 0;}
.onb-seg button{padding:8px 20px;border-radius:8px;font-size:13px;border:0;background:none;color:var(--ink2);font-weight:600;cursor:pointer;}
.onb-seg button.on{background:var(--card);color:var(--accent);box-shadow:var(--sh);}
.onb-switch{display:flex;align-items:center;gap:12px;border:1px solid var(--line);border-radius:12px;
  padding:13px 15px;background:var(--card);margin-top:16px;cursor:pointer;}
.onb-sw{width:40px;height:23px;border-radius:12px;background:var(--ink-4);position:relative;flex:none;transition:.15s;}
.onb-sw::after{content:"";width:19px;height:19px;border-radius:50%;background:var(--card);position:absolute;top:2px;left:2px;transition:.15s;}
.onb-sw.on{background:var(--accent);}
.onb-sw.on::after{left:19px;}
.onb-note{display:flex;gap:11px;align-items:flex-start;background:var(--accent-weak);border-radius:13px;
  padding:14px 16px;margin-top:22px;font-size:12.5px;line-height:1.7;color:var(--ink);}
.onb-note .ic{color:var(--accent);flex:none;margin-top:1px;}
.onb-note b{color:var(--accent);}
.onb-acts{display:flex;align-items:center;margin-top:30px;gap:10px;}
.onb-acts .grp{display:flex;gap:10px;align-items:center;margin-left:auto;}
.onb-lnk{background:none;border:0;color:var(--ink2);font-size:13px;cursor:pointer;display:inline-flex;align-items:center;gap:5px;}
.onb-lnk:hover{color:var(--accent);}
.onb-btn{height:40px;padding:0 20px;border:1px solid var(--line);border-radius:10px;background:var(--card);
  color:var(--ink);font-size:13.5px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:7px;}
.onb-btn:hover{border-color:var(--ink3);}
.onb-btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.onb-btn.pri:hover{background:var(--accent-deep);}
.onb-btn:disabled{opacity:.45;cursor:not-allowed;}
.onb-done-ic{width:56px;height:56px;border-radius:18px;background:var(--green-weak);color:var(--green);
  display:flex;align-items:center;justify-content:center;margin:0 auto 16px;}
.onb-done-ic svg{width:28px;height:28px;}
.onb-checklist{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);
  margin-top:6px;text-align:left;overflow:hidden;}
.onb-cli{display:flex;align-items:center;gap:12px;padding:13px 16px;border-bottom:1px solid var(--line2);}
.onb-cli:last-child{border-bottom:0;}
.onb-cli .ck{width:22px;height:22px;border-radius:50%;flex:none;display:flex;align-items:center;justify-content:center;}
.onb-cli .ck.done{background:var(--green-weak);color:var(--green);}
.onb-cli .ck.todo{border:1.5px solid var(--line);}
.onb-cli .ct{font-weight:600;font-size:13.5px;}
.onb-cli .cd{color:var(--ink3);font-size:11.5px;margin-top:1px;}
@media(max-width:780px){.onb-grid{grid-template-columns:1fr;}.onb-body{padding:8px 14px 60px;}}
`;
