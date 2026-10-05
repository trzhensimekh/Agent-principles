"""The only production wiring decision: RefundLedger -> SQLiteLedger."""

from pathlib import Path

from .sqlite_ledger import SQLiteLedger


def open_ledger(path: Path) -> SQLiteLedger:
    return SQLiteLedger(path)
