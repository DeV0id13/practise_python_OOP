import uuid
from datetime import datetime, timezone

from transaction import Transaction
from enums import TransactionStatus


class TransactionQueue:
    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def add_transaction(
            self,
            transaction: Transaction,
    ) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Expected a Transaction object.")
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError("Transaction status must be PENDING.")
        if any(t.transaction_id == transaction.transaction_id for t in self._transactions):
            raise ValueError("Transaction with this UUID already exists in the queue.")
        self._transactions.append(transaction)

    def get_next_transaction(self) -> Transaction | None:
        now = datetime.now(timezone.utc)
        pending_transactions = [
            t for t in self._transactions if t.status == TransactionStatus.PENDING
        ]
        ready_transactions = [
            t for t in pending_transactions if t.execute_after is None or t.execute_after <= now
        ]
        ready_transactions.sort(key=lambda t: t.priority.value, reverse=True)
        return ready_transactions[0] if ready_transactions else None

    def cancel_transaction(
            self,
            transaction_id: uuid.UUID,
    ) -> None:
        if not isinstance(transaction_id, uuid.UUID):
            raise TypeError(
                "transaction_id must be a valid UUID."
            )
        transaction = next(
            (
                t for t in self._transactions
                if t.transaction_id == transaction_id
            ),
            None,
        )
        if transaction is None:
            raise ValueError(
                "Transaction with this UUID does not exist."
            )
        transaction.change_status(TransactionStatus.CANCELLED)

    def __len__(self) -> int:
        return len(self._transactions)
