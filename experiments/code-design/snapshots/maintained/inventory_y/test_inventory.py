import unittest
from unittest.mock import patch

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
            "expires_at": None,
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
                lambda: self.inventory.renew(invalid, 1),
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


class FakeClock:
    def __init__(self, now=100):
        self.now = now
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.now


class ExpirationTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.inventory = Inventory(clock=self.clock)
        self.inventory.stock("widget", 5)

    def test_default_clock_is_monotonic(self):
        with patch("inventory.time.monotonic", return_value=20) as clock:
            inventory = Inventory()
            inventory.stock("widget", 1)
            self.assertEqual(inventory.reserve("timed", "widget", 1, 3)["expires_at"], 23)
            clock.assert_called_once_with()

    def test_exact_boundary_and_stock_released_once(self):
        original = self.inventory.reserve("timed", "widget", 3, 5)
        self.assertEqual(original["expires_at"], 105)
        self.clock.now = 104.999
        self.assertEqual(self.inventory.available("widget"), 2)
        self.assertEqual(self.inventory.get_reservation("timed")["status"], "reserved")
        self.clock.now = 105
        self.assertEqual(self.inventory.available("widget"), 5)
        expected = dict(original, status="expired")
        self.assertEqual(self.inventory.get_reservation("timed"), expected)
        self.assertEqual(self.inventory.reserve("timed", "widget", 3, 5.0), expected)
        self.assertFalse(self.inventory.cancel("timed"))
        self.clock.now = 1000
        self.assertEqual(self.inventory.available("widget"), 5)
        self.assertEqual(original["status"], "reserved")

    def test_each_observer_expires_reservations_without_a_prior_read(self):
        for method in ("available", "reserve", "cancel", "get_reservation", "renew"):
            with self.subTest(method=method):
                clock = FakeClock()
                inventory = Inventory(clock)
                inventory.stock("widget", 1)
                inventory.reserve("timed", "widget", 1, 5)
                clock.now = 105
                if method == "available":
                    self.assertEqual(inventory.available("widget"), 1)
                elif method == "reserve":
                    self.assertEqual(inventory.reserve("timed", "widget", 1, 5)["status"], "expired")
                elif method == "cancel":
                    self.assertFalse(inventory.cancel("timed"))
                elif method == "get_reservation":
                    self.assertEqual(inventory.get_reservation("timed")["status"], "expired")
                else:
                    with self.assertRaises(ValueError):
                        inventory.renew("timed", 10)
                self.assertEqual(inventory.get_reservation("timed")["status"], "expired")
                self.assertEqual(inventory.available("widget"), 1)

    def test_new_reservation_can_use_stock_released_by_expiration(self):
        self.inventory.reserve("timed", "widget", 5, 2)
        self.clock.now = 102
        replacement = self.inventory.reserve("replacement", "widget", 5, 4)
        self.assertEqual(replacement["expires_at"], 106)
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertEqual(self.inventory.get_reservation("timed")["status"], "expired")

    def test_replay_never_restarts_timer_and_ttl_is_part_of_signature(self):
        expected = self.inventory.reserve("timed", "widget", 2, 5)
        self.clock.now = 103
        self.assertEqual(self.inventory.reserve("timed", "widget", 2, 5.0), expected)
        for now in (103, 105):
            self.clock.now = now
            for sku, quantity, ttl in (("other", 2, 5), ("widget", 3, 5), ("widget", 2, 6), ("widget", 2, None)):
                with self.subTest(now=now, sku=sku, quantity=quantity, ttl=ttl):
                    with self.assertRaises(Conflict):
                        self.inventory.reserve("timed", sku, quantity, ttl)
        self.assertEqual(self.inventory.reserve("timed", "widget", 2, 5)["status"], "expired")
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_cancelled_timed_reservations_stay_cancelled_and_conflict(self):
        self.inventory.reserve("timed", "widget", 3, 5)
        self.clock.now = 104
        self.assertTrue(self.inventory.cancel("timed"))
        self.clock.now = 106
        self.assertEqual(self.inventory.reserve("timed", "widget", 3, 5.0)["status"], "cancelled")
        with self.assertRaises(Conflict):
            self.inventory.reserve("timed", "widget", 3, 6)
        self.assertFalse(self.inventory.cancel("timed"))
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_mixed_reservations_and_skus_release_only_due_stock(self):
        self.inventory.stock("gadget", 4)
        self.inventory.reserve("untimed", "widget", 1)
        self.inventory.reserve("early", "widget", 2, 1)
        self.inventory.reserve("late", "widget", 2, 5)
        self.inventory.reserve("other", "gadget", 4, 1)
        self.clock.now = 101
        self.assertEqual(self.inventory.available("widget"), 2)
        self.assertEqual(self.inventory.available("gadget"), 4)
        self.clock.now = 200
        self.assertEqual(self.inventory.available("widget"), 4)
        self.assertEqual(self.inventory.get_reservation("untimed")["status"], "reserved")
        self.assertIsNone(self.inventory.get_reservation("untimed")["expires_at"])

    def test_renew_extends_and_shortens_from_now_preserving_original_signature(self):
        self.inventory.reserve("timed", "widget", 5, 5)
        self.clock.now = 103
        renewed = self.inventory.renew("timed", 10)
        self.assertEqual(renewed["expires_at"], 113)
        self.assertEqual(self.inventory.reserve("timed", "widget", 5, 5.0), renewed)
        with self.assertRaises(Conflict):
            self.inventory.reserve("timed", "widget", 5, 10)
        self.clock.now = 105
        self.assertEqual(self.inventory.available("widget"), 0)
        self.assertEqual(self.inventory.renew("timed", 1.5)["expires_at"], 106.5)
        self.clock.now = 106.5
        self.assertEqual(self.inventory.available("widget"), 5)

    def test_renew_can_add_expiry_to_untimed_reservation(self):
        self.inventory.reserve("untimed", "widget", 2)
        self.clock.now = 200
        renewed = self.inventory.renew("untimed", 4)
        self.assertEqual(renewed["expires_at"], 204)
        self.assertEqual(self.inventory.reserve("untimed", "widget", 2), renewed)
        with self.assertRaises(Conflict):
            self.inventory.reserve("untimed", "widget", 2, 4)
        self.clock.now = 204
        self.assertEqual(self.inventory.get_reservation("untimed")["status"], "expired")

    def test_failed_renew_does_not_revive_terminal_or_consume_unknown_id(self):
        self.inventory.reserve("cancelled", "widget", 2, 5)
        self.inventory.cancel("cancelled")
        self.inventory.reserve("expired", "widget", 2, 5)
        self.clock.now = 105
        for request_id in ("missing", "cancelled", "expired"):
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    self.inventory.renew(request_id, 10)
                self.assertEqual(self.inventory.available("widget"), 5)
        self.assertEqual(self.inventory.get_reservation("cancelled")["status"], "cancelled")
        self.assertEqual(self.inventory.get_reservation("expired")["status"], "expired")
        self.assertIsNone(self.inventory.get_reservation("missing"))
        self.assertEqual(self.inventory.reserve("missing", "widget", 5, 2)["status"], "reserved")

    def test_invalid_ttls_preserve_live_reservations_and_leave_ids_available(self):
        expected = self.inventory.reserve("live", "widget", 2, 5)
        invalid_ttls = (0, -1, -0.5, True, False, float("nan"), float("inf"), -float("inf"), "5", [], {})
        for invalid in invalid_ttls:
            for operation in (
                lambda: self.inventory.reserve("new", "widget", 1, invalid),
                lambda: self.inventory.reserve("live", "widget", 2, invalid),
                lambda: self.inventory.renew("live", invalid),
            ):
                with self.subTest(ttl=invalid, operation=operation):
                    with self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(self.inventory.get_reservation("live"), expected)
                    self.assertIsNone(self.inventory.get_reservation("new"))
                    self.assertEqual(self.inventory.available("widget"), 3)
        with self.assertRaises(ValueError):
            self.inventory.renew("live", None)
        self.assertEqual(self.inventory.get_reservation("live"), expected)
        self.assertEqual(self.inventory.reserve("new", "widget", 1, 0.5)["expires_at"], 100.5)

    def test_out_of_stock_does_not_claim_timed_request_signature(self):
        with self.assertRaises(OutOfStock):
            self.inventory.reserve("retry", "widget", 6, 3)
        self.clock.now = 101
        self.assertIsNone(self.inventory.get_reservation("retry"))
        self.assertEqual(self.inventory.reserve("retry", "widget", 5, 10)["expires_at"], 111)

    def test_timed_and_renewed_snapshots_are_defensive(self):
        original = self.inventory.reserve("timed", "widget", 2, 5)
        renewed = self.inventory.renew("timed", 10)
        expected = renewed.copy()
        for snapshot in (original, renewed, self.inventory.get_reservation("timed"), self.inventory.reserve("timed", "widget", 2, 5)):
            snapshot["expires_at"] = 0
            snapshot["status"] = "expired"
            self.assertEqual(self.inventory.get_reservation("timed"), expected)
            self.assertEqual(self.inventory.available("widget"), 3)

    def test_reserve_and_renew_use_one_clock_read_per_operation(self):
        self.inventory.reserve("timed", "widget", 1, 2)
        self.assertEqual(self.clock.calls, 1)
        self.inventory.renew("timed", 3)
        self.assertEqual(self.clock.calls, 2)


if __name__ == "__main__":
    unittest.main()
