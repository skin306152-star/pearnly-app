export type Product = {
    product_id: string;
    code: string;
    name_th?: string;
    name_en?: string;
    name_zh?: string;
    unit?: string;
};
export type Lookup = (query: string) => Promise<Product[]>;
let lookup: Lookup | undefined;
export function setProductLookup(fn: Lookup): void {
    lookup = fn;
}
export function bindProductInput(
    input: HTMLInputElement,
    select: (product: Product) => void
): void {
    if (input.readOnly || input.dataset.productBound) return;
    input.dataset.productBound = '1';
    input.autocomplete = 'off';
    let timer: ReturnType<typeof setTimeout>,
        version = 0;
    const box = document.createElement('div');
    box.className = 'erp-product-suggestions';
    box.setAttribute('role', 'listbox');
    box.hidden = true;
    input.after(box);
    const close = () => {
        box.hidden = true;
        version++;
    };
    input.addEventListener('blur', () =>
        setTimeout(() => {
            if (!box.contains(document.activeElement)) close();
        }, 150)
    );
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') close();
        if (event.key === 'ArrowDown' && !box.hidden) {
            event.preventDefault();
            box.querySelector<HTMLButtonElement>('button')?.focus();
        }
    });
    input.addEventListener('input', () => {
        clearTimeout(timer);
        const current = ++version;
        box.hidden = true;
        const query = input.value.trim();
        if (!query || !lookup) return;
        timer = setTimeout(async () => {
            try {
                const products = await lookup!(query);
                if (current !== version || !input.isConnected) return;
                box.replaceChildren();
                for (const product of products) {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.setAttribute('role', 'option');
                    button.textContent = `${product.code} · ${product.name_zh || product.name_th || product.name_en || ''} · ${product.unit || '—'}`;
                    button.onmousedown = (event) => event.preventDefault();
                    button.onclick = () => {
                        select(product);
                        close();
                    };
                    button.onkeydown = (event) => {
                        if (event.key === 'Escape') {
                            close();
                            input.focus();
                        }
                        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                            event.preventDefault();
                            const next =
                                event.key === 'ArrowDown'
                                    ? button.nextElementSibling
                                    : button.previousElementSibling;
                            (next as HTMLButtonElement | null)?.focus();
                        }
                    };
                    box.append(button);
                }
                const rect = input.getBoundingClientRect();
                Object.assign(box.style, {
                    left: Math.max(8, Math.min(rect.left, window.innerWidth - 328)) + 'px',
                    top: Math.min(rect.bottom + 4, window.innerHeight - 230) + 'px',
                    width: Math.min(440, window.innerWidth - 16) + 'px',
                });
                box.hidden = !products.length;
            } catch {
                close();
            }
        }, 200);
    });
}
