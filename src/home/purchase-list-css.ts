// 商户采购 · 列表页样式(.pur.pl 作用域)· 从 purchase-list 抽出保 <500。
// 全引全站令牌(home-01-base :root + :root.dark)· 零硬编码 hex · 暗夜随翻面物理上不反白。
// 勾选对勾 stroke 用 var(--accent-ink)(暗夜下 accent 是浅紫 · 对勾须深色)· 不写死 #fff。
export const PURCHASE_LIST_CSS = `
.pur.pl .ph{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;}
.pur.pl .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.pur.pl .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.pur.pl .band{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;padding:20px 22px;border-bottom:1px solid var(--line2);flex-wrap:wrap;}
.pur.pl .star{display:flex;align-items:flex-end;gap:20px;flex-wrap:wrap;}
.pur.pl .star .big{font-size:30px;font-weight:740;letter-spacing:-1px;line-height:1;}
.pur.pl .star .big small{display:block;font-size:12.5px;color:var(--ink3);font-weight:600;margin-top:5px;letter-spacing:0;}
.pur.pl .star .ctx{display:flex;gap:16px;padding-bottom:3px;}
.pur.pl .star .ctx>div{font-size:12px;color:var(--ink2);}
.pur.pl .star .ctx b{display:block;color:var(--ink);font-size:15px;font-weight:700;margin-top:2px;}
.pur.pl .star .ctx b.g{color:var(--green);}
.pur.pl .acts{display:flex;gap:9px;}
.pur.pl .btn{border-radius:11px;}
.pur.pl .btn.primary{font-weight:650;}
.pur.pl .alert{display:flex;align-items:center;gap:9px;padding:11px 22px;background:var(--amber-weak);border-bottom:1px solid var(--line2);font-size:13px;color:var(--amber);cursor:pointer;}
.pur.pl .alert .pip{width:7px;height:7px;border-radius:50%;background:var(--amber);flex:0 0 7px;}
.pur.pl .alert b{font-weight:700;color:var(--amber);}
.pur.pl .alert .go{margin-left:auto;color:var(--amber);font-weight:650;font-size:12.5px;}
.pur.pl .toolbar{display:flex;align-items:center;gap:12px;padding:11px 18px;border-bottom:1px solid var(--line2);background:var(--line2);}
.pur.pl .seg{display:inline-flex;gap:2px;}
.pur.pl .seg .o{height:30px;padding:0 13px;border-radius:8px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.pur.pl .seg .o.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.pur.pl .search{margin-left:auto;width:230px;height:34px;background:var(--card);border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;gap:8px;padding:0 11px;}
.pur.pl .search input{border:0;outline:0;flex:1;background:transparent;font-size:13px;color:var(--ink);}

/* 多选筛选条(chip 下拉)· 票面/上传日期开关 */
.pur.pl .filterbar{display:flex;align-items:center;gap:8px;padding:11px 18px;border-bottom:1px solid var(--line2);flex-wrap:wrap;}
.pur.pl .fchip{position:relative;}
.pur.pl .fchip>.t{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--card);border-radius:9px;padding:7px 11px;font-size:12.5px;font-weight:600;color:var(--ink2);cursor:pointer;}
.pur.pl .fchip>.t.active{border-color:var(--accent);color:var(--accent-deep);background:var(--accent-weak);}
.pur.pl .fchip>.t .cnt{font-size:10.5px;font-weight:800;background:var(--accent);color:var(--accent-ink);border-radius:999px;padding:0 6px;line-height:16px;}
/* fixed 定位 + JS 按 chip 位置摆放:逃出列表 panel 的 overflow:hidden(否则空列表时下拉被裁) */
.pur.pl .fchip .dd{position:fixed;z-index:1000;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh2);padding:7px;min-width:210px;max-height:min(320px,60vh);overflow:auto;display:none;}
.pur.pl .fchip.open .dd{display:block;}
.pur.pl .fchip .opt{display:flex;align-items:center;gap:10px;padding:8px 9px;border-radius:8px;font-size:13px;cursor:pointer;color:var(--ink);}
.pur.pl .fchip .opt:hover{background:var(--accent-weak);}
.pur.pl .fchip .opt .box{width:17px;height:17px;border:1.5px solid var(--ink3);border-radius:5px;flex:none;display:grid;place-items:center;}
.pur.pl .fchip .opt .box svg{width:11px;height:11px;stroke:var(--accent-ink);opacity:0;}
.pur.pl .fchip .opt.sel .box{background:var(--accent);border-color:var(--accent);}
.pur.pl .fchip .opt.sel .box svg{opacity:1;}
.pur.pl .fchip .custom{display:none;padding:7px 9px;gap:7px;flex-direction:column;border-top:1px solid var(--line2);margin-top:5px;}
.pur.pl .fchip .custom.on{display:flex;}
.pur.pl .fchip .custom label{font-size:11px;color:var(--ink2);}
.pur.pl .fchip .custom input{border:1px solid var(--line);border-radius:8px;padding:7px 9px;font-size:13px;background:var(--card);color:var(--ink);}
.pur.pl .fchip>.t .ic-chev{transition:transform .15s;}
.pur.pl .fchip.open>.t .ic-chev{transform:rotate(180deg);}
/* 票面/上传日期口径:两段式切换(非 on/off 开关)· 当前段高亮 */
.pur.pl .datebasis{margin-left:auto;display:inline-flex;border:1px solid var(--line);border-radius:9px;padding:2px;background:var(--card);}
.pur.pl .datebasis .o{padding:5px 12px;border-radius:7px;font-size:12px;color:var(--ink2);cursor:pointer;white-space:nowrap;}
.pur.pl .datebasis .o.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}

/* 批量条 + 月份分组 + 行勾选 */
.pur.pl .bulkbar{display:none;align-items:center;gap:10px;background:var(--accent-weak);border-bottom:1px solid var(--accent);padding:9px 18px;font-size:13px;color:var(--accent-deep);font-weight:700;}
.pur.pl .bulkbar.show{display:flex;}
.pur.pl .bulkbar .del{margin-left:auto;color:var(--red);cursor:pointer;display:inline-flex;align-items:center;gap:6px;}
.pur.pl .gchk,.pur.pl .rowchk{width:17px;height:17px;border:1.5px solid var(--ink3);border-radius:5px;flex:none;display:grid;place-items:center;cursor:pointer;}
.pur.pl .gchk svg,.pur.pl .rowchk svg{width:11px;height:11px;stroke:var(--accent-ink);opacity:0;}
.pur.pl .gchk.on,.pur.pl .rowchk.on{background:var(--accent);border-color:var(--accent);}
.pur.pl .gchk.on svg,.pur.pl .rowchk.on svg{opacity:1;}
.pur.pl .monthgrp .gh{display:flex;align-items:center;gap:9px;padding:11px 18px;background:var(--line2);font-weight:700;font-size:13px;cursor:pointer;border-bottom:1px solid var(--line2);}
.pur.pl .monthgrp .gh .cnt{color:var(--ink3);font-weight:600;font-size:12px;}
.pur.pl .monthgrp .gh .sum{margin-left:auto;font-variant-numeric:tabular-nums;}
.pur.pl .monthgrp .gh .chev{transition:.2s;color:var(--ink3);width:14px;height:14px;}
.pur.pl .monthgrp.collapsed .glist{display:none;}
.pur.pl .monthgrp.collapsed .gh .chev{transform:rotate(-90deg);}

.pur.pl .row{display:flex;align-items:center;gap:14px;padding:15px 18px;border-bottom:1px solid var(--line2);cursor:pointer;}
.pur.pl .row:last-child{border-bottom:0;} .pur.pl .row:hover{background:var(--line2);}
.pur.pl .row .dt{width:46px;color:var(--ink3);font-size:12px;flex:0 0 46px;}
.pur.pl .row .who{flex:1;min-width:0;}
.pur.pl .row .nm{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.pur.pl .row .meta{color:var(--ink3);font-size:12px;margin-top:2px;display:flex;align-items:center;gap:8px;}
.pur.pl .src{font-size:10.5px;padding:1px 7px;border-radius:5px;background:var(--line2);color:var(--ink2);}
.pur.pl .src.line{background:var(--green-weak);color:var(--green);}
.pur.pl .att{font-size:10.5px;padding:1px 7px;border-radius:5px;background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.pur.pl .amt{text-align:right;}
.pur.pl .amt .v{font-weight:700;font-size:14.5px;font-variant-numeric:tabular-nums;}
.pur.pl .amt .vat{color:var(--ink3);font-size:11px;margin-top:2px;}
.pur.pl .st{font-size:11px;padding:3px 10px;border-radius:7px;min-width:52px;text-align:center;}
.pur.pl .st.paid{background:var(--line2);color:var(--ink2);}
.pur.pl .st.unpaid,.pur.pl .st.partial{background:var(--amber-weak);color:var(--amber);font-weight:600;}
.pur.pl .st.draft{background:var(--amber-weak);color:var(--amber);font-weight:700;}
.pur.pl .st.void{background:var(--line2);color:var(--ink3);text-decoration:line-through;}
.pur.pl .listfoot{text-align:center;color:var(--ink3);font-size:12px;padding:12px 0 4px;}
.pur.pl .listfoot:empty{display:none;}
/* 主操作响应式:桌面=记一笔(手动)· 手机=拍照(调原生相机)· 见 purchase-list.ts */
.pur.pl .only-mob{display:none;}
@media(max-width:600px){
  .pur.pl .ph{flex-direction:column;align-items:flex-start;gap:11px;}
  .pur.pl .band{flex-direction:column;align-items:stretch;gap:14px;}
  .pur.pl .acts{width:100%;} .pur.pl .acts .btn{flex:1;}
  .pur.pl .only-desk{display:none;}
  .pur.pl .only-mob{display:inline-flex;}
  .pur.pl .more-menu .only-mob{display:block;}
  .pur.pl .search{width:100%;margin-left:0;}
  .pur.pl .toolbar,.pur.pl .filterbar{flex-wrap:wrap;}
  .pur.pl .datebasis{margin-left:0;}
  .pur.pl .row{flex-wrap:wrap;} .pur.pl .row .amt{margin-left:auto;}
}
`;
