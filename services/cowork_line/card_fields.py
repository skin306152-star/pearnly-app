"""Field order and localized labels used by the Cowork LINE review card."""

from services.line_platform.system_i18n import field_label

HEADER_KEYS = (
    "invoice_number",
    "date",
    "document_type",
    "seller_name",
    "seller_tax",
    "seller_branch",
    "seller_address",
    "buyer_name",
    "buyer_tax",
    "buyer_branch",
    "buyer_address",
    "subtotal",
    "discount",
    "vat",
    "wht_amount",
    "total_amount",
    "currency",
    "payment_method",
    "notes",
)

HEADER_LABELS = {
    lang: tuple(field_label(lang, key) for key in HEADER_KEYS) for lang in ("th", "zh", "en", "ja")
}

__all__ = ["HEADER_KEYS", "HEADER_LABELS"]
