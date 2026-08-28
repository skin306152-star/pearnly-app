export const SALES_RECORDS_CSS = `
.pur.pl.sr .sr-filter{display:flex;gap:8px;padding:11px 18px;border-bottom:1px solid var(--line2);flex-wrap:wrap;}
.pur.pl.sr #sr-record-btn{min-height:44px;}
.pur.pl.sr .sr-filter label{display:flex;align-items:center;gap:6px;color:var(--ink3);font-size:11px;}
.pur.pl.sr .sr-filter select{height:34px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink);padding:0 28px 0 10px;font-size:12.5px;}
.pur.pl.sr .src.web{background:var(--accent-weak);color:var(--accent-deep);}
.pur.pl.sr .src.line{background:var(--green-weak);color:var(--green);}
.pur.pl.sr .kind{font-size:10.5px;padding:1px 7px;border-radius:5px;background:var(--line2);color:var(--ink2);}
.pur.pl.sr .kind.goods{background:var(--green-weak);color:var(--green);}
.pur.pl.sr .kind.service{background:var(--accent-weak);color:var(--accent-deep);}
.pur.pl.sr .erp{min-width:78px;text-align:center;font-size:11px;font-weight:650;border-radius:8px;padding:6px 9px;border:0;cursor:pointer;}
.pur.pl.sr .erp.not_pushed{background:var(--accent-weak);color:var(--accent-deep);}
.pur.pl.sr .erp.pending{background:var(--amber-weak);color:var(--amber);}
.pur.pl.sr .erp.success{background:var(--green-weak);color:var(--green);cursor:default;}
.pur.pl.sr .erp.failed{background:var(--red-weak);color:var(--red);}
.pur.pl.sr .erp:disabled{opacity:.65;cursor:wait;}
.pur.pl.sr .row .erpbox{width:92px;display:flex;justify-content:flex-end;}
.pur.pl.sr .row .meta .docno{display:inline-block;width:clamp(100px,30vw,180px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
@media(max-width:700px){
  .pur.pl.sr .sr-filter{display:grid;grid-template-columns:1fr 1fr;}
  .pur.pl.sr .sr-filter label{display:block;}.pur.pl.sr .sr-filter select{width:100%;margin-top:4px;}
  .pur.pl.sr .row .erpbox{width:auto;margin-left:auto;}.pur.pl.sr .row .dt{order:0;}
  .pur.pl.sr .row .who{min-width:calc(100% - 86px);}.pur.pl.sr .row .amt{margin-left:31px;}
}
`;
