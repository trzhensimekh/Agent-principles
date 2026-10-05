"""Behavior and adapter contracts. Only the documented scope is claimed."""

import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from threading import Barrier

from refunds.composition import open_ledger
from refunds.domain import (
    AlreadyRequested, Ineligible, Order, RefundRequest, RequestConflict, approve,
)
from refunds.service import request_refund


PAID_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


class SpringOffset(tzinfo):
    """Deterministic offset transition; no external timezone database required."""

    def utcoffset(self, value):
        return timedelta(hours=1 if value and value.day >= 15 else 0)

    def dst(self, value):
        return timedelta(0)


class PolicyTests(unittest.TestCase):
    def test_window_boundaries(self):
        order = Order("one", PAID_AT, 2500)
        for age in (timedelta(0), timedelta(days=30) - timedelta(microseconds=1)):
            with self.subTest(age=age):
                self.assertEqual(approve(order, PAID_AT + age, "r").amount_cents, 2500)
        for age in (-timedelta(microseconds=1), timedelta(days=30)):
            with self.subTest(age=age), self.assertRaises(Ineligible):
                approve(order, PAID_AT + age, "r")

    def test_state_policy(self):
        for state in ("paid", "shipped"):
            self.assertEqual(approve(Order("one", PAID_AT, 2500, state), PAID_AT, "r").order_id, "one")
        for state in ("cancelled", "pending", "unknown"):
            with self.subTest(state=state), self.assertRaises(Ineligible):
                approve(Order("one", PAID_AT, 2500, state), PAID_AT, "r")

    def test_timezone_aware_timestamps(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            Order("one", datetime(2026, 1, 1), 2500)
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            approve(Order("one", PAID_AT, 2500), datetime(2026, 1, 1), "r")
        other_zone = PAID_AT.astimezone(timezone(timedelta(hours=5)))
        self.assertEqual(approve(Order("one", PAID_AT, 2500), other_zone, "r").requested_at, PAID_AT)

    def test_money_is_positive_integer_cents(self):
        for amount in (0, -1, 1.5, True):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                Order("one", PAID_AT, amount)

    def test_request_ids_are_required(self):
        with self.assertRaises(ValueError):
            approve(Order("one", PAID_AT, 2500), PAID_AT, "")

    def test_elapsed_window_survives_offset_transition(self):
        zone = SpringOffset()
        paid = datetime(2026, 3, 1, 12, tzinfo=zone)
        now = datetime(2026, 3, 31, 12, tzinfo=zone)
        original = approve(Order("one", paid, 2500), now, "r")
        roundtripped = approve(Order("one", datetime.fromisoformat(paid.isoformat()), 2500), now, "r")
        self.assertEqual(original, roundtripped)
        self.assertEqual(original.amount_cents, 2500)  # 29 elapsed days + 23 hours
        with self.assertRaises(Ineligible):
            approve(Order("one", paid, 2500), now + timedelta(hours=1), "r")


class LedgerContractTests(unittest.TestCase):
    """Observable guarantees required of the configured RefundLedger adapter."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "ledger.sqlite"
        self.ledger = open_ledger(self.path)
        self.addCleanup(self.ledger.close)
        self.ledger.add_order(Order("one", PAID_AT, 2500))
        self.ledger.add_order(Order("two", PAID_AT, 4000))

    def request(self, order="one", request_id="r", now=PAID_AT):
        return request_refund(order, request_id, now, self.ledger)

    def test_request_and_event_are_persisted(self):
        result = self.request()
        other = open_ledger(self.path)
        try:
            self.assertEqual(other.get_request("r"), result)
            event, = other.events()
            self.assertEqual(event["event_type"], "refund.requested")
            self.assertEqual(json.loads(event["payload"]), {
                "request_id": "r", "order_id": "one", "amount_cents": 2500,
                "requested_at": PAID_AT.isoformat(),
            })
        finally:
            other.close()

    def test_replay_returns_original_after_window_closes(self):
        result = self.request()
        self.assertEqual(self.request(now=PAID_AT + timedelta(days=90)), result)
        self.assertEqual(len(self.ledger.events()), 1)

    def test_same_key_for_other_order_is_rejected(self):
        self.request()
        with self.assertRaises(RequestConflict):
            self.request(order="two")
        self.assertEqual(len(self.ledger.events()), 1)

    def test_second_key_for_same_order_is_rejected(self):
        self.request()
        with self.assertRaises(AlreadyRequested):
            self.request(request_id="another")
        self.assertIsNone(self.ledger.get_request("another"))
        self.assertEqual(len(self.ledger.events()), 1)

    def test_adapter_rechecks_idempotency_inside_transaction(self):
        original = self.request()
        self.assertEqual(self.ledger.record(RefundRequest("r", "one", 2500,
                         PAID_AT + timedelta(days=1))), original)
        with self.assertRaises(RequestConflict):
            self.ledger.record(RefundRequest("r", "two", 4000, PAID_AT))

    def test_outbox_failure_rolls_back_request(self):
        self.ledger.connection.execute("""
            CREATE TRIGGER reject_event BEFORE INSERT ON outbox
            BEGIN SELECT RAISE(ABORT, 'injected outbox failure'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "injected outbox failure"):
            self.request()
        self.assertIsNone(self.ledger.get_request("r"))
        self.assertEqual(self.ledger.events(), [])

    def test_ineligible_request_has_no_effect(self):
        with self.assertRaises(Ineligible):
            self.request(now=PAID_AT + timedelta(days=30))
        self.assertIsNone(self.ledger.get_request("r"))
        self.assertEqual(self.ledger.events(), [])

    def test_missing_order_has_no_effect(self):
        with self.assertRaises(KeyError):
            self.request(order="missing")
        self.assertEqual(self.ledger.events(), [])

    def test_orders_cannot_be_replaced_through_adapter(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger.add_order(Order("one", PAID_AT, 9999))
        self.assertEqual(self.ledger.get_order("one").amount_cents, 2500)

    def test_adapter_rejects_wrong_amount_without_effect(self):
        with self.assertRaisesRegex(ValueError, "original order amount"):
            self.ledger.record(RefundRequest("r", "one", 9999, PAID_AT))
        self.assertIsNone(self.ledger.get_request("r"))
        self.assertEqual(self.ledger.events(), [])

    def test_concurrent_same_key_creates_one_event(self):
        gate = Barrier(2)

        def invoke():
            ledger = open_ledger(self.path)
            try:
                gate.wait(timeout=5)
                return request_refund("one", "r", PAID_AT, ledger)
            finally:
                ledger.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = [future.result(timeout=10)
                             for future in (pool.submit(invoke), pool.submit(invoke))]
        self.assertEqual(first, second)
        self.assertEqual(len(self.ledger.events()), 1)

    def test_concurrent_different_keys_cannot_double_request(self):
        gate = Barrier(2)

        def invoke(key):
            ledger = open_ledger(self.path)
            try:
                gate.wait(timeout=5)
                try:
                    request_refund("one", key, PAID_AT, ledger)
                    return "accepted"
                except AlreadyRequested:
                    return "rejected"
            finally:
                ledger.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=10)
                       for future in (pool.submit(invoke, "a"), pool.submit(invoke, "b"))]
        self.assertCountEqual(results, ["accepted", "rejected"])
        self.assertEqual(len(self.ledger.events()), 1)


if __name__ == "__main__":
    unittest.main()
