// 商户采购 · 屏10 录入页样式(.pur 作用域 · 逐令牌照搬设计稿 10-费用进项录入)· 从 purchase-form 抽出保 <500。
export const PURCHASE_FORM_CSS = `
.pur .back{display:inline-flex;align-items:center;gap:6px;color:var(--ink2);font-size:12.5px;margin-bottom:11px;cursor:pointer;}
.pur.f .wrap{width:100%;}
.pur .ph{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px;}
.pur .ph .t{font-size:20px;font-weight:700;}
.pur .ph .sub{color:var(--ink2);font-size:12.5px;margin-top:3px;}
.pur .acts{display:flex;gap:9px;flex-shrink:0;}
.pur .btn.full{width:100%;} .pur .btn.ghost{border-style:dashed;color:var(--accent);} .pur .btn.sm{height:34px;font-size:12.5px;flex:1;}
.pur .wsbar{background:var(--accent-weak);border:1px solid var(--accent-weak);border-radius:10px;padding:9px 13px;font-size:12.5px;color:var(--accent-deep);margin-bottom:14px;}
.pur .wsbar .link{color:var(--accent-deep);font-weight:700;cursor:pointer;text-decoration:underline;}
.pur .dupbar{background:var(--red-weak);border:1px solid var(--red-weak);border-radius:10px;padding:9px 13px;font-size:12.5px;color:var(--red);margin-bottom:14px;}
.pur .grid{display:grid;grid-template-columns:330px 1fr;gap:14px;align-items:start;}
.pur .col{display:flex;flex-direction:column;gap:14px;}
.pur .card>.hd{padding:12px 15px;border-bottom:1px solid var(--line);font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center;}
.pur .card>.hd .muted{color:var(--ink3);font-weight:400;cursor:pointer;}
.pur .card>.bd{padding:13px 15px;}
.pur .field{margin-bottom:11px;}
.pur .field>label{display:block;font-size:11.5px;color:var(--ink2);margin-bottom:5px;}
.pur .inp{min-height:40px;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;padding:7px 12px;font-size:13.5px;background:var(--card);}
.pur .inp.pick{cursor:pointer;justify-content:space-between;} .pur .inp.ro{background:var(--line2);font-weight:700;} .pur .inp.ph{color:var(--ink3);}
.pur .inp.ai{border-color:var(--green-weak);background:var(--green-weak);} .pur .inp.todo{border-color:var(--amber-weak);background:var(--amber-weak);}
.pur input.fin{width:100%;border:0;outline:0;background:transparent;font:inherit;color:inherit;}
.pur input.fin::-webkit-outer-spin-button,.pur input.fin::-webkit-inner-spin-button{-webkit-appearance:none;margin:0;}
.pur select.fsel{border:0;outline:0;background:transparent;font:inherit;color:inherit;width:100%;cursor:pointer;}
.pur .two{display:grid;grid-template-columns:1fr 1fr;gap:11px;}
.pur .seg{display:flex;gap:7px;}
.pur .seg .o{flex:1;height:38px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:12.5px;color:var(--ink2);cursor:pointer;text-align:center;padding:0 6px;}
.pur .seg .o.on{border-color:var(--accent);background:var(--accent-weak);color:var(--accent-deep);font-weight:700;}
.pur .seg.sm2 .o{height:34px;font-size:12px;}
.pur .aimark{font-size:10.5px;background:var(--green-weak);color:var(--green);padding:1px 7px;border-radius:5px;margin-left:6px;font-weight:600;}
.pur .hint{background:var(--amber-weak);border:1px solid var(--amber-weak);border-radius:9px;padding:8px 11px;font-size:12px;color:var(--amber);margin-bottom:10px;}
.pur .docchip{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:9px;padding:8px 11px;font-size:12.5px;margin-bottom:9px;}
.pur .docchip .pdf{background:var(--red-weak);color:var(--red);font-size:10px;font-weight:700;padding:2px 6px;border-radius:5px;}
.pur .docchip .x{margin-left:auto;color:var(--ink3);cursor:pointer;}
.pur .img{aspect-ratio:3/4;background:var(--line2);border:1px dashed var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:var(--ink3);margin-bottom:9px;overflow:hidden;}
.pur .img img{width:100%;height:100%;object-fit:cover;}
.pur .img img.billimg{object-fit:contain;cursor:zoom-in;}
.pur .seg2{display:flex;gap:8px;} .pur .mt{margin-top:10px;}
.pur .item{border:1px solid var(--line);border-radius:11px;padding:11px 12px;margin-bottom:10px;}
.pur .irow1{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.pur .irow1 .seg{flex:0 0 130px;} .pur .irow1 .iname{flex:1;font-weight:600;font-size:13.5px;}
.pur .irow1 .iname input{width:100%;border:0;outline:0;font:inherit;background:transparent;}
.pur .irow1 .x{color:var(--ink3);cursor:pointer;font-size:16px;}
.pur .igrid{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;}
.pur .igrid .f label{display:block;font-size:11px;color:var(--ink2);margin-bottom:4px;}
.pur .inp.sm{min-height:36px;font-size:13px;padding:5px 10px;}
.pur .iextra{margin-top:9px;font-size:11.5px;color:var(--ink2);}
.pur .iextra .link{color:var(--accent);cursor:pointer;}
.pur .pill{font-size:10.5px;padding:1px 7px;border-radius:5px;}
.pur .pill.ok{background:var(--green-weak);color:var(--green);} .pur .pill.warn{background:var(--amber-weak);color:var(--amber);}
.pur .sum{display:flex;justify-content:space-between;padding:6px 0;font-size:13px;}
.pur .sum.tot{border-top:1px solid var(--line);margin-top:6px;padding-top:11px;font-weight:800;font-size:16px;}
.pur .sum.mid{font-size:13px;font-weight:600;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
.pur .sum .tax{color:var(--green);} .pur .sum .wht{color:var(--amber);}
@media(max-width:760px){
  .pur .ph{flex-direction:column;} .pur .acts{width:100%;} .pur .acts .btn{flex:1;}
  .pur .grid{grid-template-columns:1fr;}
  .pur .igrid{grid-template-columns:repeat(2,1fr);}
  .pur .irow1{flex-wrap:wrap;} .pur .irow1 .seg{flex:0 0 100%;order:3;} .pur .irow1 .iname{order:1;} .pur .irow1 .x{order:2;}
}
`;
