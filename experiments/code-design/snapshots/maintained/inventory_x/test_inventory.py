import unittest
from unittest.mock import patch

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
            {"request_id": "first", "sku": "widget", "quantity": 3, "status": "reserved", "expires_at": None},
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
        expected = {"request_id": "request", "sku": "widget", "quantity": 2, "status": "reserved", "expires_at": None}
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
                lambda: self.inventory.renew(invalid, 5),
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


class FakeClock:
    def __init__(self, now=100):
        self.now = now

    def __call__(self):
        return self.now


class ExpirationTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.inventory = Inventory(self.clock)
        self.inventory.stock("widget", 5)

    def test_default_clock_is_monotonic(self):
        with patch("inventory.time.monotonic", return_value=20):
            inventory = Inventory()
            inventory.stock("widget", 1)
            self.assertEqual(inventory.reserve("request", "widget", 1, 5)["expires_at"], 25)

    def test_expiry_boundary_and_stock_release_exactly_once(self):
        original = self.inventory.reserve("request", "widget", 3, 5)
        self.assertEqual(original["expires_at"], 105)
        self.clock.now = 104.999
        self.assertEqual(self.inventory.available("widget"), 2)
        self.assertEqual(self.inventory.get_reservation("request")["status"], "reserved")
        self.clock.now = 105
        self.assertEqual(self.inventory.available("widget"), 5)
        self.assertEqual(self.inventory.get_reservation("request"), dict(original, status="expired"))
        self.assertFalse(self.inventory.cancel("request"))
        self.clock.now = 200
        self.assertEqual(self.inventory.available("widget"), 5)
        self.assertEqual(original["status"], "reserved")

    def test_each_observing_method_expires_reservations(self):
        for operation in ("available", "reserve", "cancel", "get_reservation", "renew"):
            with self.subTest(operation=operation):
                clock = FakeClock()
                inventory = Inventory(clock)
                inventory.stock("widget", 1)
                inventory.reserve("request", "widget", 1, 5)
                clock.now = 105
                if operation == "available":
                    self.assertEqual(inventory.available("widget"), 1)
                elif operation == "reserve":
                    self.assertEqual(inventory.reserve("request", "widget", 1, 5)["status"], "expired")
                elif operation == "cancel":
                    self.assertFalse(inventory.cancel("request"))
                elif operation == "get_reservation":
                    self.assertEqual(inventory.get_reservation("request")["status"], "expired")
                else:
                    with self.assertRaises(ValueError):
                        inventory.renew("request", 5)
                self.assertEqual(inventory.available("widget"), 1)
                self.assertEqual(inventory.get_reservation("request")["status"], "expired")

    def test_new_reservation_can_use_stock_released_at_expiry(self):
        self.inventory.reserve("first", "widget", 5, 5)
        self.clock.now = 105
        self.inventory.reserve("second", "widget", 5, 10)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertEqual(self.inventory.get_reservation("first")["status"], "expired")
        self.clock.now = 115
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_cancel_before_expiry_remains_cancelled(self):
        self.inventory.reserve("request", "widget", 3, 5)
        self.clock.now = 104
        self.assertTrue(self.inventory.cancel("request"))
        self.clock.now = 105
        self.assertFalse(self.inventory.cancel("request"))
        self.assertEqual(self.inventory.reserve("request", "widget", 3, 5)["status"], "cancelled")
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_timers_and_nonexpiring_reservations_are_independent(self):
        self.inventory.stock("other", 2)
        self.inventory.reserve("short", "widget", 2, 5)
        self.inventory.reserve("long", "widget", 2, 10)
        self.inventory.reserve("permanent", "widget", 1)
        self.inventory.reserve("other", "other", 2, 5)
        self.clock.now = 105
        self.assertEqual(self.inventory.available("widget"), 2)
        self.assertEqual(self.inventory.available("other"), 2)
        self.assertEqual(self.inventory.get_reservation("long")["status"], "reserved")
        self.clock.now = 1000
        self.assertEqual(self.inventory.available("widget"), 4)
        permanent = self.inventory.get_reservation("permanent")
        self.assertEqual(permanent["status"], "reserved")
        self.assertIsNone(permanent["expires_at"])

    def test_replay_preserves_timer_and_compares_numeric_ttls(self):
        original = self.inventory.reserve("request", "widget", 3, 5)
        self.clock.now = 103
        self.assertEqual(self.inventory.reserve("request", "widget", 3, 5.0), original)
        self.clock.now = 106
        self.assertEqual(self.inventory.reserve("request", "widget", 3, 5.0), dict(original, status="expired"))
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_conflicts_include_original_ttl_in_every_status(self):
        for status in ("reserved", "cancelled", "expired"):
            with self.subTest(status=status):
                clock = FakeClock()
                inventory = Inventory(clock)
                inventory.stock("widget", 5)
                inventory.reserve("request", "widget", 2, 5)
                if status == "cancelled":
                    inventory.cancel("request")
                elif status == "expired":
                    clock.now = 105
                for sku, quantity, ttl in (("widget", 2, None), ("widget", 2, 6), ("other", 2, 5), ("widget", 1, 5)):
                    with self.assertRaises(Conflict):
                        inventory.reserve("request", sku, quantity, ttl)
                self.assertEqual(inventory.get_reservation("request")["status"], status)
        self.inventory.reserve("permanent", "widget", 2)
        with self.assertRaises(Conflict):
            self.inventory.reserve("permanent", "widget", 2, 5)

    def test_renew_extends_then_shortens_without_changing_signature(self):
        original = self.inventory.reserve("request", "widget", 3, 5)
        self.clock.now = 103
        renewed = self.inventory.renew("request", 10)
        self.assertEqual(renewed["expires_at"], 113)
        self.assertEqual(self.inventory.reserve("request", "widget", 3, 5.0), renewed)
        with self.assertRaises(Conflict):
            self.inventory.reserve("request", "widget", 3, 10)
        self.clock.now = 105
        self.assertEqual(self.inventory.available("widget"), 2)
        self.assertEqual(self.inventory.renew("request", 1.5)["expires_at"], 106.5)
        self.clock.now = 106.5
        self.assertEqual(self.inventory.available("widget"), 5)
        self.assertEqual(self.inventory.reserve("request", "widget", 3, 5)["status"], "expired")
        self.assertEqual(original["expires_at"], 105)

    def test_renew_can_add_expiry_to_originally_nonexpiring_reservation(self):
        self.inventory.reserve("request", "widget", 3)
        self.clock.now = 200
        renewed = self.inventory.renew("request", 5)
        self.assertEqual(renewed["expires_at"], 205)
        self.assertEqual(self.inventory.reserve("request", "widget", 3), renewed)
        with self.assertRaises(Conflict):
            self.inventory.reserve("request", "widget", 3, 5)
        self.clock.now = 205
        self.assertEqual(self.inventory.reserve("request", "widget", 3)["status"], "expired")

    def test_failed_renewals_do_not_create_or_revive_reservations(self):
        self.inventory.reserve("cancelled", "widget", 2, 5)
        self.inventory.reserve("expired", "widget", 2, 5)
        self.inventory.cancel("cancelled")
        self.clock.now = 105
        for request_id in ("unknown", "cancelled", "expired"):
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    self.inventory.renew(request_id, 5)
                self.assertEqual(self.inventory.available("widget"), 5)
        self.assertIsNone(self.inventory.get_reservation("unknown"))
        self.assertEqual(self.inventory.get_reservation("cancelled")["status"], "cancelled")
        self.assertEqual(self.inventory.get_reservation("expired")["status"], "expired")
        self.assertEqual(self.inventory.reserve("unknown", "widget", 5)["status"], "reserved")

    def test_invalid_ttls_leave_live_reservations_and_ids_unchanged(self):
        original = self.inventory.reserve("request", "widget", 2, 5)
        for invalid in (0, -1, -0.5, True, False, float("nan"), float("inf"), -float("inf"), "5", [], {}):
            operations = (
                lambda: self.inventory.reserve("new", "widget", 1, invalid),
                lambda: self.inventory.reserve("request", "widget", 2, invalid),
                lambda: self.inventory.renew("request", invalid),
            )
            for operation in operations:
                with self.subTest(invalid=invalid, operation=operation):
                    with self.assertRaises(ValueError) as error:
                        operation()
                    self.assertIs(type(error.exception), ValueError)
                    self.assertEqual(self.inventory.get_reservation("request"), original)
                    self.assertEqual(self.inventory.available("widget"), 3)
                    self.assertIsNone(self.inventory.get_reservation("new"))
        with self.assertRaises(ValueError):
            self.inventory.renew("request", None)
        self.assertEqual(self.inventory.get_reservation("request"), original)
        self.inventory.reserve("new", "widget", 3, 5)

    def test_timed_out_of_stock_retry_starts_timer_on_success(self):
        with self.assertRaises(OutOfStock):
            self.inventory.reserve("request", "widget", 6, 5)
        self.assertIsNone(self.inventory.get_reservation("request"))
        self.clock.now = 200
        self.inventory.stock("widget", 1)
        self.assertEqual(self.inventory.reserve("request", "widget", 6, 5)["expires_at"], 205)

    def test_renewed_and_expired_snapshots_are_defensive(self):
        self.inventory.reserve("request", "widget", 2, 5)
        renewed = self.inventory.renew("request", 10)
        renewed["expires_at"] = 0
        renewed["quantity"] = 100
        self.assertEqual(self.inventory.get_reservation("request")["expires_at"], 110)
        self.clock.now = 110
        expired = self.inventory.reserve("request", "widget", 2, 5)
        expired["status"] = "reserved"
        expired["expires_at"] = 1000
        self.assertEqual(self.inventory.get_reservation("request")["status"], "expired")
        self.assertEqual(self.inventory.available("widget"), 5)


if __name__ == "__main__":
    unittest.main()
