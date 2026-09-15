"""Changing the edit action must preserve every original button appearance property."""

from unittest import TestCase, mock
from services.line_dms import cards, edit_link


class CustomerButtonStyleTests(TestCase):
    def test_browser_edit_preserves_original_style_across_all_oa_cards(self):
        for channel in ("dms", "dms_a", "dms_b"):
            with (
                self.subTest(channel=channel),
                mock.patch.object(
                    edit_link, "url", return_value=f"https://example.com/edit?channel={channel}"
                ),
            ):
                original = cards._btn(cards.BTN_EDIT, "old", "secondary")
                edited = cards._edit_button("nonce")
                self.assertEqual(
                    {k: v for k, v in edited.items() if k != "action"},
                    {k: v for k, v in original.items() if k != "action"},
                )
                self.assertEqual(edited["action"]["type"], "uri")
                self.assertEqual(edited["action"]["label"], original["action"]["label"])
                card = cards.diff_card([], "nonce", primary="update", summary={})
                buttons = card["contents"]["footer"]["contents"]
                self.assertEqual([b["height"] for b in buttons], ["sm", "sm", "sm"])
                self.assertEqual(
                    [b["style"] for b in buttons], ["primary", "secondary", "secondary"]
                )

    def test_unavailable_link_preserves_original_button(self):
        with mock.patch.object(edit_link, "url", return_value=""):
            self.assertEqual(
                cards._edit_button("nonce"),
                cards._btn(cards.BTN_EDIT, cards._data(cards.ACT_EDIT, nonce="nonce"), "secondary"),
            )
