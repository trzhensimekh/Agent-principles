"""SQLite effect adapter. The transaction covers the request and its outbox."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .domain import AlreadyRequested, Order, RefundRequest, RequestConflict


class SQLiteLedger:
    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path, timeout=5)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                paid_at TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                state TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS refund_requests (
                request_id TEXT PRIMARY KEY,
                order_id TEXT UNIQUE NOT NULL REFERENCES orders(order_id),
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                requested_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS outbox (
                request_id TEXT PRIMARY KEY REFERENCES refund_requests(request_id),
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.connection.close()

    def add_order(self, order: Order) -> None:
        """Insert an order once. This example intentionally has no update API."""
        with self.connection:
            self.connection.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?)",
                (order.order_id, order.paid_at.isoformat(), order.amount_cents, order.state),
            )

    def get_order(self, order_id: str) -> Order:
        row = self.connection.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        if row is None:
            raise KeyError(order_id)
        return Order(row["order_id"], datetime.fromisoformat(row["paid_at"]),
                     row["amount_cents"], row["state"])

    def get_request(self, request_id: str) -> RefundRequest | None:
        row = self.connection.execute(
            "SELECT * FROM refund_requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        if row is None:
            return None
        return RefundRequest(row["request_id"], row["order_id"], row["amount_cents"],
                             datetime.fromisoformat(row["requested_at"]))

    def record(self, request: RefundRequest) -> RefundRequest:
        # BEGIN IMMEDIATE serializes the check + insert across separate connections.
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            previous = self.get_request(request.request_id)
            if previous is not None:
                if previous.order_id != request.order_id:
                    raise RequestConflict("request_id already belongs to another order")
                return previous
            if self.connection.execute(
                "SELECT 1 FROM refund_requests WHERE order_id = ?", (request.order_id,)
            ).fetchone():
                raise AlreadyRequested("a full refund has already been requested")
            order = self.get_order(request.order_id)
            if order.amount_cents != request.amount_cents:
                raise ValueError("refund amount must equal the original order amount")
            self.connection.execute(
                "INSERT INTO refund_requests VALUES (?, ?, ?, ?)",
                (request.request_id, request.order_id, request.amount_cents,
                 request.requested_at.isoformat()),
            )
            payload = json.dumps({
                "request_id": request.request_id,
                "order_id": request.order_id,
                "amount_cents": request.amount_cents,
                "requested_at": request.requested_at.isoformat(),
            }, sort_keys=True)
            self.connection.execute(
                "INSERT INTO outbox VALUES (?, ?, ?)",
                (request.request_id, "refund.requested", payload),
            )
        return request

    def events(self) -> list[dict]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM outbox ORDER BY request_id"
        )]
