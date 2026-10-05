"""Acceptance tests derived only from the two pricing task specifications.

The evaluator supplies a synthetic ``candidate`` module with ``module`` set to
the pricing module under test. Stage 2 must run both test classes.
"""

import copy
import unittest

import candidate


def item(sku="a", price=100, quantity=1, **flags):
    return dict(sku=sku, unit_price_cents=price, quantity=quantity, **flags)


class PricingAssertions:
    def quote(self, *args, **kwargs):
        return candidate.module.quote(*args, **kwargs)

    def assert_money(self, result, subtotal, discount, shipping, tax, total):
        self.assertIsInstance(result, dict)
        expected = dict(subtotal_cents=subtotal, discount_cents=discount,
                        shipping_cents=shipping, tax_cents=tax, total_cents=total)
        for key, amount in expected.items():
            self.assertIn(key, result)
            self.assertIs(type(result[key]), int, key)
            self.assertEqual(result[key], amount, key)

    def assert_lines(self, result, expected):
        self.assertIn("lines", result)
        self.assertIsInstance(result["lines"], list)
        self.assertEqual(len(result["lines"]), len(expected))
        for actual, (sku, subtotal, discount, net, taxable) in zip(result["lines"], expected):
            self.assertIsInstance(actual, dict)
            wanted = dict(sku=sku, subtotal_cents=subtotal,
                          discount_cents=discount, net_cents=net, taxable=taxable)
            for key, value in wanted.items():
                self.assertIn(key, actual)
                self.assertEqual(actual[key], value, key)
            for key in ("subtotal_cents", "discount_cents", "net_cents"):
                self.assertIs(type(actual[key]), int, key)
            self.assertIs(type(actual["taxable"]), bool)


class PricingStage1Tests(PricingAssertions, unittest.TestCase):
    def test_default_quote(self):
        self.assert_money(self.quote([item(price=129, quantity=3)]), 387, 0, 0, 0, 387)

    def test_discount_tax_floor_and_untaxed_shipping(self):
        result = self.quote([item(price=101, quantity=3)], 17, 19, 13)
        self.assert_money(result, 303, 51, 19, 32, 303)

    def test_percent_boundaries(self):
        for discount in (0, 100):
            for tax in (0, 100):
                with self.subTest(discount=discount, tax=tax):
                    net = 251 if discount == 0 else 0
                    expected_tax = net if tax == 100 else 0
                    self.assert_money(self.quote([item(price=251)], discount, 7, tax),
                                      251, 251 - net, 7, expected_tax, net + 7 + expected_tax)

    def test_repeated_skus_and_zero_prices(self):
        rows = [item("x", 0, 9), item("x", 7, 3), item("x", 11, 2)]
        self.assert_money(self.quote(rows, 33, 2, 9), 43, 14, 2, 2, 33)

    def test_all_zero_rows(self):
        self.assert_money(self.quote([item(price=0), item(price=0, quantity=99)], 100, 99, 100),
                          0, 0, 99, 0, 99)

    def test_huge_integer_arithmetic(self):
        price = 10 ** 100 + 137
        quantity = 10 ** 25 + 3
        subtotal = price * quantity
        discount = subtotal * 37 // 100
        tax = (subtotal - discount) * 83 // 100
        shipping = 10 ** 80 + 19
        self.assert_money(self.quote([item(price=price, quantity=quantity)], 37, shipping, 83),
                          subtotal, discount, shipping, tax, subtotal - discount + shipping + tax)

    def test_input_is_not_mutated(self):
        rows = [item("x", 19, 3), item("x", 0, 2)]
        before = copy.deepcopy(rows)
        self.quote(rows, 23, 4, 17)
        self.assertEqual(rows, before)

    def test_calls_are_independent_and_deterministic(self):
        rows = [item(price=47, quantity=2)]
        first = self.quote(rows, 19, 13, 7)
        saved = copy.deepcopy(first)
        self.quote([item(price=0)], 100, 500, 100)
        self.assertEqual(first, saved)
        self.assertEqual(self.quote(rows, 19, 13, 7), saved)
        first["total_cents"] = -1
        self.assert_money(self.quote(rows, 19, 13, 7), 94, 17, 13, 5, 95)

    def test_nonempty_sku_including_whitespace(self):
        self.assert_money(self.quote([item(" ", 1), item("é", 2)]), 3, 0, 0, 0, 3)

    def test_invalid_items_container(self):
        for rows in (None, [], (), (item(),), {}, "items", 42, True):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    self.quote(rows)

    def test_invalid_row_and_missing_required_fields(self):
        rows = [None, [], "a", 1, True, {}, {"sku": "a"},
                {"sku": "a", "unit_price_cents": 1},
                {"sku": "a", "quantity": 1},
                {"unit_price_cents": 1, "quantity": 1}]
        for bad in rows:
            with self.subTest(row=bad):
                with self.assertRaises(ValueError):
                    self.quote([item(), bad])

    def test_invalid_sku(self):
        for sku in ("", None, 1, True, [], b"a"):
            with self.subTest(sku=sku):
                with self.assertRaises(ValueError):
                    self.quote([item(sku=sku)])

    def test_invalid_unit_prices_and_quantities(self):
        for key, values in (("unit_price_cents", (-1, True, False, 1.0, "1", None)),
                            ("quantity", (0, -1, True, False, 1.0, "1", None))):
            for value in values:
                with self.subTest(key=key, value=value):
                    row = item()
                    row[key] = value
                    with self.assertRaises(ValueError):
                        self.quote([row])

    def test_invalid_percentages(self):
        for key in ("discount_percent", "tax_percent"):
            for value in (-1, 101, True, False, 0.0, 99.0, "10", None, [], float("nan")):
                with self.subTest(key=key, value=value):
                    with self.assertRaises(ValueError):
                        self.quote([item()], **{key: value})

    def test_invalid_shipping(self):
        for shipping in (-1, True, False, 0.0, "0", None, [], float("inf")):
            with self.subTest(shipping=shipping):
                with self.assertRaises(ValueError):
                    self.quote([item()], shipping_cents=shipping)


class PricingStage2Tests(PricingAssertions, unittest.TestCase):
    def test_default_lines(self):
        result = self.quote([item("a", 9, 2), item("b", 2, 3)])
        self.assert_money(result, 24, 0, 0, 0, 24)
        self.assert_lines(result, [("a", 18, 0, 18, True), ("b", 6, 0, 6, True)])

    def test_discount_eligible_subtotal_and_cap(self):
        rows = [item("a", 100, discountable=False), item("b", 300)]
        result = self.quote(rows, 10, 0, 10, discount_cap_cents=25)
        self.assert_money(result, 400, 25, 0, 37, 412)
        self.assert_lines(result, [("a", 100, 0, 100, True), ("b", 300, 25, 275, True)])

    def test_cap_none_zero_binding_and_nonbinding(self):
        for cap, discount in ((None, 25), (0, 0), (7, 7), (25, 25), (99, 25)):
            with self.subTest(cap=cap):
                result = self.quote([item(price=101)], 25, discount_cap_cents=cap)
                self.assert_money(result, 101, discount, 0, 0, 101 - discount)
                self.assert_lines(result, [("a", 101, discount, 101 - discount, True)])

    def test_largest_remainders_not_independent_rounding(self):
        result = self.quote([item("a", 1), item("b", 2), item("c", 3)],
                            100, discount_cap_cents=2)
        self.assert_money(result, 6, 2, 0, 0, 4)
        self.assert_lines(result, [("a", 1, 0, 1, True), ("b", 2, 1, 1, True),
                                   ("c", 3, 1, 2, True)])

    def test_ties_use_original_order_and_keep_repeated_skus(self):
        rows = [item("z", 1), item("a", 1), item("z", 1)]
        result = self.quote(rows, 100, discount_cap_cents=2)
        self.assert_money(result, 3, 2, 0, 0, 1)
        self.assert_lines(result, [("z", 1, 1, 0, True), ("a", 1, 1, 0, True),
                                   ("z", 1, 0, 1, True)])

    def test_tie_across_tax_status_changes_tax(self):
        result = self.quote([item("exempt", 1, taxable=False), item("taxed", 1)],
                            50, tax_percent=100)
        self.assert_money(result, 2, 1, 0, 1, 2)
        self.assert_lines(result, [("exempt", 1, 1, 0, False), ("taxed", 1, 0, 1, True)])

    def test_mixed_flags_with_taxable_shipping(self):
        rows = [item("a", 5), item("b", 7, taxable=False),
                item("c", 4, discountable=False)]
        result = self.quote(rows, 50, 3, 33, shipping_taxable=True)
        self.assert_money(result, 16, 6, 3, 2, 15)
        self.assert_lines(result, [("a", 5, 3, 2, True), ("b", 7, 3, 4, False),
                                   ("c", 4, 0, 4, True)])

    def test_shipping_tax_flag_and_exempt_merchandise(self):
        for taxable, tax in ((False, 0), (True, 5)):
            with self.subTest(shipping_taxable=taxable):
                result = self.quote([item(price=100, taxable=False)], 10, 11, 50,
                                    shipping_taxable=taxable)
                self.assert_money(result, 100, 10, 11, tax, 101 + tax)
                self.assert_lines(result, [("a", 100, 10, 90, False)])

    def test_tax_is_rounded_once(self):
        result = self.quote([item("a", 1), item("b", 1)], tax_percent=50)
        self.assert_money(result, 2, 0, 0, 1, 3)
        result = self.quote([item(price=1)], shipping_cents=1, tax_percent=50,
                            shipping_taxable=True)
        self.assert_money(result, 1, 0, 1, 1, 3)

    def test_zero_eligible_subtotal(self):
        rows = [item("a", 17, discountable=False), item("b", 0),
                item("c", 0, taxable=False)]
        result = self.quote(rows, 100, 3, 100, discount_cap_cents=99)
        self.assert_money(result, 17, 0, 3, 17, 37)
        self.assert_lines(result, [("a", 17, 0, 17, True), ("b", 0, 0, 0, True),
                                   ("c", 0, 0, 0, False)])
        self.assert_money(self.quote([item(price=0)], 100, 3, 100,
                                     shipping_taxable=True), 0, 0, 3, 3, 6)

    def test_zero_rows_and_ineligible_rows_cannot_take_remainder(self):
        rows = [item("zero", 0), item("ineligible", 100, discountable=False),
                item("first", 1), item("second", 1)]
        result = self.quote(rows, 50)
        self.assert_money(result, 102, 1, 0, 0, 101)
        self.assert_lines(result, [("zero", 0, 0, 0, True),
                                   ("ineligible", 100, 0, 100, True),
                                   ("first", 1, 1, 0, True), ("second", 1, 0, 1, True)])

    def test_full_discount_never_exceeds_row_subtotal(self):
        rows = [item("a", 0), item("b", 1), item("c", 3, 7)]
        result = self.quote(rows, 100, 2, 100, discount_cap_cents=10 ** 90,
                            shipping_taxable=True)
        self.assert_money(result, 22, 22, 2, 2, 4)
        self.assert_lines(result, [("a", 0, 0, 0, True), ("b", 1, 1, 0, True),
                                   ("c", 21, 21, 0, True)])

    def test_huge_values_preserve_fractional_remainder_order(self):
        n = 10 ** 100 + 1
        rows = [item("a", n), item("b", n + 1, taxable=False), item("c", n + 2)]
        result = self.quote(rows, 99, 13, 37, discount_cap_cents=7, shipping_taxable=True)
        tax = (2 * n + 10) * 37 // 100
        self.assert_money(result, 3 * n + 3, 7, 13, tax, 3 * n + 9 + tax)
        self.assert_lines(result, [("a", n, 2, n - 2, True),
                                   ("b", n + 1, 2, n - 1, False),
                                   ("c", n + 2, 3, n - 1, True)])

    def test_huge_discount_allocation_with_known_result(self):
        n = 10 ** 100
        rows = [item("a", 2 * n + 1), item("b", 2 * n + 1), item("c", 2 * n + 1)]
        result = self.quote(rows, 50)
        self.assert_money(result, 6 * n + 3, 3 * n + 1, 0, 0, 3 * n + 2)
        self.assert_lines(result, [("a", 2 * n + 1, n + 1, n, True),
                                   ("b", 2 * n + 1, n, n + 1, True),
                                   ("c", 2 * n + 1, n, n + 1, True)])

    def test_new_arguments_can_be_positional(self):
        result = self.quote([item()], 20, 5, 10, 3, True)
        self.assert_money(result, 100, 3, 5, 10, 112)
        self.assert_lines(result, [("a", 100, 3, 97, True)])

    def test_success_and_failure_never_mutate_caller_rows(self):
        rows = [item("a", 3), item("a", 4, discountable=False, taxable=False)]
        before = copy.deepcopy(rows)
        result = self.quote(rows, 37, 11, 13, 1, True)
        self.assertEqual(rows, before)
        result["lines"][0]["sku"] = "changed"
        self.assertEqual(rows, before)
        rows.append(item("bad", 2, taxable=1))
        before = copy.deepcopy(rows)
        with self.assertRaises(ValueError):
            self.quote(rows)
        self.assertEqual(rows, before)

    def test_invalid_item_flags_even_when_financially_irrelevant(self):
        for flag in ("discountable", "taxable"):
            for value in (0, 1, None, "true", "false", [], {}, 0.0, 1.0):
                with self.subTest(flag=flag, value=value):
                    with self.assertRaises(ValueError):
                        self.quote([item(price=0, **{flag: value})])

    def test_invalid_discount_caps(self):
        for cap in (-1, True, False, 0.0, 1.0, "0", [], {}, float("inf")):
            with self.subTest(cap=cap):
                with self.assertRaises(ValueError):
                    self.quote([item(price=0)], discount_cap_cents=cap)

    def test_invalid_shipping_taxable(self):
        for value in (0, 1, None, "true", "false", [], {}, 0.0, 1.0):
            with self.subTest(shipping_taxable=value):
                with self.assertRaises(ValueError):
                    self.quote([item(price=0)], shipping_taxable=value)

