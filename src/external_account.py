import uuid
from decimal import Decimal, InvalidOperation

from enums import AccountCurrency


class ExternalAccount:
    def __init__(
            self,
            currency: AccountCurrency,
            balance: Decimal = Decimal("0.00"),
            account_id: uuid.UUID | None = None,
    ) -> None:
        if not isinstance(currency, AccountCurrency):
            raise TypeError(
                "Currency must be an instance of AccountCurrency."
            )
        if not isinstance(balance, Decimal):
            raise TypeError("Balance must be a Decimal.")
        if not balance.is_finite() or balance < 0:
            raise ValueError(
                "Balance must be a non-negative finite Decimal."
            )
        try:
            if balance != balance.quantize(Decimal("0.01")):
                raise ValueError(
                    "Balance must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError("Invalid balance precision.") from exc
        if account_id is not None and not isinstance(account_id, uuid.UUID):
            raise ValueError("Account ID must be a valid UUID.")
        if account_id is None:
            account_id = uuid.uuid4()
        self.currency = currency
        self._balance = balance
        self.account_id = account_id

    def deposit(self, amount: Decimal) -> None:
        if not isinstance(amount, Decimal):
            raise TypeError("Amount must be a Decimal.")
        if not amount.is_finite() or amount <= 0:
            raise ValueError("Amount must be a positive finite Decimal.")
        try:
            if amount != amount.quantize(Decimal("0.01")):
                raise ValueError(
                    "Amount must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError("Invalid amount precision.") from exc
        self._balance += amount

    @property
    def balance(self) -> Decimal:
        return self._balance
