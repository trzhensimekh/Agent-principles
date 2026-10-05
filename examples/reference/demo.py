"""Run one complete request and its idempotent replay in a temporary database."""

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from refunds.composition import open_ledger
from refunds.domain import Order
from refunds.service import request_refund


def main() -> None:
    paid_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with TemporaryDirectory() as directory:
        ledger = open_ledger(Path(directory) / "demo.sqlite")
        try:
            ledger.add_order(Order("order-1", paid_at, 2500))
            result = request_refund("order-1", "request-1", paid_at + timedelta(days=1), ledger)
            replay = request_refund("order-1", "request-1", paid_at + timedelta(days=90), ledger)
            assert replay == result
            print(json.dumps({"request": asdict(result), "outbox": ledger.events(),
                              "replay_equal": replay == result}, default=str, indent=2))
        finally:
            ledger.close()


if __name__ == "__main__":
    main()
