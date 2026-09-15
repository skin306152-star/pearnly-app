// ERP/POS only: move the existing buyer pane without replacing its controls or listeners.
export function configureCustomerNavigation(entry: string): void {
    const split = entry === 'erp' || entry === 'pos';
    const menu = document.getElementById('nav-buyer-clients');
    if (menu) menu.style.display = split ? '' : 'none';
    if (!split) return;
    const label = document.querySelector<HTMLElement>(
        '.nav-item[data-route="clients"] [data-i18n]'
    );
    if (label) {
        label.dataset.i18n = 'company-master-title';
        label.textContent = window.t('company-master-title');
    }
    const company = document.getElementById('page-clients');
    const customers = document.getElementById('page-buyer-clients');
    const pane = document.getElementById('cust-pane-buyer');
    if (!company || !customers || !pane) return;
    const title = company.querySelector<HTMLElement>('.h1');
    if (title) {
        title.dataset.i18n = 'company-master-title';
        title.textContent = window.t('company-master-title');
    }
    company.querySelector('.sub')?.remove();
    company.querySelector('.cust-tab-bar')?.remove();
    if (!customers.contains(pane)) {
        customers.classList.add('ui');
        const wrap = document.createElement('div');
        wrap.className = 'wrap';
        const heading = document.createElement('div');
        heading.className = 'pagehead';
        const text = document.createElement('div');
        text.className = 'h1';
        text.dataset.i18n = 'buyer-customers-title';
        text.textContent = window.t('buyer-customers-title');
        heading.append(text);
        wrap.append(heading, pane);
        customers.append(wrap);
    }
    pane.classList.add('active');
    document.getElementById('cust-pane-seller')?.classList.add('active');
}
