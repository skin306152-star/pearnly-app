// Read-only mode keeps the original tabs and attachment controls available.
export function lockPurchasePreview(root: HTMLElement | null): void {
    root?.querySelectorAll<HTMLInputElement>(
        '.form-pane input,.form-pane select,.editfoot button'
    ).forEach((el) => {
        el.disabled = true;
    });
    root?.querySelectorAll<HTMLElement>(
        '.seg .o,#pur-supplier-pick,#pur-lines [data-del],#pur-add-line,#pur-lines [data-match],#pur-lines [data-disc],#pur-lines [data-wht],#pur-manual-tog,#pur-add-file,#pur-gen-receipt'
    ).forEach((el) => {
        el.onclick = null;
        el.setAttribute('aria-disabled', 'true');
    });
    root?.querySelectorAll<HTMLElement>('.editfoot').forEach((el) => {
        el.hidden = true;
        el.style.display = 'none';
    });
}
