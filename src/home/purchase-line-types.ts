import type { ItemType } from './purchase-common.js';

export interface DocLine {
    code?: string;
    barcode?: string;
    id?: string;
    item_type: ItemType;
    product_id: string | null;
    product_matched?: boolean;
    description: string;
    name_unclear?: boolean; // P2C:OCR 整名读不出·description 已清空·前端显「รายการที่ N」占位
    qty: number;
    unit: string | null;
    unit_price: number;
    discount: number;
    vat_rate: number;
    wht_rate: number;
    category_label?: string | null;
    category_id?: string | null;
    subcategory_id?: string | null;
    stock_in?: boolean;
    discountOn?: boolean; // 行折扣开关(UI 态 · 控制是否显示/计折扣输入)
}
