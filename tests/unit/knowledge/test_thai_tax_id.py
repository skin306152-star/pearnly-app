"""MOD-11 Thai tax-id validator, checked against hand-computed expectations.

For 1234567890121 the weighted sum of the first 12 digits (weights 13..2) is
352; 352 mod 11 = 0; (11 - 0) mod 10 = 1, so the 13th digit must be 1 -> valid.
1111111111119: weighted sum 90; 90 mod 11 = 2; (11 - 2) mod 10 = 9 -> valid.
These are computed independently of the implementation under test.
"""

from services.knowledge.rules.validity import valid_thai_tax_id


def test_valid_ids():
    assert valid_thai_tax_id("1234567890121")
    assert valid_thai_tax_id("1111111111119")


def test_invalid_check_digit():
    assert not valid_thai_tax_id("1234567890120")
    assert not valid_thai_tax_id("1111111111111")


def test_wrong_length_or_nondigit():
    assert not valid_thai_tax_id("123")
    assert not valid_thai_tax_id("12345678901234")
    assert not valid_thai_tax_id("12345abc90121")
    assert not valid_thai_tax_id("")


def test_all_zero_is_invalid():
    assert not valid_thai_tax_id("0000000000000")


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestThaiTaxId = build_case(globals(), "TestThaiTaxId")
