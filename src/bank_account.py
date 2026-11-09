from abstract_account import AbstractAccount
from exceptions import InsufficientFundsError
from decimal import Decimal
from enums import AccountStatus, AccountCurrency
import uuid


class BankAccount(AbstractAccount):
    def __init__(
            self,
            first_name: str,
            last_name: str,
            balance: Decimal = Decimal("0.00"),
            account_status: AccountStatus = AccountStatus.ACTIVE,
            account_id: uuid.UUID | None = None,
            currency: AccountCurrency = AccountCurrency.USD,
    ) -> None:
        if not isinstance(currency, AccountCurrency):
            raise ValueError(
                "Currency must be an instance of AccountCurrency."
            )

        super().__init__(
            first_name,
            last_name,
            balance,
            account_status,
            account_id,
        )

        self.currency = currency

    def get_account_info(self) -> dict[str, str | Decimal]:
        return {
            "account_type": type(self).__name__,
            "account_id": str(self.account_id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "balance": self.balance,
            "account_status": self.account_status.value,
            "currency": self.currency.value,
        }

    def withdraw(self, amount: Decimal) -> Decimal:
        self.validate_status()
        self.validate_operation_amount(amount)

        if amount > self.balance:
            raise InsufficientFundsError(
                "Insufficient funds."
            )

        self._balance -= amount
        return self._balance

    def deposit(self, amount: Decimal) -> Decimal:
        self.validate_status()
        self.validate_operation_amount(amount)

        self._balance += amount
        return self._balance

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} | "
            f"{self.first_name} {self.last_name} | "
            f"****{self.short_account_id[-4:]} | "
            f"{self.account_status.value} | "
            f"{self.balance:.2f} {self.currency.value}"
        )
