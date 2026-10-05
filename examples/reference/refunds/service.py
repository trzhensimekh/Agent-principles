"""Application entry point. All effects cross the explicitly supplied ledger."""

from datetime import datetime

from .domain import RefundRequest, RequestConflict, approve
from .ports import RefundLedger


def request_refund(
    order_id: str, request_id: str, now: datetime, ledger: RefundLedger
) -> RefundRequest:
    """Request a full refund; replay succeeds even after eligibility expires."""
    previous = ledger.get_request(request_id)
    if previous is not None:
        if previous.order_id != order_id:
            raise RequestConflict("request_id already belongs to another order")
        return previous
    approved = approve(ledger.get_order(order_id), now, request_id)
    return ledger.record(approved)
