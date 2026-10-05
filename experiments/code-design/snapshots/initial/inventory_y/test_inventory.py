import unittest

from inventory import Conflict, Inventory, OutOfStock


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def test_empty_inventory_and_independent_instances(self):
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertIsNone(self.inventory.get_reservation("missing"))
        self.assertIs(self.inventory.cancel("missing"), False)
        self.inventory.stock("widget", 3)
        self.assertEqual(Inventory().available("widget"), 0)

    def test_stock_adds_and_skus_are_independent(self):
        self.inventory.stock("widget", 5)
        self.inventory.stock("widget", 3)
        self.inventory.stock("gadget", 2)
        self.assertEqual(self.inventory.available("widget"), 8)
        self.assertEqual(self.inventory.available("gadget"), 2)

    def test_reservation_snapshot_and_exact_replay_at_zero_stock(self):
        self.inventory.stock("widget", 3)
        expected = {
            "request_id": "order-1",
            "sku": "widget",
            "quantity": 3,
            "status": "reserved",
        }
        self.assertEqual(self.inventory.reserve("order-1", "widget", 3), expected)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertEqual(self.inventory.reserve("order-1", "widget", 3), expected)
        self.assertEqual(self.inventory.get_reservation("order-1"), expected)
        self.assertEqual(self.inventory.available("widget"), 0)

    def test_out_of_stock_preserves_state_and_allows_retry(self):
        self.inventory.stock("widget", 3)
        self.inventory.reserve("first", "widget", 2)
        before = self.inventory.get_reservation("first")
        for sku, quantity in [("widget", 2), ("unknown", 1)]:
            with self.subTest(sku=sku):
                with self.assertRaises(OutOfStock):
                    self.inventory.reserve("retry", sku, quantity)
                self.assertIsNone(self.inventory.get_reservation("retry"))
                self.assertEqual(self.inventory.available("widget"), 1)
                self.assertEqual(self.inventory.available("unknown"), 0)
                self.assertEqual(self.inventory.get_reservation("first"), before)
        self.inventory.stock("unknown", 1)
        self.assertEqual(
            self.inventory.reserve("retry", "unknown", 1)["status"], "reserved"
        )

    def test_conflicting_replays_before_and_after_cancellation(self):
        self.inventory.stock("widget", 5)
        self.inventory.reserve("order-1", "widget", 2)
        for cancelled in (False, True):
            if cancelled:
                self.inventory.cancel("order-1")
            expected = self.inventory.get_reservation("order-1")
            balance = self.inventory.available("widget")
            for sku, quantity in [("other", 2), ("widget", 3)]:
                with self.subTest(cancelled=cancelled, sku=sku, quantity=quantity):
                    with self.assertRaises(Conflict):
                        self.inventory.reserve("order-1", sku, quantity)
                    self.assertEqual(self.inventory.get_reservation("order-1"), expected)
                    self.assertEqual(self.inventory.available("widget"), balance)
                    self.assertEqual(self.inventory.available("other"), 0)

    def test_cancel_releases_once_and_replay_does_not_resurrect(self):
        self.inventory.stock("widget", 8)
        self.inventory.reserve("first", "widget", 3)
        self.inventory.reserve("second", "widget", 4)
        self.inventory.stock("widget", 2)
        self.assertEqual(self.inventory.available("widget"), 3)
        self.assertIs(self.inventory.cancel("first"), True)
        self.assertEqual(self.inventory.available("widget"), 6)
        self.assertIs(self.inventory.cancel("first"), False)
        cancelled = self.inventory.reserve("first", "widget", 3)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.inventory.get_reservation("first"), cancelled)
        self.assertEqual(self.inventory.available("widget"), 6)
        self.assertEqual(self.inventory.get_reservation("second")["status"], "reserved")
        self.assertIs(self.inventory.cancel("second"), True)
        self.assertEqual(self.inventory.available("widget"), 10)

    def test_unknown_cancel_does_not_consume_id(self):
        self.assertIs(self.inventory.cancel("new"), False)
        self.inventory.stock("widget", 1)
        self.assertEqual(self.inventory.reserve("new", "widget", 1)["status"], "reserved")

    def test_snapshots_are_defensive_and_do_not_change_over_time(self):
        self.inventory.stock("widget", 5)
        original = self.inventory.reserve("order-1", "widget", 2)
        expected = original.copy()
        for snapshot in (
            self.inventory.reserve("order-1", "widget", 2),
            self.inventory.get_reservation("order-1"),
        ):
            snapshot.clear()
            snapshot.update(request_id="changed", sku="other", quantity=100, status="cancelled")
            self.assertEqual(self.inventory.get_reservation("order-1"), expected)
            self.assertEqual(self.inventory.available("widget"), 3)
        self.inventory.cancel("order-1")
        self.assertEqual(original, expected)
        cancelled = self.inventory.reserve("order-1", "widget", 2)
        cancelled["status"] = "reserved"
        self.assertEqual(self.inventory.get_reservation("order-1")["status"], "cancelled")
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_sku_validation_across_public_entry_points(self):
        self.inventory.stock("widget", 4)
        for invalid in ("", None, 1, True, [], {}):
            operations = (
                lambda: self.inventory.stock(invalid, 1),
                lambda: self.inventory.available(invalid),
                lambda: self.inventory.reserve("new", invalid, 1),
            )
            for operation in operations:
                with self.subTest(sku=invalid, operation=operation):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.inventory.available("widget"), 4)
                    self.assertIsNone(self.inventory.get_reservation("new"))
        self.assertEqual(self.inventory.reserve("new", "widget", 1)["status"], "reserved")

    def test_request_id_validation_across_public_entry_points(self):
        self.inventory.stock("widget", 4)
        for invalid in ("", None, 1, True, [], {}):
            operations = (
                lambda: self.inventory.reserve(invalid, "widget", 1),
                lambda: self.inventory.cancel(invalid),
                lambda: self.inventory.get_reservation(invalid),
            )
            for operation in operations:
                with self.subTest(request_id=invalid, operation=operation):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.inventory.available("widget"), 4)

    def test_quantity_validation_is_atomic_for_stock_and_reserve(self):
        self.inventory.stock("widget", 4)
        expected = self.inventory.reserve("existing", "widget", 1)
        for invalid in (0, -1, True, False, 1.0, "1", None, [], {}):
            operations = (
                lambda: self.inventory.stock("widget", invalid),
                lambda: self.inventory.stock("new-sku", invalid),
                lambda: self.inventory.reserve("new", "widget", invalid),
                lambda: self.inventory.reserve("existing", "widget", invalid),
            )
            for operation in operations:
                with self.subTest(quantity=invalid, operation=operation):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.inventory.available("widget"), 3)
                    self.assertEqual(self.inventory.available("new-sku"), 0)
                    self.assertEqual(self.inventory.get_reservation("existing"), expected)
                    self.assertIsNone(self.inventory.get_reservation("new"))
        self.assertEqual(self.inventory.reserve("new", "widget", 1)["status"], "reserved")

    def test_nonempty_identifiers_are_not_trimmed_or_normalized(self):
        self.inventory.stock(" ", 2)
        self.inventory.reserve(" ", " ", 1)
        self.assertEqual(self.inventory.available(" "), 1)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertIs(self.inventory.cancel(" "), True)

    def test_domain_exceptions_are_value_errors(self):
        self.assertTrue(issubclass(OutOfStock, ValueError))
        self.assertTrue(issubclass(Conflict, ValueError))


if __name__ == "__main__":
    unittest.main()
