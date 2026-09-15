// ERP 网页录入薄适配层：只保存入口方向，手填与识别共用内部记录表单。
export type ErpDirection = 'purchase' | 'sales';
const DIRECTION_KEY = 'pearnly_erp_intake_direction';

export function isErpEntry(): boolean {
    return window._entry === 'erp' || localStorage.getItem('pearnly_entry') === 'erp';
}

export function isCoworkEntry(): boolean {
    return (
        window._entry === 'cowork' ||
        window._entry === 'main' ||
        localStorage.getItem('pearnly_entry') === 'cowork' ||
        localStorage.getItem('pearnly_entry') === 'main'
    );
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
