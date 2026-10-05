"""Prompt-derived inventory acceptance tests; candidate is supplied by runner.py."""
import unittest

import candidate


class InventoryStage1Tests(unittest.TestCase):
    def setUp(self):
        self.module = candidate.module
        self.inv = self.module.Inventory()

    def assertSnapshot(self, actual, request_id, sku, quantity, status):
        self.assertIsInstance(actual, dict)
        self.assertEqual({k: actual[k] for k in ('request_id', 'sku', 'quantity', 'status')},
                         dict(request_id=request_id, sku=sku, quantity=quantity, status=status))

    def test_exception_types(self):
        self.assertTrue(issubclass(self.module.OutOfStock, ValueError))
        self.assertTrue(issubclass(self.module.Conflict, ValueError))

    def test_empty_additive_stock_and_independent_skus(self):
        self.assertEqual(self.inv.available('unknown'), 0)
        self.inv.stock('a', 7)
        self.inv.stock('a', 5)
        self.inv.stock('b', 3)
        self.assertEqual(self.inv.available('a'), 12)
        self.assertEqual(self.inv.available('b'), 3)

    def test_reserve_exact_stock_and_current_snapshots(self):
        self.inv.stock('a', 5)
        self.assertSnapshot(self.inv.reserve('r1', 'a', 2), 'r1', 'a', 2, 'reserved')
        self.assertSnapshot(self.inv.reserve('r2', 'a', 3), 'r2', 'a', 3, 'reserved')
        self.assertEqual(self.inv.available('a'), 0)
        self.assertSnapshot(self.inv.get_reservation('r1'), 'r1', 'a', 2, 'reserved')

    def test_out_of_stock_does_not_consume_id_or_change_state(self):
        self.inv.stock('a', 3)
        self.inv.reserve('existing', 'a', 1)
        before = self.inv.get_reservation('existing')
        with self.assertRaises(self.module.OutOfStock):
            self.inv.reserve('retry', 'a', 3)
        self.assertEqual(self.inv.available('a'), 2)
        self.assertIsNone(self.inv.get_reservation('retry'))
        self.assertEqual(self.inv.get_reservation('existing'), before)
        self.assertSnapshot(self.inv.reserve('retry', 'a', 2), 'retry', 'a', 2, 'reserved')

    def test_unknown_sku_failure_allows_retry_on_different_sku(self):
        with self.assertRaises(self.module.OutOfStock):
            self.inv.reserve('retry', 'unknown', 1)
        self.inv.stock('a', 1)
        self.assertSnapshot(self.inv.reserve('retry', 'a', 1), 'retry', 'a', 1, 'reserved')

    def test_replay_is_idempotent_even_with_no_stock_available(self):
        self.inv.stock('a', 4)
        first = self.inv.reserve('r', 'a', 4)
        self.assertEqual(self.inv.reserve('r', 'a', 4), first)
        self.assertEqual(self.inv.available('a'), 0)

    def test_conflicting_replays_leave_state_unchanged(self):
        self.inv.stock('a', 6)
        self.inv.stock('b', 6)
        first = self.inv.reserve('r', 'a', 2)
        for sku, qty in [('b', 2), ('a', 3), ('b', 3)]:
            with self.subTest(sku=sku, qty=qty):
                with self.assertRaises(self.module.Conflict):
                    self.inv.reserve('r', sku, qty)
                self.assertEqual(self.inv.get_reservation('r'), first)
                self.assertEqual(self.inv.available('a'), 4)
                self.assertEqual(self.inv.available('b'), 6)

    def test_cancel_releases_once_and_terminal_replay(self):
        self.inv.stock('a', 5)
        self.inv.reserve('r', 'a', 3)
        self.assertIs(self.inv.cancel('r'), True)
        self.assertEqual(self.inv.available('a'), 5)
        self.assertIs(self.inv.cancel('r'), False)
        self.assertIs(self.inv.cancel('unknown'), False)
        self.assertIsNone(self.inv.get_reservation('unknown'))
        self.assertSnapshot(self.inv.reserve('r', 'a', 3), 'r', 'a', 3, 'cancelled')
        self.assertEqual(self.inv.available('a'), 5)
        with self.assertRaises(self.module.Conflict):
            self.inv.reserve('r', 'a', 2)

    def test_reservation_and_get_snapshots_are_defensive(self):
        self.inv.stock('a', 8)
        for returned in [self.inv.reserve('r', 'a', 3), self.inv.get_reservation('r')]:
            returned.update(request_id='other', sku='b', quantity=1000, status='cancelled')
            returned['arbitrary'] = []
        self.assertSnapshot(self.inv.get_reservation('r'), 'r', 'a', 3, 'reserved')
        self.assertEqual(self.inv.available('a'), 5)
        replay = self.inv.reserve('r', 'a', 3)
        replay.clear()
        self.assertSnapshot(self.inv.get_reservation('r'), 'r', 'a', 3, 'reserved')

    def test_invalid_skus_all_entry_points_preserve_state(self):
        self.inv.stock('a', 8)
        saved = self.inv.reserve('live', 'a', 3)
        for bad in ['', None, True, False, 0, 1, 1.5, [], {}, b'a']:
            for method in ['stock', 'available', 'reserve']:
                with self.subTest(bad=repr(bad), method=method):
                    with self.assertRaises(ValueError):
                        if method == 'stock':
                            self.inv.stock(bad, 2)
                        elif method == 'available':
                            self.inv.available(bad)
                        else:
                            self.inv.reserve('retry', bad, 2)
                    self.assertEqual(self.inv.available('a'), 5)
                    self.assertEqual(self.inv.get_reservation('live'), saved)
                    self.assertIsNone(self.inv.get_reservation('retry'))

    def test_invalid_ids_all_entry_points_preserve_state(self):
        self.inv.stock('a', 8)
        saved = self.inv.reserve('live', 'a', 3)
        for bad in ['', None, True, False, 0, 1, 1.5, [], {}, b'r']:
            for method in ['reserve', 'cancel', 'get_reservation']:
                with self.subTest(bad=repr(bad), method=method):
                    with self.assertRaises(ValueError):
                        if method == 'reserve':
                            self.inv.reserve(bad, 'a', 2)
                        else:
                            getattr(self.inv, method)(bad)
                    self.assertEqual(self.inv.available('a'), 5)
                    self.assertEqual(self.inv.get_reservation('live'), saved)

    def test_invalid_quantities_do_not_consume_ids_or_modify_live_requests(self):
        self.inv.stock('a', 8)
        saved = self.inv.reserve('live', 'a', 3)
        for bad in [0, -1, True, False, 1.0, '2', None, [], {}, float('nan'), float('inf')]:
            for method in ['stock', 'new_reserve', 'live_reserve']:
                with self.subTest(bad=repr(bad), method=method):
                    with self.assertRaises(ValueError):
                        if method == 'stock':
                            self.inv.stock('a', bad)
                        else:
                            self.inv.reserve('retry' if method == 'new_reserve' else 'live', 'a', bad)
                    self.assertEqual(self.inv.available('a'), 5)
                    self.assertEqual(self.inv.get_reservation('live'), saved)
                    self.assertIsNone(self.inv.get_reservation('retry'))
        self.assertSnapshot(self.inv.reserve('retry', 'a', 2), 'retry', 'a', 2, 'reserved')

    def test_instances_are_independent_and_large_quantities_exact(self):
        huge = 10 ** 80 + 7
        self.inv.stock('a', huge)
        other = self.module.Inventory()
        self.assertEqual(other.available('a'), 0)
        self.inv.reserve('r', 'a', huge - 1)
        self.assertEqual(self.inv.available('a'), 1)
        self.inv.cancel('r')
        self.assertEqual(self.inv.available('a'), huge)


class Clock:
    def __init__(self, now=100):
        self.now = now

    def __call__(self):
        return self.now


class InventoryStage2Tests(unittest.TestCase):
    def setUp(self):
        self.module = candidate.module
        self.clock = Clock()
        self.inv = self.module.Inventory(clock=self.clock)
        self.inv.stock('a', 10)

    def reserve(self, request_id='r', sku='a', quantity=4, ttl_seconds=5):
        return self.inv.reserve(request_id, sku, quantity, ttl_seconds=ttl_seconds)

    def test_no_expiry_defaults_and_fractional_ttl(self):
        snapshot = self.inv.reserve('forever', 'a', 2)
        self.assertIsNone(snapshot['expires_at'])
        self.assertEqual(self.reserve()['expires_at'], 105)
        self.clock.now = 100.25
        self.assertEqual(self.reserve('fraction', quantity=1, ttl_seconds=0.5)['expires_at'], 100.75)
        self.clock.now = 10 ** 9
        self.assertEqual(self.inv.get_reservation('forever')['status'], 'reserved')
        self.assertEqual(self.inv.available('a'), 8)

    def test_expiry_is_exact_and_releases_stock_once(self):
        self.reserve()
        self.clock.now = 104.999
        self.assertEqual(self.inv.available('a'), 6)
        self.assertEqual(self.inv.get_reservation('r')['status'], 'reserved')
        self.clock.now = 105
        self.assertEqual(self.inv.available('a'), 10)
        snapshot = self.inv.get_reservation('r')
        self.assertEqual(snapshot['status'], 'expired')
        self.assertEqual(snapshot['expires_at'], 105)
        self.assertIs(self.inv.cancel('r'), False)
        self.clock.now = 110
        self.assertEqual(self.inv.available('a'), 10)
        self.assertEqual(self.inv.get_reservation('r'), snapshot)

    def test_each_observer_expires_without_prior_available_call(self):
        for observer in ['available', 'reserve', 'cancel', 'get_reservation', 'renew']:
            for now in [105, 106]:
                with self.subTest(observer=observer, now=now):
                    clock = Clock()
                    inv = self.module.Inventory(clock=clock)
                    inv.stock('a', 4)
                    inv.reserve('r', 'a', 4, ttl_seconds=5)
                    clock.now = now
                    if observer == 'available':
                        self.assertEqual(inv.available('a'), 4)
                    elif observer == 'reserve':
                        self.assertEqual(inv.reserve('new', 'a', 4)['status'], 'reserved')
                    elif observer == 'cancel':
                        self.assertIs(inv.cancel('r'), False)
                    elif observer == 'get_reservation':
                        self.assertEqual(inv.get_reservation('r')['status'], 'expired')
                    else:
                        with self.assertRaises(ValueError):
                            inv.renew('r', 5)
                    self.assertEqual(inv.get_reservation('r')['status'], 'expired')
                    self.assertEqual(inv.available('a'), 0 if observer == 'reserve' else 4)

    def test_timed_replay_never_restarts_timer_including_after_expiry(self):
        first = self.reserve()
        self.clock.now = 103
        self.assertEqual(self.reserve(ttl_seconds=5.0), first)
        self.assertEqual(self.inv.available('a'), 6)
        self.clock.now = 105
        replay = self.reserve()
        self.assertEqual(replay['status'], 'expired')
        self.assertEqual(replay['expires_at'], 105)
        self.assertEqual(self.inv.available('a'), 10)
        self.clock.now = 1000
        self.assertEqual(self.reserve(), replay)

    def test_original_ttl_conflicts_for_live_cancelled_and_expired(self):
        for terminal in ['live', 'cancelled', 'expired']:
            with self.subTest(terminal=terminal):
                clock = Clock()
                inv = self.module.Inventory(clock=clock)
                inv.stock('a', 10)
                inv.reserve('r', 'a', 4, ttl_seconds=5)
                if terminal == 'cancelled':
                    inv.cancel('r')
                elif terminal == 'expired':
                    clock.now = 105
                saved = inv.get_reservation('r')
                for kwargs in [dict(ttl_seconds=None), dict(ttl_seconds=6)]:
                    with self.assertRaises(self.module.Conflict):
                        inv.reserve('r', 'a', 4, **kwargs)
                    self.assertEqual(inv.get_reservation('r'), saved)
                with self.assertRaises(self.module.Conflict):
                    inv.reserve('r', 'a', 3, ttl_seconds=5)

    def test_none_signature_conflicts_with_timed_and_preserves_terminal(self):
        first = self.inv.reserve('r', 'a', 4)
        with self.assertRaises(self.module.Conflict):
            self.reserve()
        self.assertEqual(self.inv.get_reservation('r'), first)
        self.inv.cancel('r')
        with self.assertRaises(self.module.Conflict):
            self.reserve()
        self.assertEqual(self.inv.reserve('r', 'a', 4, ttl_seconds=None)['status'], 'cancelled')

    def test_invalid_ttl_preserves_live_state_and_does_not_consume_new_id(self):
        saved = self.reserve()
        for bad in [0, -1, -0.5, True, False, '5', [], {}, float('nan'), float('inf'), -float('inf')]:
            for request_id in ['new', 'r']:
                with self.subTest(bad=repr(bad), request_id=request_id):
                    with self.assertRaises(ValueError):
                        self.reserve(request_id, ttl_seconds=bad)
                    self.assertEqual(self.inv.get_reservation('r'), saved)
                    self.assertIsNone(self.inv.get_reservation('new'))
                    self.assertEqual(self.inv.available('a'), 6)
        self.assertEqual(self.reserve('new', ttl_seconds=2)['status'], 'reserved')

    def test_failed_timed_out_of_stock_can_retry_with_different_signature(self):
        with self.assertRaises(self.module.OutOfStock):
            self.reserve(quantity=11, ttl_seconds=10)
        self.clock.now = 101
        snapshot = self.reserve(quantity=4, ttl_seconds=2)
        self.assertEqual(snapshot['expires_at'], 103)

    def test_renew_sets_expiry_from_now_and_can_shorten(self):
        self.reserve()
        self.clock.now = 103
        renewed = self.inv.renew('r', 10)
        self.assertEqual(renewed['expires_at'], 113)
        self.assertEqual(renewed['status'], 'reserved')
        self.assertEqual(self.inv.available('a'), 6)
        self.clock.now = 106
        self.assertEqual(self.inv.get_reservation('r')['status'], 'reserved')
        self.assertEqual(self.inv.renew('r', 1)['expires_at'], 107)
        self.clock.now = 107
        self.assertEqual(self.inv.get_reservation('r')['status'], 'expired')
        self.assertEqual(self.inv.available('a'), 10)

    def test_renew_preserves_original_signature(self):
        self.reserve(ttl_seconds=5)
        self.clock.now = 103
        current = self.inv.renew('r', 10)
        self.assertEqual(self.reserve(ttl_seconds=5.0), current)
        with self.assertRaises(self.module.Conflict):
            self.reserve(ttl_seconds=10)
        self.clock.now = 113
        self.assertEqual(self.reserve(ttl_seconds=5)['status'], 'expired')
        self.assertEqual(self.inv.available('a'), 10)

    def test_renew_previously_nonexpiring_preserves_none_signature(self):
        self.inv.reserve('r', 'a', 4)
        self.clock.now = 200
        renewed = self.inv.renew('r', 2.5)
        self.assertEqual(renewed['expires_at'], 202.5)
        self.assertEqual(self.inv.reserve('r', 'a', 4), renewed)
        with self.assertRaises(self.module.Conflict):
            self.reserve(ttl_seconds=2.5)
        self.clock.now = 202.5
        self.assertEqual(self.inv.get_reservation('r')['status'], 'expired')

    def test_renew_invalid_ttl_and_id_leave_active_reservation_unchanged(self):
        saved = self.reserve()
        for bad in [None, 0, -1, -0.5, True, False, '5', [], {}, float('nan'), float('inf'), -float('inf')]:
            with self.subTest(ttl=repr(bad)):
                with self.assertRaises(ValueError):
                    self.inv.renew('r', bad)
                self.assertEqual(self.inv.get_reservation('r'), saved)
                self.assertEqual(self.inv.available('a'), 6)
        for bad in ['', None, True, False, 0, 1, 1.5, [], {}, b'r']:
            with self.subTest(request_id=repr(bad)):
                with self.assertRaises(ValueError):
                    self.inv.renew(bad, 5)
                self.assertEqual(self.inv.get_reservation('r'), saved)

    def test_renew_unknown_cancelled_or_expired_never_revives(self):
        with self.assertRaises(ValueError):
            self.inv.renew('missing', 5)
        self.assertIsNone(self.inv.get_reservation('missing'))
        self.reserve('cancelled', quantity=2)
        self.inv.cancel('cancelled')
        self.reserve('expired', quantity=2)
        self.clock.now = 105
        for request_id, status in [('cancelled', 'cancelled'), ('expired', 'expired')]:
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    self.inv.renew(request_id, 5)
                self.assertEqual(self.inv.get_reservation(request_id)['status'], status)
                self.assertEqual(self.inv.available('a'), 10)

    def test_cancellation_before_expiry_retains_cancelled_status_after_deadline(self):
        self.reserve()
        self.clock.now = 104.999
        self.assertIs(self.inv.cancel('r'), True)
        self.clock.now = 105
        self.assertEqual(self.inv.get_reservation('r')['status'], 'cancelled')
        self.assertIs(self.inv.cancel('r'), False)
        self.assertEqual(self.reserve()['status'], 'cancelled')
        self.assertEqual(self.inv.available('a'), 10)

    def test_mixed_expirations_and_independent_skus(self):
        self.inv.stock('b', 5)
        self.reserve('early', quantity=3, ttl_seconds=2)
        self.reserve('late', quantity=4, ttl_seconds=5)
        self.reserve('forever', quantity=2, ttl_seconds=None)
        self.reserve('b', sku='b', quantity=5, ttl_seconds=2)
        self.clock.now = 102
        self.assertEqual(self.inv.available('a'), 4)
        self.assertEqual(self.inv.available('b'), 5)
        self.clock.now = 105
        self.assertEqual(self.inv.available('a'), 8)

    def test_all_timed_snapshot_paths_are_defensive(self):
        self.reserve()
        for snapshot in [self.inv.get_reservation('r'), self.reserve(), self.inv.renew('r', 6)]:
            snapshot.update(expires_at=0, status='expired', quantity=999, sku='b')
        actual = self.inv.get_reservation('r')
        self.assertEqual(actual['expires_at'], 106)
        self.assertEqual(actual['status'], 'reserved')
        self.assertEqual(actual['quantity'], 4)
        self.assertEqual(self.inv.available('a'), 6)
