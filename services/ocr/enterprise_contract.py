"""Versioned extraction contract from the 2026-09-03 evaluation."""

from __future__ import annotations

CONTRACT_VERSION = "enterprise-2026-09-03-v1"
MODEL = "gemini-3.8-flash"
LOCATION = "global"
THINKING_LEVEL = "LOW"
MAX_OUTPUT_TOKENS = 16384


def string_property() -> dict:
    return {"type": "string"}


def object_schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required or list(properties),
    }


INVOICE_ITEM = object_schema(
    {key: string_property() for key in ("name", "qty", "price", "subtotal")}
)
EXTRA_INVOICE = object_schema(
    {
        "invoice_number": string_property(),
        "date": string_property(),
        "seller_name": string_property(),
        "seller_tax": string_property(),
        "total_amount": string_property(),
        "items": {"type": "array", "items": INVOICE_ITEM},
    }
)
INVOICE_SCHEMA = object_schema(
    {
        "document_type": {
            "type": "string",
            "enum": [
                "tax_invoice",
                "simplified_tax_invoice",
                "receipt",
                "credit_note",
                "payment_evidence",
                "order_evidence",
                "purchase_order",
                "quotation",
                "delivery_note",
                "other",
            ],
        },
        "invoice_number": string_property(),
        "date": string_property(),
        "date_raw": string_property(),
        "seller_name": string_property(),
        "seller_tax": string_property(),
        "seller_addr": string_property(),
        "buyer_name": string_property(),
        "buyer_tax": string_property(),
        "buyer_addr": string_property(),
        "subtotal": string_property(),
        "vat": string_property(),
        "discount": string_property(),
        "total_amount": string_property(),
        "cash_amount": string_property(),
        "change_amount": string_property(),
        "payment_method": string_property(),
        "currency": string_property(),
        "items": {"type": "array", "items": INVOICE_ITEM},
        "additional_invoices": {"type": "array", "items": EXTRA_INVOICE},
    }
)
BANK_ENTRY = object_schema(
    {
        key: string_property()
        for key in (
            "transaction_date",
            "transaction_date_raw",
            "description",
            "reference",
            "deposit",
            "withdrawal",
            "amount",
            "direction",
            "balance",
        )
    }
)
BANK_SCHEMA = object_schema(
    {
        "document_type": string_property(),
        "bank_name": string_property(),
        "bank_code": string_property(),
        "account_name": string_property(),
        "account_number": string_property(),
        "account_last4": string_property(),
        "period_start": string_property(),
        "period_end": string_property(),
        "opening_balance": string_property(),
        "closing_balance": string_property(),
        "entries": {"type": "array", "items": BANK_ENTRY},
    }
)
GL_ENTRY = object_schema(
    {
        key: string_property()
        for key in (
            "transaction_date",
            "transaction_date_raw",
            "voucher_no",
            "account_code",
            "description",
            "debit",
            "credit",
            "amount",
            "direction",
            "balance",
        )
    }
)
GL_SCHEMA = object_schema(
    {
        "document_type": string_property(),
        "period_start": string_property(),
        "period_end": string_property(),
        "account_name": string_property(),
        "account_number": string_property(),
        "opening_balance": string_property(),
        "closing_balance": string_property(),
        "total_debit": string_property(),
        "total_credit": string_property(),
        "entries": {"type": "array", "items": GL_ENTRY},
    }
)
VAT_ENTRY = object_schema(
    {
        key: string_property()
        for key in (
            "seq_no",
            "transaction_date",
            "transaction_date_raw",
            "invoice_no",
            "customer_name",
            "customer_tax",
            "customer_branch",
            "subtotal",
            "vat",
            "total",
        )
    }
)
VAT_SCHEMA = object_schema(
    {
        "document_type": string_property(),
        "seller_name": string_property(),
        "seller_tax": string_property(),
        "period_year": string_property(),
        "period_month": string_property(),
        "total_subtotal": string_property(),
        "total_vat": string_property(),
        "total_total": string_property(),
        "entries": {"type": "array", "items": VAT_ENTRY},
    }
)


COMMON = """Use the attached original document image as the primary source and the Enterprise OCR
transcript as a second reading. Return only the requested JSON. Never use an expected answer and do
not invent unreadable values. Preserve every printed table row exactly once and in printed order.
Convert unambiguous Buddhist years to Gregorian by subtracting 543. Return monetary values as strings
without currency symbols or thousands separators; use an empty string when a field is absent.
"""

PROMPTS = {
    "invoice": COMMON
    + """This is a Thai accounting document such as a tax invoice, receipt, purchase order,
quotation or delivery note. total_amount is the final payable total, not cash tendered or change.
Extract each item row with name, quantity, unit price and line subtotal. Tax IDs contain 13 digits.
Use a snake_case document_type from the schema enum. A Tax ID printed below a Buyer label belongs to
the buyer, not the seller. Cross-check invoice-number characters directly in the image because OCR
can confuse I, T, 1 and 7. Preserve identifier prefixes such as R#, REF and Rcpt when they are printed
as part of the value; exclude a plain field label followed by a colon. Keep invoice_number to the
single labeled line and never append a terminal ID, time or date. subtotal is the printed Subtotal,
not a value calculated backward from VAT or Total. Do not change spelling merely to make it look correct.
If the image contains a clearly separate second invoice or a section labeled as another invoice,
extract it into additional_invoices rather than silently dropping it; otherwise return an empty array.
""",
    "bank": COMMON
    + """This is a bank statement. Extract opening and closing balances and every transaction row.
Read deposit, withdrawal and running balance only from their table columns. amount equals the non-empty
deposit or withdrawal and direction must match it. Reference digits and description digits are never
amounts. Do not include headers, carried-forward rows or totals as transactions.
""",
    "gl": COMMON
    + """This is a General Ledger. Extract opening/closing balance and every transaction row.
Read debit, credit and balance only from their printed columns. Voucher/account/description digits are
never amounts. Do not include page headers, carried-forward rows or totals as entries.
""",
    "vat": COMMON
    + """This is a Thai VAT report. Extract every invoice row plus printed report totals. Keep seller
and customer tax IDs as 13 digits. Do not count headers, subtotals or page totals as entries.
""",
}
SCHEMAS = {"invoice": INVOICE_SCHEMA, "bank": BANK_SCHEMA, "gl": GL_SCHEMA, "vat": VAT_SCHEMA}
