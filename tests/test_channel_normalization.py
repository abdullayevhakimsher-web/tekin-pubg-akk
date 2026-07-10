import unittest

from database import db


class ChannelNormalizationTests(unittest.TestCase):
    def test_full_tme_link_is_normalized(self):
        self.assertEqual(
            db.normalize_channel_link("https://t.me/TekiinAkklar"),
            "@TekiinAkklar",
        )

    def test_plain_username_is_prefixed(self):
        self.assertEqual(db.normalize_channel_link("TekiinAkklar"), "@TekiinAkklar")

    def test_existing_at_username_is_preserved(self):
        self.assertEqual(db.normalize_channel_link("@TekiinAkklar"), "@TekiinAkklar")


if __name__ == "__main__":
    unittest.main()
