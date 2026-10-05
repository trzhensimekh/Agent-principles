"""Observable contract tests for the quote API."""

import copy
import unittest

from pricing import quote


class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.items = [{"sku": "widget", "unit_price_cents": 101, "quantity": 1}]

    def assertQuoteAmounts(self, result, expected):
        amounts = {key: value for key, value in result.items() if key != "lines"}
        self.assertEqual(amounts, expected)
        self.assertTrue(all(type(amount) is int for amount in amounts.values()))

    def test_defaults_and_result_shape(self):
        result = quote(self.items)
        self.assertQuoteAmounts(result, {
            "subtotal_cents": 101,
            "discount_cents": 0,
            "shipping_cents": 0,
            "tax_cents": 0,
            "total_cents": 101,
        })
        self.assertEqual(result["lines"], [{
            "sku": "widget", "subtotal_cents": 101, "discount_cents": 0,
            "net_cents": 101, "taxable": True,
        }])

    def test_rounding_and_tax_base_exclude_shipping(self):
        self.assertQuoteAmounts(quote(self.items, 50, 99, 50), {
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
        self.assertQuoteAmounts(quote(items, 50, 0, 50), {
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
        self.assertQuoteAmounts(quote(self.items, 100, 7, 100), {
            "subtotal_cents": 101,
            "discount_cents": 101,
            "shipping_cents": 7,
            "tax_cents": 0,
            "total_cents": 7,
        })
        self.assertEqual(quote(self.items, tax_percent=100)["tax_cents"], 101)

    def test_zero_subtotal_with_shipping(self):
        items = [{"sku": "free", "unit_price_cents": 0, "quantity": 1}]
        self.assertQuoteAmounts(quote(items, 50, 23, 100), {
            "subtotal_cents": 0,
            "discount_cents": 0,
            "shipping_cents": 23,
            "tax_cents": 0,
            "total_cents": 23,
        })

    def test_very_large_amounts_are_exact(self):
        items = [{"sku": "large", "unit_price_cents": 10**100 + 7, "quantity": 3}]
        result = quote(items, 33, 9, 25)
        self.assertQuoteAmounts(result, {
            "subtotal_cents": 3 * 10**100 + 21,
            "discount_cents": 99 * 10**98 + 6,
            "shipping_cents": 9,
            "tax_cents": 5025 * 10**96 + 3,
            "total_cents": 25125 * 10**96 + 27,
        })

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

    def test_selective_discount_and_tax_with_cap_and_taxable_shipping(self):
        items = [
            {"sku": "taxed", "unit_price_cents": 101, "quantity": 2},
            {"sku": "exempt", "unit_price_cents": 99, "quantity": 1,
             "taxable": False},
            {"sku": "full-price", "unit_price_cents": 50, "quantity": 1,
             "discountable": False},
        ]
        result = quote(items, 50, 11, 20, 100, True)
        self.assertQuoteAmounts(result, {
            "subtotal_cents": 351, "discount_cents": 100,
            "shipping_cents": 11, "tax_cents": 39, "total_cents": 301,
        })
        self.assertEqual(result["lines"], [
            {"sku": "taxed", "subtotal_cents": 202, "discount_cents": 67,
             "net_cents": 135, "taxable": True},
            {"sku": "exempt", "subtotal_cents": 99, "discount_cents": 33,
             "net_cents": 66, "taxable": False},
            {"sku": "full-price", "subtotal_cents": 50, "discount_cents": 0,
             "net_cents": 50, "taxable": True},
        ])

    def test_largest_remainder_precedes_input_order(self):
        items = [
            {"sku": "small", "unit_price_cents": 1, "quantity": 1},
            {"sku": "large", "unit_price_cents": 3, "quantity": 1},
        ]
        result = quote(items, 25)
        self.assertEqual([line["discount_cents"] for line in result["lines"]], [0, 1])

    def test_remainder_ties_keep_duplicate_skus_separate_and_affect_tax(self):
        items = [
            {"sku": "same", "unit_price_cents": 1, "quantity": 1,
             "taxable": False},
            {"sku": "same", "unit_price_cents": 1, "quantity": 1},
            {"sku": "same", "unit_price_cents": 1, "quantity": 1},
        ]
        result = quote(items, 100, 0, 100, 2)
        self.assertEqual([line["discount_cents"] for line in result["lines"]], [1, 1, 0])
        self.assertEqual(result["tax_cents"], 1)
        self.assertEqual(len(result["lines"]), 3)

    def test_zero_eligible_subtotal_and_zero_price_rows(self):
        items = [
            {"sku": "free", "unit_price_cents": 0, "quantity": 10},
            {"sku": "full-price", "unit_price_cents": 100, "quantity": 1,
             "discountable": False, "taxable": False},
        ]
        result = quote(items, 100, 17, 100, None, True)
        self.assertEqual(result["discount_cents"], 0)
        self.assertEqual(result["tax_cents"], 17)
        self.assertEqual([line["discount_cents"] for line in result["lines"]], [0, 0])
        items.append({"sku": "paid", "unit_price_cents": 1, "quantity": 1})
        self.assertEqual(
            [line["discount_cents"] for line in quote(items, 100)["lines"]], [0, 0, 1]
        )

    def test_cap_zero_and_cap_above_nominal_discount(self):
        self.assertEqual(quote(self.items, 50, discount_cap_cents=0)["discount_cents"], 0)
        self.assertEqual(quote(self.items, 50, discount_cap_cents=1000), quote(self.items, 50))

    def test_tax_rounds_once_across_rows_and_shipping(self):
        items = [
            {"sku": "a", "unit_price_cents": 1, "quantity": 1},
            {"sku": "b", "unit_price_cents": 1, "quantity": 1},
        ]
        self.assertEqual(quote(items, tax_percent=50)["tax_cents"], 1)
        self.assertEqual(quote(items[:1], 0, 1, 50, None, True)["tax_cents"], 1)

    def test_very_large_allocation_distinguishes_close_remainders(self):
        amount = 10**100
        items = [
            {"sku": "a", "unit_price_cents": amount, "quantity": 1},
            {"sku": "b", "unit_price_cents": amount + 1, "quantity": 1,
             "taxable": False},
        ]
        result = quote(items, 100, 0, 100, 1)
        self.assertEqual([line["discount_cents"] for line in result["lines"]], [0, 1])
        self.assertEqual(result["tax_cents"], amount)
        self.assertEqual(result["total_cents"], 3 * amount)

    def test_invalid_boolean_flags_and_cap(self):
        for field in ("discountable", "taxable"):
            for value in (0, 1, None, "true", [], {}):
                item = {**self.items[0], field: value}
                original = copy.deepcopy(item)
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    quote([item])
                self.assertEqual(item, original)
        for value in (0, 1, None, "false", [], {}):
            with self.subTest(shipping_taxable=value), self.assertRaises(ValueError):
                quote(self.items, shipping_taxable=value)
        for value in (-1, True, False, 1.0, "1", [], {}):
            with self.subTest(discount_cap_cents=value), self.assertRaises(ValueError):
                quote(self.items, discount_cap_cents=value)

    def test_lines_are_independent_of_inputs_and_other_calls(self):
        items = [{**self.items[0], "discountable": False, "taxable": False}]
        original = copy.deepcopy(items)
        expected = quote(items)
        first = quote(items)
        first["lines"][0]["sku"] = "changed"
        first["lines"][0]["taxable"] = True
        first["lines"].append({})
        self.assertEqual(items, original)
        self.assertEqual(quote(items), expected)

    def test_allocation_conserves_cents_and_never_exceeds_row_subtotals(self):
        for prices in ((0, 0, 0), (1, 1, 1), (3, 7, 11), (0, 100, 3)):
            for percent in (0, 1, 33, 67, 100):
                for cap in (None, 0, 1, 7, 1000):
                    items = [
                        {"sku": str(index), "unit_price_cents": price, "quantity": 1}
                        for index, price in enumerate(prices)
                    ]
                    with self.subTest(prices=prices, percent=percent, cap=cap):
                        result = quote(items, percent, discount_cap_cents=cap)
                        self.assertEqual(
                            sum(line["discount_cents"] for line in result["lines"]),
                            result["discount_cents"],
                        )
                        for line in result["lines"]:
                            self.assertGreaterEqual(line["discount_cents"], 0)
                            self.assertLessEqual(line["discount_cents"], line["subtotal_cents"])
                            self.assertEqual(
                                line["net_cents"], line["subtotal_cents"] - line["discount_cents"]
                            )


if __name__ == "__main__":
    unittest.main()
