// 商户采购 · 屏6 单据详情样式(.pur.d 作用域)· 一体化布局(与复核屏同款:整屏一张白卡 + 左票据栏吸顶 + 右信息分段 + 底部操作条吸底)。
// 全引全站令牌(home-01-base :root + :root.dark)· 零硬编码 hex · 暗夜随翻面不反白。
export const PURCHASE_DETAIL_CSS = `
.pur.d .wrap{width:100%;}
/* 顶栏:面板卡 · 返回 + 标题 + 面包屑 */
.pur.d .ph{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:20px 22px;border:1px solid var(--line);border-radius:18px;background:var(--card);box-shadow:var(--sh);margin-bottom:18px;}
.pur.d .ph .phl{display:flex;align-items:flex-start;gap:14px;min-width:0;}
.pur.d .ph .back{width:38px;height:38px;border-radius:11px;border:1px solid var(--line);background:var(--card);color:var(--ink2);display:grid;place-items:center;flex:none;cursor:pointer;font-size:20px;line-height:1;}
.pur.d .ph .back:hover{border-color:var(--accent);background:var(--accent-weak);color:var(--accent-deep);}
.pur.d .ph .t{font-size:23px;font-weight:740;letter-spacing:-.4px;display:flex;align-items:center;flex-wrap:wrap;gap:9px;line-height:1.2;}
.pur.d .ph .crumb{margin-top:7px;color:var(--ink3);font-size:12.5px;} .pur.d .ph .crumb i{color:var(--ink-4);padding:0 6px;font-style:normal;}

.pur.d .badge{display:inline-flex;align-items:center;gap:5px;height:26px;padding:0 10px;border-radius:999px;font-size:11.5px;font-weight:700;white-space:nowrap;}
.pur.d .badge.success{color:var(--green);background:var(--green-weak);}
.pur.d .badge.purple{color:var(--accent-deep);background:var(--accent-weak);}
.pur.d .badge.warning{color:var(--amber);background:var(--amber-weak);}
.pur.d .badge.neutral{color:var(--ink2);background:var(--line2);}
.pur.d .badge.paid{color:var(--green);background:var(--green-weak);}
.pur.d .badge.unpaid,.pur.d .badge.partial{color:var(--amber);background:var(--amber-weak);}
.pur.d .badge.void{color:var(--ink2);background:var(--line2);}

/* 摘要条:4 列 KPI */
.pur.d .summary{display:grid;grid-template-columns:1.25fr .75fr .8fr .8fr;border-radius:16px;background:var(--card);border:1px solid var(--line);box-shadow:var(--sh);overflow:hidden;margin-bottom:18px;}
.pur.d .summary .si{padding:18px 20px;min-width:0;} .pur.d .summary .si+.si{border-left:1px solid var(--line);}
.pur.d .summary .eyebrow{font-size:11.5px;color:var(--ink3);margin-bottom:7px;}
.pur.d .summary .sv{font-size:16px;font-weight:720;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.pur.d .summary .sv.total{color:var(--accent-deep);font-size:23px;letter-spacing:-.4px;}

/* 一体化:整屏一张白卡 · 左 330 票据栏(吸顶)+ 右信息分段(滚动)+ 底部操作条(吸底) */
.pur.d .sheet{display:grid;grid-template-columns:330px minmax(0,1fr);align-items:start;background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:visible;}
.pur.d .preview-pane{position:sticky;top:calc(var(--topbar-h) + 14px);min-width:0;max-height:calc(100vh - var(--topbar-h) - 28px);overflow-y:auto;border-right:1px solid var(--line);border-radius:16px 0 0 16px;display:flex;flex-direction:column;}
.pur.d .form-pane{min-width:0;display:flex;flex-direction:column;}
.pur.d .scroll{padding:0 6px;}
.pur.d .section{border-bottom:1px solid var(--line);} .pur.d .form-pane .section:last-of-type{border-bottom:0;}
.pur.d .sheet .card{border:0;border-radius:0;box-shadow:none;background:transparent;}
.pur.d .preview-pane .card + .card{border-top:1px solid var(--line);}
.pur.d .card .hd{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:56px;padding:0 18px;}
.pur.d .card .hd .ct{display:flex;align-items:center;gap:10px;font-weight:780;font-size:15px;}
.pur.d .card .hd .ico{width:32px;height:32px;display:grid;place-items:center;border-radius:10px;background:var(--accent-weak);color:var(--accent-deep);flex:none;}
.pur.d .card .hd .muted{color:var(--ink3);font-weight:500;font-size:12px;}
.pur.d .card .bd{padding:14px 18px;}
.pur.d .editfoot{position:sticky;bottom:0;z-index:7;border-top:1px solid var(--line);background:var(--card);border-radius:0 0 16px 0;display:flex;gap:10px;justify-content:flex-end;align-items:center;padding:14px 22px;}

/* 基本信息字段网格 */
.pur.d .meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 34px;padding:4px 18px 16px;}
.pur.d .meta .f{display:grid;grid-template-columns:118px minmax(0,1fr);gap:12px;padding:13px 0;border-bottom:1px dashed var(--line2);}
.pur.d .meta .f:nth-last-child(-n+2){border-bottom:0;}
.pur.d .meta .f .l{color:var(--ink3);font-size:12.5px;} .pur.d .meta .f .v{font-size:13.5px;font-weight:650;word-break:break-word;}

/* 明细表 */
.pur.d .table-wrap{overflow-x:auto;}
.pur.d table{width:100%;border-collapse:collapse;}
.pur.d th,.pur.d td{padding:13px 14px;text-align:left;border-bottom:1px solid var(--line2);}
.pur.d th{color:var(--ink3);font-size:11.5px;font-weight:700;background:var(--bg);}
.pur.d td{font-size:13.5px;vertical-align:top;} .pur.d tbody tr:last-child td{border-bottom:0;}
.pur.d td.num,.pur.d th.num{text-align:right;font-variant-numeric:tabular-nums;}
.pur.d .pname{font-weight:700;}
.pur.d .pill{display:inline-flex;align-items:center;margin-left:7px;padding:2px 7px;border-radius:6px;font-size:10.5px;font-weight:700;}
.pur.d .pill.ok{background:var(--green-weak);color:var(--green);} .pur.d .pill.warn{background:var(--amber-weak);color:var(--amber);cursor:pointer;}

/* 金额/付款 金额行 */
.pur.d .mlist{padding:4px 18px 16px;}
.pur.d .mrow{display:flex;justify-content:space-between;gap:20px;padding:11px 0;color:var(--ink2);font-size:13.5px;}
.pur.d .mrow strong{color:var(--ink);font-variant-numeric:tabular-nums;font-weight:700;}
.pur.d .mrow.tax strong{color:var(--green);} .pur.d .mrow.unpaid strong{color:var(--amber);}
.pur.d .mrow.total{margin-top:5px;padding-top:15px;border-top:1px dashed var(--line);font-size:15px;font-weight:800;color:var(--ink);}
.pur.d .mrow.total strong{color:var(--accent-deep);font-size:20px;}

/* 票图 */
.pur.d .img{position:relative;overflow:hidden;border-radius:13px;background:var(--line2);aspect-ratio:4/4.4;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;color:var(--ink3);cursor:zoom-in;}
.pur.d .img img{width:100%;height:100%;object-fit:cover;display:block;}
.pur.d .view-btn{width:100%;justify-content:center;margin-top:11px;}
.pur-lightbox{position:fixed;inset:0;background:rgba(17,24,39,.9);z-index:1100;display:flex;align-items:center;justify-content:center;padding:8px;cursor:zoom-out;}
.pur-lightbox img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;border-radius:6px;}

/* 处理记录(诚实推导 · 无假人名/时间)*/
.pur.d .timeline{padding:14px 18px;}
.pur.d .step{display:grid;grid-template-columns:18px 1fr;gap:12px;position:relative;padding-bottom:18px;}
.pur.d .step:last-child{padding-bottom:0;}
.pur.d .step:not(:last-child)::after{content:"";position:absolute;left:8px;top:18px;bottom:0;width:2px;background:var(--line);}
.pur.d .dot{width:16px;height:16px;border-radius:50%;background:var(--ink-4);border:4px solid var(--line2);z-index:1;}
.pur.d .dot.ok{background:var(--green);border-color:var(--green-weak);} .pur.d .dot.active{background:var(--accent);border-color:var(--accent-weak);} .pur.d .dot.void{background:var(--red);border-color:var(--red-weak);}
.pur.d .step .st{font-weight:720;font-size:13.5px;} .pur.d .step .sm{margin-top:4px;color:var(--ink3);font-size:12px;}
.pur.d .note{margin:4px 18px 16px;padding:13px 14px;border-radius:12px;background:var(--bg);border:1px solid var(--line);color:var(--ink2);font-size:12.5px;line-height:1.65;}
.pur.d .vch{display:flex;flex-direction:column;gap:8px;padding:14px 18px;} .pur.d .vch .btn{width:100%;justify-content:flex-start;}
.pur.d .stocknote{margin:0 18px 16px;font-size:12px;color:var(--ink2);background:var(--green-weak);border-radius:9px;padding:9px 11px;}
.pur.d.voided{opacity:.62;}

@media(max-width:1024px){
  .pur.d .sheet{display:block;border:0;border-radius:0;box-shadow:none;overflow:visible;}
  .pur.d .preview-pane{position:static;max-height:none;overflow:visible;border-right:0;border-bottom:1px solid var(--line);border-radius:0;}
  .pur.d .editfoot{position:fixed;left:0;right:0;bottom:0;z-index:30;border-radius:0;padding:12px;}
  .pur.d .scroll{padding:0;}
  .pur.d .summary{grid-template-columns:repeat(2,1fr);}
  .pur.d .summary .si:nth-child(3){border-left:0;border-top:1px solid var(--line);} .pur.d .summary .si:nth-child(4){border-top:1px solid var(--line);}
}
@media(max-width:600px){
  .pur.d .ph{flex-direction:column;align-items:flex-start;padding:16px;}
  .pur.d .summary{grid-template-columns:1fr;} .pur.d .summary .si+.si{border-left:0;border-top:1px solid var(--line);}
  .pur.d .meta{grid-template-columns:1fr;} .pur.d .meta .f:nth-last-child(-n+2){border-bottom:1px dashed var(--line2);} .pur.d .meta .f:last-child{border-bottom:0;}
}
`;
