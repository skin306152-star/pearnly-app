// 商户采购 · 复核/录入屏样式(.pur 作用域 · 照搬 docs/smart-intake 原型)· 从 purchase-form 抽出保 <500。
// 全引全站令牌(暗夜随翻面)· 表单控件显式 color:var(--ink) 防暗夜反白 · 勾选/对勾用 var(--accent-ink)。
export const PURCHASE_FORM_CSS = `
.pur .back{display:inline-flex;align-items:center;gap:6px;color:var(--ink2);font-size:12.5px;margin-bottom:11px;cursor:pointer;}
.pur.f .wrap{width:100%;}
.pur .ph{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:13px;}
.pur.f .ph .phl{display:flex;align-items:center;gap:11px;}
.pur.f .ph .back{margin-bottom:0;font-size:24px;line-height:1;color:var(--ink2);flex:none;}
.pur .ph .t{font-size:20px;font-weight:700;}
.pur .ph .sub{color:var(--ink2);font-size:12.5px;margin-top:3px;}
.pur .acts{display:flex;gap:9px;flex-shrink:0;}
.pur .btn.full{width:100%;} .pur .btn.ghost{border-style:dashed;color:var(--accent);} .pur .btn.sm{height:34px;font-size:12.5px;flex:1;}
.pur .wsbar{background:var(--accent-weak);border:1px solid var(--accent-weak);border-radius:10px;padding:9px 13px;font-size:12.5px;color:var(--accent-deep);margin-bottom:14px;}
.pur .wsbar .link{color:var(--accent-deep);font-weight:700;cursor:pointer;text-decoration:underline;}
.pur .dupbar{background:var(--red-weak);border:1px solid var(--red-weak);border-radius:10px;padding:9px 13px;font-size:12.5px;color:var(--red);margin-bottom:14px;}

/* 需复核横幅(消费 confidence_band/field_confidence)· 点字段名平滑滚 + 高亮 */
.pur .vbanner{display:none;gap:10px;align-items:flex-start;background:var(--amber-weak);border:1px solid var(--amber-line,var(--amber-weak));border-radius:12px;padding:11px 13px;margin-bottom:14px;}
.pur .vbanner.show{display:flex;} .pur .vbanner b{color:var(--amber);} .pur .vbanner .j{color:var(--amber);font-weight:800;text-decoration:underline;cursor:pointer;}
.pur .vbanner svg{color:var(--amber);flex:none;}

/* 吸顶上下文条:左=套账(记账给 X) + 右=分类导航(scroll-spy)· 桌面/手机同款 */
.pur .ctxbar{position:sticky;top:0;z-index:9;display:flex;align-items:center;gap:12px;background:var(--bg);padding:9px 0;margin-bottom:14px;border-bottom:1px solid var(--line);}
.pur .ctxbar .wsbar{margin-bottom:0;flex:none;}
.pur .etabs{display:flex;gap:6px;flex:1;overflow-x:auto;}
.pur .etabs button{border:none;background:transparent;color:var(--ink2);padding:7px 14px;border-radius:999px;font-weight:600;font-size:13px;cursor:pointer;white-space:nowrap;}
.pur .etabs button.on{background:var(--accent-weak);color:var(--accent-deep);}

.pur .grid{display:grid;grid-template-columns:330px 1fr;gap:14px;align-items:start;}
/* 右列融成一张连续白卡:内部各 card 去边框/阴影,区与区之间一条细横线(治「东一块西一块」) */
.pur.f .rcol{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--sh);overflow:hidden;}
.pur.f .rcol .card{border:0;border-radius:0;box-shadow:none;background:transparent;}
.pur.f .rcol .card + .card,.pur.f .rcol > div + div .card:first-child{border-top:1px solid var(--line);}
.pur .edit-left{position:sticky;top:0;align-self:start;}
.pur .col{display:flex;flex-direction:column;gap:14px;}
.pur .card>.hd{padding:12px 15px;border-bottom:1px solid var(--line);font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center;gap:8px;}
.pur .card>.hd .muted{color:var(--ink3);font-weight:400;cursor:pointer;}
.pur .card>.bd{padding:13px 15px;}
.pur .field{margin-bottom:11px;}
.pur .field>label{display:flex;gap:6px;align-items:center;font-size:11.5px;color:var(--ink2);margin-bottom:5px;}
.pur .field>label .req{color:var(--red);}
.pur .field>label .tg{font-size:10px;font-weight:800;border-radius:5px;padding:1px 6px;}
.pur .tg-ok{background:var(--green-weak);color:var(--green);} .pur .tg-fix{background:var(--amber-weak);color:var(--amber);} .pur .tg-learn{background:var(--accent-weak);color:var(--accent-deep);}
.pur .tg-need{background:var(--red-weak);color:var(--red);}
.pur .inp{min-height:40px;border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;padding:7px 12px;font-size:13.5px;background:var(--card);color:var(--ink);}
.pur .inp.pick{cursor:pointer;justify-content:space-between;} .pur .inp.ro{background:var(--line2);font-weight:700;} .pur .inp.ph{color:var(--ink3);}
.pur .field.ok .inp{border-color:var(--green-weak);background:var(--green-weak);} .pur .field.fix .inp{border-color:var(--amber-line,var(--amber-weak));background:var(--amber-weak);}
.pur .field.need .inp,.pur .field.err .inp{border-color:var(--red);background:var(--red-weak);}
.pur .field .et{color:var(--red);font-size:12px;margin-top:5px;display:none;} .pur .field.need .et,.pur .field.err .et{display:block;}
.pur input.fin{width:100%;border:0;outline:0;background:transparent;font:inherit;color:inherit;}
.pur input.fin::-webkit-outer-spin-button,.pur input.fin::-webkit-inner-spin-button{-webkit-appearance:none;margin:0;}
.pur select.fsel{border:0;outline:0;background:transparent;font:inherit;color:var(--ink);width:100%;cursor:pointer;}
.pur .two{display:grid;grid-template-columns:1fr 1fr;gap:11px;} .pur .two .field{margin:0;}
.pur .row-inline{display:flex;align-items:center;gap:8px;}
.pur .rd{flex:none;border:1px solid var(--accent);color:var(--accent-deep);background:var(--card);border-radius:9px;padding:10px 12px;font-size:12px;font-weight:700;white-space:nowrap;cursor:pointer;}
.pur .swrow{display:flex;align-items:center;gap:9px;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.pur .sw{width:40px;height:23px;border-radius:999px;background:var(--line);position:relative;flex:none;transition:.15s;}
.pur .sw.on{background:var(--accent);} .pur .sw::after{content:"";position:absolute;left:3px;top:3px;width:17px;height:17px;border-radius:50%;background:var(--card);transition:.15s;} .pur .sw.on::after{left:20px;}
.pur .hide{display:none!important;}
.pur .aimark{font-size:10.5px;background:var(--green-weak);color:var(--green);padding:1px 7px;border-radius:5px;margin-left:6px;font-weight:600;}
.pur .hint{background:var(--amber-weak);border:1px solid var(--amber-weak);border-radius:9px;padding:8px 11px;font-size:12px;color:var(--amber);margin-bottom:10px;}
.pur .infonote{background:var(--bg);border-radius:10px;padding:10px 12px;font-size:12px;color:var(--ink2);margin-bottom:12px;display:flex;gap:7px;align-items:flex-start;}

/* 图查看器:拖拽平移 + 滚轮缩放 + 旋转/复位 + 实时百分比 + 多文件 1/N 相册 */
.pur .viewer{background:var(--line2);border:1px solid var(--line);border-radius:12px;height:320px;position:relative;overflow:hidden;cursor:grab;touch-action:none;}
.pur .viewer.grabbing{cursor:grabbing;}
.pur .viewer .vimg{position:absolute;left:50%;top:50%;max-width:78%;max-height:88%;transform-origin:center;will-change:transform;user-select:none;-webkit-user-drag:none;}
.pur .viewer .vph{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--ink3);text-align:center;}
.pur .viewer .vfile{position:absolute;top:10px;right:10px;background:var(--card);border:1px solid var(--line);color:var(--ink2);border-radius:7px;font-size:11px;padding:3px 9px;font-weight:600;}
.pur .viewer .vhint{position:absolute;left:10px;top:10px;background:var(--card);border:1px solid var(--line);color:var(--ink3);border-radius:7px;font-size:11px;padding:3px 9px;}
.pur .viewer .vtools{position:absolute;right:10px;bottom:10px;display:flex;gap:6px;align-items:center;}
.pur .viewer .vtools button{background:var(--card);border:1px solid var(--line);color:var(--ink2);border-radius:8px;width:32px;height:32px;display:grid;place-items:center;cursor:pointer;flex:none;}
.pur .viewer .vzoom{background:var(--card);border:1px solid var(--line);border-radius:8px;font-size:12px;font-weight:700;padding:0 10px;height:32px;display:flex;align-items:center;color:var(--ink2);}
.pur .thumbs{display:flex;gap:8px;margin-top:10px;overflow:auto;}
.pur .thumbs .t{width:50px;height:60px;border-radius:8px;border:1px solid var(--line);background:var(--line2);display:grid;place-items:center;flex:none;color:var(--ink3);cursor:pointer;overflow:hidden;}
.pur .thumbs .t img{width:100%;height:100%;object-fit:cover;}
.pur .thumbs .t.on{border-color:var(--accent);border-width:2px;}
.pur .thumbs .add{width:50px;height:60px;border-radius:8px;border:1px dashed var(--ink3);display:grid;place-items:center;color:var(--ink2);flex:none;cursor:pointer;}
.pur .img{aspect-ratio:3/4;background:var(--line2);border:1px dashed var(--line);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:8px;color:var(--ink3);margin-bottom:9px;overflow:hidden;}
.pur .seg2{display:flex;gap:8px;} .pur .mt{margin-top:10px;}
.pur .seg{display:flex;gap:7px;}
.pur .seg .o{flex:1;height:38px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:12.5px;color:var(--ink2);cursor:pointer;text-align:center;padding:0 6px;}
.pur .seg .o.on{border-color:var(--accent);background:var(--accent-weak);color:var(--accent-deep);font-weight:700;}
.pur .seg.sm2 .o{height:34px;font-size:12px;}

/* 明细行 */
.pur .item{border:1px solid var(--line);border-radius:11px;padding:11px 12px;margin-bottom:10px;}
.pur .irow1{display:flex;align-items:center;gap:10px;margin-bottom:10px;}
.pur .irow1 .seg{flex:0 0 130px;} .pur .irow1 .iname{flex:1;font-weight:600;font-size:13.5px;}
.pur .irow1 .iname input{width:100%;border:0;outline:0;font:inherit;background:transparent;color:var(--ink);}
.pur .irow1 .x{color:var(--ink3);cursor:pointer;font-size:16px;}
.pur .igrid{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;}
.pur .igrid .f label{display:block;font-size:11px;color:var(--ink2);margin-bottom:4px;}
.pur .inp.sm{min-height:36px;font-size:13px;padding:5px 10px;}
.pur .idisc{margin-top:9px;}
.pur .iextra{margin-top:9px;font-size:11.5px;color:var(--ink2);}
.pur .iextra .link{color:var(--accent);cursor:pointer;}
.pur .pill{font-size:10.5px;padding:1px 7px;border-radius:5px;}
.pur .pill.ok{background:var(--green-weak);color:var(--green);} .pur .pill.warn{background:var(--amber-weak);color:var(--amber);}
.pur .addline{width:100%;border:1px dashed var(--accent);color:var(--accent-deep);background:var(--accent-weak);border-radius:11px;padding:11px;font-weight:700;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:6px;}

/* 汇总卡(手动改额) */
.pur .sum{display:flex;justify-content:space-between;align-items:center;padding:6px 0;font-size:13px;}
.pur .sum.tot{border-top:1px solid var(--line);margin-top:6px;padding-top:11px;font-weight:800;font-size:16px;}
.pur .sum.mid{font-size:13px;font-weight:600;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
.pur .sum .tax{color:var(--green);} .pur .sum .wht{color:var(--amber);}
.pur .sum .medit{width:96px;text-align:right;border:1px solid var(--line);border-radius:8px;padding:5px 8px;font:inherit;color:var(--ink);background:var(--card);}
.pur .consist{font-size:12px;border-radius:9px;padding:8px 11px;margin-top:8px;}
.pur .consist.ok{background:var(--green-weak);color:var(--green);} .pur .consist.bad{background:var(--red-weak);color:var(--red);}

/* 底部操作条:吸底 + 三个按钮均匀铺满 */
.pur .editfoot{display:flex;gap:9px;padding:12px 0;position:sticky;bottom:0;background:var(--bg);border-top:1px solid var(--line);z-index:9;}
.pur .editfoot .btn{flex:1;}
@media(max-width:760px){
  .pur .ctxbar{flex-direction:column;align-items:stretch;}
  .pur .ctxbar .wsbar{width:100%;}
  .pur .etabs{flex:none;}
  .pur .ph{flex-direction:column;}
  .pur .grid{grid-template-columns:1fr;} .pur .edit-left{position:static;}
  .pur .igrid{grid-template-columns:repeat(2,1fr);}
  .pur .irow1{flex-wrap:wrap;} .pur .irow1 .seg{flex:0 0 100%;order:3;} .pur .irow1 .iname{order:1;} .pur .irow1 .x{order:2;}
}
`;
