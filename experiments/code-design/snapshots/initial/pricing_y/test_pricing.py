"""Contract tests for the integer-cent quote function."""

import copy
import unittest

from pricing import quote


class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.item = {"sku": "A", "unit_price_cents": 101, "quantity": 3}

    def test_default_quote(self):
        self.assertEqual(quote([self.item]), {
            "subtotal_cents": 303,
            "discount_cents": 0,
            "shipping_cents": 0,
            "tax_cents": 0,
            "total_cents": 303,
        })

    def test_rounding_and_shipping_not_taxable(self):
        self.assertEqual(quote([self.item], 17, 99, 7), {
            "subtotal_cents": 303,
            "discount_cents": 51,
            "shipping_cents": 99,
            "tax_cents": 17,
            "total_cents": 368,
        })

    def test_repeated_skus_and_zero_price(self):
        items = [self.item, dict(self.item), {
            "sku": "A", "unit_price_cents": 0, "quantity": 500,
        }]
        self.assertEqual(quote(items)["subtotal_cents"], 606)
        self.assertEqual(quote([items[-1]], shipping_cents=12, tax_percent=100), {
            "subtotal_cents": 0,
            "discount_cents": 0,
            "shipping_cents": 12,
            "tax_cents": 0,
            "total_cents": 12,
        })

    def test_percentage_boundaries(self):
        self.assertEqual(quote([self.item], 100, 55, 100), {
            "subtotal_cents": 303,
            "discount_cents": 303,
            "shipping_cents": 55,
            "tax_cents": 0,
            "total_cents": 55,
        })
        self.assertEqual(quote([self.item], tax_percent=100)["total_cents"], 606)

    def test_very_large_values_remain_exact(self):
        magnitude = 10 ** 100
        result = quote([{
            "sku": "large", "unit_price_cents": magnitude + 1, "quantity": 100,
        }], 37, magnitude, 11)
        self.assertEqual(result, {
            "subtotal_cents": 100 * magnitude + 100,
            "discount_cents": 37 * magnitude + 37,
            "shipping_cents": magnitude,
            "tax_cents": 693 * (magnitude // 100) + 6,
            "total_cents": 7093 * (magnitude // 100) + 69,
        })
        self.assertTrue(all(type(amount) is int for amount in result.values()))

    def test_inputs_preserved_and_calls_independent(self):
        items = [dict(self.item, metadata={"tags": ["sale"]})]
        original = copy.deepcopy(items)
        first = quote(items, 17, 99, 7)
        expected = dict(first)
        first["total_cents"] = -1
        quote([{"sku": "other", "unit_price_cents": 9, "quantity": 1}])
        self.assertEqual(quote(items, 17, 99, 7), expected)
        self.assertEqual(items, original)

    def test_invalid_items_container_or_entry(self):
        for items in (None, [], {}, (), (self.item,), "items", 3, True, [None], [[]], [1]):
            with self.subTest(items=items), self.assertRaises(ValueError):
                quote(items)

    def test_missing_fields(self):
        for key in self.item:
            item = dict(self.item)
            del item[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                quote([item])

    def test_invalid_fields(self):
        invalid_values = {
            "sku": ("", None, 3, False, []),
            "unit_price_cents": (-1, True, False, 1.0, "1", None),
            "quantity": (-1, 0, True, False, 1.0, "1", None),
        }
        for key, values in invalid_values.items():
            for value in values:
                item = dict(self.item, **{key: value})
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    quote([self.item, item])

    def test_invalid_quote_arguments(self):
        for key in ("discount_percent", "tax_percent", "shipping_cents"):
            values = [-1, True, False, 1.0, "1", None]
            if key != "shipping_cents":
                values += [101]
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    quote([self.item], **{key: value})

    def test_invalid_call_preserves_inputs(self):
        items = [self.item, {"sku": "invalid"}]
        original = copy.deepcopy(items)
        with self.assertRaises(ValueError):
            quote(items)
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
