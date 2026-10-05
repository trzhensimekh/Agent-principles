"""Observable contract tests for the quote API."""

import copy
import unittest

from pricing import quote


class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.items = [{"sku": "widget", "unit_price_cents": 101, "quantity": 1}]

    def test_defaults_and_result_shape(self):
        result = quote(self.items)
        self.assertEqual(result, {
            "subtotal_cents": 101,
            "discount_cents": 0,
            "shipping_cents": 0,
            "tax_cents": 0,
            "total_cents": 101,
        })
        self.assertTrue(all(type(amount) is int for amount in result.values()))

    def test_rounding_and_tax_base_exclude_shipping(self):
        self.assertEqual(quote(self.items, 50, 99, 50), {
            "subtotal_cents": 101,
            "discount_cents": 50,
            "shipping_cents": 99,
            "tax_cents": 25,
            "total_cents": 175,
        })

    def test_discount_rounds_after_summing_lines(self):
        items = [
            {"sku": "a", "unit_price_cents": 1, "quantity": 1},
            {"sku": "b", "unit_price_cents": 1, "quantity": 1},
        ]
        self.assertEqual(quote(items, 50, 0, 50), {
            "subtotal_cents": 2,
            "discount_cents": 1,
            "shipping_cents": 0,
            "tax_cents": 0,
            "total_cents": 1,
        })

    def test_repeated_skus_zero_prices_and_quantities(self):
        items = [
            {"sku": "same", "unit_price_cents": 100, "quantity": 2},
            {"sku": "same", "unit_price_cents": 150, "quantity": 1},
            {"sku": "free", "unit_price_cents": 0, "quantity": 100},
        ]
        self.assertEqual(quote(items)["subtotal_cents"], 350)

    def test_percentage_upper_bound(self):
        self.assertEqual(quote(self.items, 100, 7, 100), {
            "subtotal_cents": 101,
            "discount_cents": 101,
            "shipping_cents": 7,
            "tax_cents": 0,
            "total_cents": 7,
        })
        self.assertEqual(quote(self.items, tax_percent=100)["tax_cents"], 101)

    def test_zero_subtotal_with_shipping(self):
        items = [{"sku": "free", "unit_price_cents": 0, "quantity": 1}]
        self.assertEqual(quote(items, 50, 23, 100), {
            "subtotal_cents": 0,
            "discount_cents": 0,
            "shipping_cents": 23,
            "tax_cents": 0,
            "total_cents": 23,
        })

    def test_very_large_amounts_are_exact(self):
        items = [{"sku": "large", "unit_price_cents": 10**100 + 7, "quantity": 3}]
        result = quote(items, 33, 9, 25)
        self.assertEqual(result, {
            "subtotal_cents": 3 * 10**100 + 21,
            "discount_cents": 99 * 10**98 + 6,
            "shipping_cents": 9,
            "tax_cents": 5025 * 10**96 + 3,
            "total_cents": 25125 * 10**96 + 27,
        })
        self.assertTrue(all(type(amount) is int for amount in result.values()))

    def test_caller_inputs_are_preserved_and_results_are_independent(self):
        self.items[0]["metadata"] = {"tags": ["sale"]}
        original = copy.deepcopy(self.items)
        expected = quote(self.items, 15, 12, 7)
        first = quote(self.items, 15, 12, 7)
        first["total_cents"] = -1
        quote(self.items, 100, 999, 100)
        self.assertEqual(quote(self.items, 15, 12, 7), expected)
        self.assertEqual(self.items, original)

    def test_invalid_items_container(self):
        for items in (None, [], {}, (), tuple(self.items), "items", 1, True):
            with self.subTest(items=items), self.assertRaises(ValueError):
                quote(items)

    def test_invalid_item_types_and_missing_fields(self):
        for item in (None, [], "widget", 1, True):
            with self.subTest(item=item), self.assertRaises(ValueError):
                quote([item])
        for missing in ("sku", "unit_price_cents", "quantity"):
            item = self.items[0].copy()
            del item[missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                quote([item])

    def test_invalid_item_field_values(self):
        invalid_values = {
            "sku": ("", None, 123, False, []),
            "unit_price_cents": (-1, 1.0, "1", None, True, False),
            "quantity": (0, -1, 1.0, "1", None, True, False),
        }
        for field, values in invalid_values.items():
            for value in values:
                item = {**self.items[0], field: value}
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    quote([item])

    def test_invalid_optional_arguments(self):
        for argument in ("discount_percent", "tax_percent", "shipping_cents"):
            values = [-1, 1.0, "1", None, True, False, []]
            if argument != "shipping_cents":
                values.append(101)
            for value in values:
                with self.subTest(argument=argument, value=value), self.assertRaises(ValueError):
                    quote(self.items, **{argument: value})

    def test_validation_failure_preserves_input(self):
        items = self.items + [{"sku": "bad", "unit_price_cents": 5, "quantity": 0}]
        original = copy.deepcopy(items)
        with self.assertRaises(ValueError):
            quote(items)
        self.assertEqual(items, original)

    def test_whitespace_sku_is_nonempty(self):
        items = [{"sku": " ", "unit_price_cents": 2, "quantity": 1}]
        self.assertEqual(quote(items)["total_cents"], 2)


if __name__ == "__main__":
    unittest.main()
