import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from enums import (
    AccountCurrency,
    TransactionType,
    TransactionStatus,
    TransactionPriority,
)
from exceptions import InvalidOperationError


class Transaction:
    def __init__(
            self,
            transaction_type: TransactionType,
            amount: Decimal,
            currency: AccountCurrency,
            client_id: uuid.UUID,
            sender_account_id: uuid.UUID | None = None,
            recipient_account_id: uuid.UUID | None = None,
            priority: TransactionPriority = TransactionPriority.NORMAL,
            execute_after: datetime | None = None,
    ) -> None:
        if not isinstance(transaction_type, TransactionType):
            raise ValueError("Transaction type must be an instance of TransactionType.")
        if not isinstance(amount, Decimal):
            raise TypeError("Amount must be a Decimal.")
        if not amount.is_finite() or amount <= 0:
            raise ValueError(
                "Amount must be a positive finite Decimal."
            )
        try:
            if amount != amount.quantize(Decimal("0.01")):
                raise ValueError(
                    "Amount must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError("Invalid amount precision.") from exc
        if not isinstance(currency, AccountCurrency):
            raise ValueError("Currency must be an instance of AccountCurrency.")
        if not isinstance(priority, TransactionPriority):
            raise ValueError("Priority must be an instance of TransactionPriority.")
        if not isinstance(client_id, uuid.UUID):
            raise ValueError("Client ID must be a valid UUID.")
        if sender_account_id is not None and not isinstance(sender_account_id, uuid.UUID):
            raise ValueError("Sender account ID must be a valid UUID.")
        if recipient_account_id is not None and not isinstance(recipient_account_id, uuid.UUID):
            raise ValueError("Recipient account ID must be a valid UUID.")
        if transaction_type == TransactionType.DEPOSIT and recipient_account_id is None:
            raise ValueError("Recipient account ID is required for deposit transactions.")
        if transaction_type == TransactionType.WITHDRAWAL and sender_account_id is None:
            raise ValueError("Sender account ID is required for withdrawal transactions.")
        if transaction_type in (
                TransactionType.INTERNAL_TRANSFER,
                TransactionType.EXTERNAL_TRANSFER,
        ):
            if sender_account_id is None or recipient_account_id is None:
                raise ValueError(
                    "Sender and recipient are required for transfers."
                )

            if sender_account_id == recipient_account_id:
                raise ValueError(
                    "Sender and recipient must be different accounts."
                )
        if execute_after is not None:
            if not isinstance(execute_after, datetime):
                raise TypeError(
                    "execute_after must be a datetime object."
                )

            if execute_after.tzinfo is None or execute_after.utcoffset() is None:
                raise ValueError(
                    "execute_after must have timezone information."
                )
        self.transaction_id = uuid.uuid4()
        self.transaction_type = transaction_type
        self._amount = amount
        self._currency = currency
        self.client_id = client_id
        self.sender_account_id = sender_account_id
        self.recipient_account_id = recipient_account_id
        self._priority = priority
        self._status = TransactionStatus.PENDING
        self._fee = Decimal("0.00")
        self.failure_reason = None
        self.created_at = datetime.now(timezone.utc)
        self.execute_after = execute_after
        self.processed_at = None
        self._attempts = 0

    def change_status(
            self,
            new_status: TransactionStatus,
    ) -> None:
        if not isinstance(new_status, TransactionStatus):
            raise TypeError(
                "new_status must be an instance of TransactionStatus."
            )
        valid_transitions = {
            TransactionStatus.PENDING: {
                TransactionStatus.PROCESSING,
                TransactionStatus.CANCELLED,
            },
            TransactionStatus.PROCESSING: {
                TransactionStatus.COMPLETED,
                TransactionStatus.FAILED,
            },
            TransactionStatus.FAILED: {
                TransactionStatus.PENDING,
            },
            TransactionStatus.COMPLETED: set(),
            TransactionStatus.CANCELLED: set(),
        }
        if new_status not in valid_transitions[self._status]:
            raise InvalidOperationError(
                f"Transition from {self._status.value} "
                f"to {new_status.value} is not allowed."
            )
        self._status = new_status

    def start_processing(self) -> None:
        self.change_status(TransactionStatus.PROCESSING)
        self._attempts += 1
        self.failure_reason = None
        self.processed_at = None

    def complete(self, fee: Decimal) -> None:
        if not isinstance(fee, Decimal):
            raise TypeError("Fee must be a Decimal.")
        if not fee.is_finite() or fee < 0:
            raise ValueError(
                "Fee must be a non-negative finite Decimal."
            )
        try:
            if fee != fee.quantize(Decimal("0.01")):
                raise ValueError(
                    "Fee must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError("Invalid fee precision.") from exc
        self.change_status(TransactionStatus.COMPLETED)
        self._fee = fee
        self.processed_at = datetime.now(timezone.utc)

    def fail(self, reason: str) -> None:
        if not isinstance(reason, str):
            raise TypeError("Reason must be a string.")
        if not reason.strip():
            raise ValueError("Failure reason cannot be empty.")
        self.change_status(TransactionStatus.FAILED)
        self.failure_reason = reason.strip()
        self.processed_at = datetime.now(timezone.utc)

    @property
    def status(self) -> TransactionStatus:
        return self._status

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def currency(self) -> AccountCurrency:
        return self._currency

    @property
    def priority(self) -> TransactionPriority:
        return self._priority

    @property
    def fee(self) -> Decimal:
        return self._fee

    @property
    def attempts(self) -> int:
        return self._attempts

    def get_transaction_info(self) -> dict[str, object]:
        return {
            "transaction_id": str(self.transaction_id),
            "transaction_type": self.transaction_type.value,
            "amount": self._amount,
            "currency": self._currency.value,
            "client_id": str(self.client_id),
            "sender_account_id": str(self.sender_account_id) if self.sender_account_id else None,
            "recipient_account_id": str(self.recipient_account_id) if self.recipient_account_id else None,
            "priority": self._priority.value,
            "status": self.status.value,
            "fee": self._fee,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at.isoformat(),
            "execute_after": self.execute_after.isoformat() if self.execute_after else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "attempts": self._attempts,
        }

    def __str__(self) -> str:
        return (
            f"Transaction | "
            f"ID: {str(self.transaction_id)[:8]} | "
            f"Type: {self.transaction_type.value} | "
            f"Amount: {self._amount:.2f} {self._currency.value} | "
            f"Status: {self.status.value} | "
            f"Attempts: {self._attempts}"
        )
