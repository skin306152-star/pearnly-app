export const SALES_RECORD_DETAIL_CSS = `
.pur.d.srd .summary{grid-template-columns:1.25fr .8fr .8fr .8fr;}
.pur.d.srd .original-note{padding:0 18px 14px;color:var(--ink3);font-size:11.5px;line-height:1.55;}
.pur.d.srd .kind-label{display:inline-flex;align-items:center;height:24px;padding:0 9px;border-radius:999px;background:var(--accent-weak);color:var(--accent-deep);font-size:11.5px;font-weight:700;}
.pur.d.srd .pushbox{padding:14px 18px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:8px;}
.pur.d.srd .pushbox .row{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:12px;color:var(--ink2);}
.pur.d.srd .pushbox .btn{justify-content:center;}
.pur.d.srd .preview-pane .img{min-height:250px;}
.pur.d.srd .preview-pane .img img{width:100%;height:auto;max-height:440px;object-fit:contain;}
@media(max-width:760px){.pur.d.srd .summary{grid-template-columns:1fr 1fr;}.pur.d.srd .summary .si:nth-child(3){border-left:0;border-top:1px solid var(--line);}.pur.d.srd .summary .si:nth-child(4){border-top:1px solid var(--line);}}
`;
