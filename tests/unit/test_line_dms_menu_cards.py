import os
import unittest
from unittest.mock import patch

from services.line_dms import cards, menu_cards


class DmsMenuCardTests(unittest.TestCase):
    def _items(self):
        contents = menu_cards.menu_card()["contents"]["body"]["contents"]
        return [item for item in contents if item.get("action")]

    def test_card_has_three_actions_in_order(self):
        with patch.dict(os.environ, {"LINE_DMS_LIFF_ID": "DMS-LIFF"}, clear=False):
            items = self._items()
        self.assertEqual(len(items), 3)
        self.assertEqual(
            items[0]["action"],
            {"type": "postback", "data": cards._data(cards.ACT_MENU_CUSTOMER)},
        )
        self.assertEqual(
            items[1]["action"],
            {"type": "postback", "data": cards._data(cards.ACT_MENU_BOOKING)},
        )
        self.assertEqual(
            items[2]["action"],
            {
                "type": "uri",
                "label": cards.TXT_MENU_ITEM3,
                "uri": "https://liff.line.me/DMS-LIFF?portal=dms",
            },
        )

    def test_third_action_falls_back_to_dms(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self._items()[2]["action"]["uri"], "https://pearnly.com/dms")


if __name__ == "__main__":
    unittest.main()
