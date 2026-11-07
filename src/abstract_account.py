from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
import uuid

from exceptions import (
    AccountClosedError,
    AccountFrozenError,
    InvalidOperationError,
)
from enums import AccountStatus


class AbstractAccount(ABC):
    def __init__(
            self,
            first_name: str,
            last_name: str,
            balance: Decimal = Decimal("0.00"),
            account_status: AccountStatus = AccountStatus.ACTIVE,
            account_id: uuid.UUID | None = None,
    ) -> None:
        if account_id is None:
            self.account_id = uuid.uuid4()
        elif not isinstance(account_id, uuid.UUID):
            raise ValueError("Account ID must be a valid UUID.")
        else:
            self.account_id = account_id

        if not (
                isinstance(first_name, str) and first_name.strip()
        ) or not (
                isinstance(last_name, str) and last_name.strip()
        ):
            raise ValueError(
                "First name and last name must be non-empty strings."
            )

        self.validate_decimal_amount(balance)

        if not isinstance(account_status, AccountStatus):
            raise ValueError(
                "Account status must be an instance of AccountStatus."
            )

        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self._balance = balance
        self._account_status = account_status

    def validate_status(self) -> None:
        if self.account_status == AccountStatus.FROZEN:
            raise AccountFrozenError("Account is frozen.")

        if self.account_status == AccountStatus.CLOSED:
            raise AccountClosedError("Account is closed.")

    @staticmethod
    def validate_decimal_amount(number: Decimal) -> None:
        if (
                not isinstance(number, Decimal)
                or not number.is_finite()
                or number < 0
        ):
            raise ValueError(
                "Amount must be a non-negative finite Decimal."
            )

        try:
            if number != number.quantize(Decimal("0.01")):
                raise ValueError(
                    "Amount must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError(
                "Invalid amount precision."
            ) from exc

    @classmethod
    def validate_operation_amount(
            cls,
            amount: Decimal,
    ) -> None:
        try:
            cls.validate_decimal_amount(amount)
        except ValueError as exc:
            raise InvalidOperationError(str(exc)) from exc

        if amount == 0:
            raise InvalidOperationError(
                "Operation amount must be positive."
            )

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def account_status(self) -> AccountStatus:
        return self._account_status

    @property
    def short_account_id(self) -> str:
        return f"{self.account_id.int % 10 ** 12:012d}"

    def freeze(self) -> None:
        self.validate_status()
        self._account_status = AccountStatus.FROZEN

    def unfreeze(self) -> None:
        if self.account_status == AccountStatus.CLOSED:
            raise AccountClosedError(
                "Closed account cannot be unfrozen."
            )

        if self.account_status != AccountStatus.FROZEN:
            raise InvalidOperationError(
                "Account is not frozen."
            )

        self._account_status = AccountStatus.ACTIVE

    def close(self) -> None:
        self.validate_status()

        if self.balance != Decimal("0.00"):
            raise InvalidOperationError(
                "Account balance must be zero before closing."
            )

        self._account_status = AccountStatus.CLOSED

    @abstractmethod
    def deposit(self, amount: Decimal) -> Decimal:
        pass

    @abstractmethod
    def withdraw(self, amount: Decimal) -> Decimal:
        pass

    @abstractmethod
    def get_account_info(self) -> dict[str, str | Decimal]:
        pass
