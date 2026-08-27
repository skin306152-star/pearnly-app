// ERP 网页录入薄适配层：只保存入口方向，业务仍由共享 DMS/OCR 工作台执行。
export type ErpDirection = 'purchase' | 'sales';
const DIRECTION_KEY = 'pearnly_erp_intake_direction';

export function isErpEntry(): boolean {
    return window._entry === 'erp' || localStorage.getItem('pearnly_entry') === 'erp';
}

export function setErpIntakeDirection(direction: ErpDirection): void {
    sessionStorage.setItem(DIRECTION_KEY, direction);
    window.routeTo?.('dms-intake');
}

export function erpIntakeDirection(): ErpDirection | '' {
    if (!isErpEntry()) return '';
    const value = sessionStorage.getItem(DIRECTION_KEY);
    return value === 'purchase' || value === 'sales' ? value : '';
}
