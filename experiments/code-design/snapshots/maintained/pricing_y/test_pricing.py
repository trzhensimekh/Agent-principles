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
            "lines": [{"sku": "A", "subtotal_cents": 303,
                       "discount_cents": 0, "net_cents": 303, "taxable": True}],
        })

    def test_rounding_and_shipping_not_taxable(self):
        self.assertEqual(quote([self.item], 17, 99, 7), {
            "subtotal_cents": 303,
            "discount_cents": 51,
            "shipping_cents": 99,
            "tax_cents": 17,
            "total_cents": 368,
            "lines": [{"sku": "A", "subtotal_cents": 303,
                       "discount_cents": 51, "net_cents": 252, "taxable": True}],
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
            "lines": [{"sku": "A", "subtotal_cents": 0,
                       "discount_cents": 0, "net_cents": 0, "taxable": True}],
        })

    def test_percentage_boundaries(self):
        self.assertEqual(quote([self.item], 100, 55, 100), {
            "subtotal_cents": 303,
            "discount_cents": 303,
            "shipping_cents": 55,
            "tax_cents": 0,
            "total_cents": 55,
            "lines": [{"sku": "A", "subtotal_cents": 303,
                       "discount_cents": 303, "net_cents": 0, "taxable": True}],
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
            "lines": [{"sku": "large", "subtotal_cents": 100 * magnitude + 100,
                       "discount_cents": 37 * magnitude + 37,
                       "net_cents": 63 * magnitude + 63, "taxable": True}],
        })
        self.assertTrue(all(type(value) is int for key, value in result.items()
                            if key != "lines"))

    def test_inputs_preserved_and_calls_independent(self):
        items = [dict(self.item, metadata={"tags": ["sale"]})]
        original = copy.deepcopy(items)
        first = quote(items, 17, 99, 7)
        expected = copy.deepcopy(first)
        first["total_cents"] = -1
        first["lines"][0]["net_cents"] = -1
        first["lines"].append({"sku": "injected"})
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


class SelectivePricingTests(unittest.TestCase):
    @staticmethod
    def item(price, sku="A", **flags):
        return {"sku": sku, "unit_price_cents": price, "quantity": 1, **flags}

    def test_selective_discount_cap_and_tax_exemption(self):
        items = [
            self.item(101),
            self.item(202, taxable=False),
            self.item(300, discountable=False),
        ]
        result = quote(items, 50, 9, 10, 5, True)
        self.assertEqual(result, {
            "subtotal_cents": 603, "discount_cents": 5, "shipping_cents": 9,
            "tax_cents": 40, "total_cents": 647,
            "lines": [
                {"sku": "A", "subtotal_cents": 101, "discount_cents": 2,
                 "net_cents": 99, "taxable": True},
                {"sku": "A", "subtotal_cents": 202, "discount_cents": 3,
                 "net_cents": 199, "taxable": False},
                {"sku": "A", "subtotal_cents": 300, "discount_cents": 0,
                 "net_cents": 300, "taxable": True},
            ],
        })

    def test_largest_remainder_wins_before_input_order(self):
        items = [self.item(1), self.item(3), self.item(2)]
        result = quote(items, discount_percent=100, discount_cap_cents=2)
        self.assertEqual([line["discount_cents"] for line in result["lines"]],
                         [0, 1, 1])

    def test_ties_follow_input_order_and_change_tax_base(self):
        items = [self.item(1, taxable=False), self.item(1), self.item(1)]
        result = quote(items, discount_percent=100, discount_cap_cents=2,
                       tax_percent=100)
        self.assertEqual([line["discount_cents"] for line in result["lines"]],
                         [1, 1, 0])
        self.assertEqual(result["tax_cents"], 1)
        # Repeated SKUs stay separate, and reversing rows changes the tie winner.
        reversed_result = quote(list(reversed(items)), 100, 0, 100, 2)
        self.assertEqual(reversed_result["tax_cents"], 0)

    def test_zero_eligible_subtotal_and_zero_price_rows(self):
        cases = [
            [self.item(5, discountable=False)],
            [self.item(0)],
            [self.item(0), self.item(5, discountable=False)],
        ]
        for items in cases:
            with self.subTest(items=items):
                result = quote(items, discount_percent=100)
                self.assertEqual(result["discount_cents"], 0)
                self.assertTrue(all(line["discount_cents"] == 0
                                    for line in result["lines"]))
        result = quote([self.item(0), self.item(1), self.item(0), self.item(1)],
                       discount_percent=50)
        self.assertEqual([line["discount_cents"] for line in result["lines"]],
                         [0, 1, 0, 0])

    def test_cap_is_applied_after_percentage_rounding(self):
        for cap, expected in ((None, 51), (0, 0), (50, 50), (51, 51), (999, 51)):
            with self.subTest(cap=cap):
                result = quote([self.item(303)], 17, discount_cap_cents=cap)
                self.assertEqual(result["discount_cents"], expected)
                self.assertEqual(result["lines"][0]["net_cents"], 303 - expected)

    def test_tax_is_rounded_once_after_shipping(self):
        result = quote([self.item(9), self.item(9), self.item(99, taxable=False)],
                       shipping_cents=2, tax_percent=10, shipping_taxable=True)
        self.assertEqual(result["tax_cents"], 2)
        result = quote([self.item(9), self.item(9)], tax_percent=10)
        self.assertEqual(result["tax_cents"], 1)

    def test_shipping_can_be_taxable_when_items_are_exempt_or_fully_discounted(self):
        for items, percent in (([self.item(100, taxable=False)], 0),
                               ([self.item(100)], 100)):
            for taxable, expected in ((False, 0), (True, 7)):
                with self.subTest(items=items, shipping_taxable=taxable):
                    result = quote(items, percent, 99, 8,
                                   shipping_taxable=taxable)
                    self.assertEqual(result["tax_cents"], expected)

    def test_large_remainders_remain_distinguishable(self):
        magnitude = 10 ** 100
        result = quote([self.item(magnitude + 1, taxable=False),
                        self.item(magnitude + 2)], 50, magnitude, 37, 1, True)
        self.assertEqual([line["discount_cents"] for line in result["lines"]],
                         [0, 1])
        self.assertEqual(result["tax_cents"], 74 * (magnitude // 100))
        self.assertEqual(result["total_cents"],
                         3 * magnitude + 2 + 74 * (magnitude // 100))

    def test_allocations_are_bounded_and_conserve_discount(self):
        items = [self.item(0), self.item(1), self.item(2, discountable=False),
                 self.item(3), self.item(7, taxable=False)]
        for percent in (0, 1, 17, 33, 50, 99, 100):
            for cap in (None, 0, 1, 2, 9, 100):
                with self.subTest(percent=percent, cap=cap):
                    result = quote(items, percent, discount_cap_cents=cap)
                    lines = result["lines"]
                    self.assertEqual(sum(line["discount_cents"] for line in lines),
                                     result["discount_cents"])
                    self.assertEqual(sum(line["net_cents"] for line in lines),
                                     result["subtotal_cents"] - result["discount_cents"])
                    self.assertEqual(lines[2]["discount_cents"], 0)
                    for line in lines:
                        self.assertGreaterEqual(line["discount_cents"], 0)
                        self.assertLessEqual(line["discount_cents"],
                                             line["subtotal_cents"])

    def test_new_flags_and_nested_metadata_are_preserved(self):
        items = [self.item(11, discountable=True, taxable=False),
                 self.item(19, discountable=False, metadata={"tags": ["sale"]})]
        original = copy.deepcopy(items)
        result = quote(items, 50, 3, 10, 2, True)
        expected = copy.deepcopy(result)
        result["lines"][0]["taxable"] = True
        self.assertEqual(quote(items, 50, 3, 10, 2, True), expected)
        self.assertEqual(items, original)

    def test_invalid_item_flags_preserve_inputs(self):
        for flag in ("discountable", "taxable"):
            for value in (None, 0, 1, -1, 1.0, "true", [], {}):
                items = [self.item(10), self.item(20, **{flag: value})]
                original = copy.deepcopy(items)
                with self.subTest(flag=flag, value=value), self.assertRaises(ValueError):
                    quote(items)
                self.assertEqual(items, original)

    def test_invalid_new_quote_arguments(self):
        invalid = {
            "discount_cap_cents": (-1, True, False, 0.0, "1", [], {}),
            "shipping_taxable": (None, 0, 1, -1, 0.0, "true", [], {}),
        }
        for key, values in invalid.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    quote([self.item(10)], **{key: value})


if __name__ == "__main__":
    unittest.main()
