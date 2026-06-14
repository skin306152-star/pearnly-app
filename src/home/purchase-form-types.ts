// 商户采购 · 复核屏状态类型(DraftIn 入参 / FormState)。从 purchase-form 抽出保 <500 · 子模块共用 FormState。
import type { DocKind, DocLine } from './purchase-common.js';

export interface DraftIn {
    id?: string;
    doc_kind?: DocKind;
    supplier?: {
        name?: string;
        tax_id?: string;
        branch_type?: string;
        branch_no?: string;
        address?: string;
    } | null;
    doc_no?: string | null;
    doc_date?: string | null;
    due_date?: string | null;
    has_vat?: boolean;
    currency?: string;
    fx_rate?: number | null;
    requester?: string | null;
    payment_status?: string;
    lines?: DocLine[];
    ai_fields?: number;
    dedupe_hit?: boolean;
    confidence_band?: string;
    field_confidence?: Record<string, number>;
    bill_image_ref?: string | null;
    bill_image_url?: string | null;
    bill_image_local?: string | null;
    attachments?: { kind?: string; url?: string | null }[];
}

export interface FormState {
    id: string | null;
    doc_kind: DocKind;
    supplierName: string;
    taxId: string;
    branchType: string;
    branchNo: string;
    branchName: string;
    address: string;
    docNo: string;
    docDate: string;
    dueLabel: string;
    hasVat: boolean;
    paymentStatus: 'unpaid' | 'paid';
    requester: string;
    currency: string;
    fxRate: string;
    lines: DocLine[];
    mergeMode: boolean; // 明细 拆分多条(false·默认)/ 合并记一条(true · 不逐项·单行)
    priceMode: 'exclusive' | 'inclusive';
    manualOn: boolean;
    override: { subtotal: number; discount: number; vat: number; grand: number };
    aiFields: number;
    dedupeHit: boolean;
    confidenceBand: string;
    fieldConf: Record<string, 'ok' | 'fix'>;
    billRef: string;
    billUrls: string[];
    billIdx: number;
}
