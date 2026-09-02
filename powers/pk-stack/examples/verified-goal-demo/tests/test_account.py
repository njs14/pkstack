from __future__ import annotations

import unittest

from account import normalize_account_id


class NormalizeAccountIdTests(unittest.TestCase):
    def test_accepts_plain_twelve_digit_identifier(self) -> None:
        self.assertEqual(normalize_account_id("123456789012"), "123456789012")

    def test_removes_spaces_and_hyphens(self) -> None:
        self.assertEqual(normalize_account_id("1234-5678 9012"), "123456789012")

    def test_rejects_non_digits(self) -> None:
        with self.assertRaisesRegex(ValueError, "12 digits"):
            normalize_account_id("1234-ABCD-9012")

    def test_rejects_wrong_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "12 digits"):
            normalize_account_id("123-456")


if __name__ == "__main__":
    unittest.main()
