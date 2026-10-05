import unittest

from inventory import Conflict, Inventory, OutOfStock


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()

    def test_empty_inventory_and_independent_instances(self):
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertIsNone(self.inventory.get_reservation("unknown"))
        self.assertFalse(self.inventory.cancel("unknown"))
        self.inventory.stock("widget", 2)
        self.assertEqual(Inventory().available("widget"), 0)

    def test_stock_accumulates_and_reservations_are_independent(self):
        self.inventory.stock("widget", 5)
        self.inventory.stock("widget", 2)
        self.inventory.stock("other", 8)
        self.assertEqual(
            self.inventory.reserve("first", "widget", 3),
            {"request_id": "first", "sku": "widget", "quantity": 3, "status": "reserved"},
        )
        self.inventory.reserve("second", "widget", 4)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertEqual(self.inventory.available("other"), 8)
        self.inventory.stock("widget", 1)
        self.assertTrue(self.inventory.cancel("first"))
        self.assertEqual(self.inventory.available("widget"), 4)
        self.assertEqual(self.inventory.get_reservation("second")["status"], "reserved")

    def test_out_of_stock_does_not_consume_request_id(self):
        self.assertTrue(issubclass(OutOfStock, ValueError))
        self.inventory.stock("widget", 2)
        for sku, quantity in (("unknown", 1), ("widget", 3)):
            with self.subTest(sku=sku):
                with self.assertRaises(OutOfStock):
                    self.inventory.reserve("retry", sku, quantity)
                self.assertIsNone(self.inventory.get_reservation("retry"))
                self.assertFalse(self.inventory.cancel("retry"))
                self.assertEqual(self.inventory.available("widget"), 2)
                self.assertEqual(self.inventory.available("unknown"), 0)
        self.inventory.stock("widget", 1)
        self.assertEqual(self.inventory.reserve("retry", "widget", 3)["status"], "reserved")
        self.assertEqual(self.inventory.available("widget"), 0)

    def test_successful_replay_and_cancelled_replay(self):
        self.inventory.stock("widget", 3)
        original = self.inventory.reserve("request", "widget", 3)
        self.assertEqual(self.inventory.reserve("request", "widget", 3), original)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertTrue(self.inventory.cancel("request"))
        self.assertFalse(self.inventory.cancel("request"))
        self.assertEqual(self.inventory.available("widget"), 3)
        cancelled = dict(original, status="cancelled")
        self.assertEqual(self.inventory.reserve("request", "widget", 3), cancelled)
        self.assertEqual(self.inventory.get_reservation("request"), cancelled)
        self.assertEqual(self.inventory.available("widget"), 3)
        self.assertEqual(original["status"], "reserved")

    def test_conflicts_before_and_after_cancellation(self):
        self.assertTrue(issubclass(Conflict, ValueError))
        self.inventory.stock("widget", 3)
        self.inventory.reserve("request", "widget", 3)
        for cancelled in (False, True):
            if cancelled:
                self.inventory.cancel("request")
            before = self.inventory.get_reservation("request")
            available = self.inventory.available("widget")
            for sku, quantity in (("other", 3), ("widget", 1), ("widget", 4)):
                with self.subTest(cancelled=cancelled, sku=sku, quantity=quantity):
                    with self.assertRaises(Conflict):
                        self.inventory.reserve("request", sku, quantity)
                    self.assertEqual(self.inventory.get_reservation("request"), before)
                    self.assertEqual(self.inventory.available("widget"), available)
                    self.assertEqual(self.inventory.available("other"), 0)

    def test_returned_dictionaries_are_defensive_copies(self):
        self.inventory.stock("widget", 4)
        expected = {"request_id": "request", "sku": "widget", "quantity": 2, "status": "reserved"}
        created = self.inventory.reserve("request", "widget", 2)
        replayed = self.inventory.reserve("request", "widget", 2)
        fetched = self.inventory.get_reservation("request")
        for snapshot in (created, replayed, fetched):
            snapshot.clear()
            snapshot.update({"sku": "other", "quantity": 100, "status": "cancelled"})
            self.assertEqual(self.inventory.get_reservation("request"), expected)
            self.assertEqual(self.inventory.available("widget"), 2)
        self.assertTrue(self.inventory.cancel("request"))
        self.assertEqual(self.inventory.available("widget"), 4)
        cancelled = self.inventory.reserve("request", "widget", 2)
        cancelled["status"] = "reserved"
        self.assertEqual(self.inventory.get_reservation("request")["status"], "cancelled")

    def test_invalid_strings_are_rejected_across_entry_points(self):
        self.inventory.stock("widget", 3)
        self.inventory.reserve("request", "widget", 1)
        expected = self.inventory.get_reservation("request")
        for invalid in ("", None, 0, True, [], {}, b"widget"):
            operations = (
                lambda: self.inventory.stock(invalid, 2),
                lambda: self.inventory.available(invalid),
                lambda: self.inventory.reserve(invalid, "widget", 1),
                lambda: self.inventory.reserve("new", invalid, 1),
                lambda: self.inventory.cancel(invalid),
                lambda: self.inventory.get_reservation(invalid),
            )
            for operation in operations:
                with self.subTest(invalid=invalid, operation=operation):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.inventory.available("widget"), 2)
                    self.assertEqual(self.inventory.get_reservation("request"), expected)
                    self.assertIsNone(self.inventory.get_reservation("new"))
        self.inventory.reserve("new", "widget", 1)
        self.assertEqual(self.inventory.available("widget"), 1)

    def test_invalid_quantities_are_rejected_without_state_changes(self):
        self.inventory.stock("widget", 3)
        self.inventory.reserve("existing", "widget", 1)
        expected = self.inventory.get_reservation("existing")
        for invalid in (0, -1, True, False, 1.0, "1", None, [], {}):
            operations = (
                lambda: self.inventory.stock("widget", invalid),
                lambda: self.inventory.reserve("new", "widget", invalid),
                lambda: self.inventory.reserve("existing", "widget", invalid),
            )
            for operation in operations:
                with self.subTest(invalid=invalid, operation=operation):
                    with self.assertRaises(ValueError) as error:
                        operation()
                    self.assertIs(type(error.exception), ValueError)
                    self.assertEqual(self.inventory.available("widget"), 2)
                    self.assertEqual(self.inventory.get_reservation("existing"), expected)
                    self.assertIsNone(self.inventory.get_reservation("new"))
        self.inventory.reserve("new", "widget", 2)
        self.assertEqual(self.inventory.available("widget"), 0)

    def test_strings_are_nonempty_without_normalization(self):
        self.inventory.stock(" ", 1)
        self.inventory.stock("Widget", 2)
        self.inventory.reserve(" ", " ", 1)
        self.assertEqual(self.inventory.available(" "), 0)
        self.assertEqual(self.inventory.available("Widget"), 2)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertTrue(self.inventory.cancel(" "))


if __name__ == "__main__":
    unittest.main()
