from decimal import Decimal

from bank_account import BankAccount
from exceptions import InvalidOperationError, InsufficientFundsError


class SavingsAccount(BankAccount):
    def __init__(
            self,
            first_name: str,
            last_name: str,
            balance: Decimal,
            min_balance: Decimal,
            monthly_interest_rate: Decimal,
            **kwargs
    ) -> None:
        super().__init__(
            first_name=first_name,
            last_name=last_name,
            balance=balance,
            **kwargs
        )
        self.validate_decimal_amount(min_balance)
        if (
                not isinstance(monthly_interest_rate, Decimal)
                or not monthly_interest_rate.is_finite()
                or monthly_interest_rate < 0
                or monthly_interest_rate != monthly_interest_rate.quantize(Decimal("0.00001"))
        ):
            raise ValueError(
                "Месячная ставка должна быть неотрицательным конечным Decimal с точностью до 5 знаков."
            )
        if balance < min_balance:
            raise ValueError(
                "Начальный баланс не может быть меньше минимального остатка."
            )
        self._min_balance = min_balance
        self._monthly_interest_rate = monthly_interest_rate

    @property
    def min_balance(self) -> Decimal:
        return self._min_balance

    @property
    def monthly_interest_rate(self) -> Decimal:
        return self._monthly_interest_rate

    def withdraw(self, amount: Decimal) -> Decimal:
        self.validate_status()
        self.validate_operation_amount(amount)
        if amount > self.balance:
            raise InsufficientFundsError(
                "Недостаточно средств для снятия."
            )
        if self.balance - amount < self.min_balance:
            raise InvalidOperationError(
                "Минимальный остаток не может быть нарушен."
            )
        return super().withdraw(amount)

    def apply_monthly_interest(self) -> Decimal:
        self.validate_status()
        interest = (
                self.balance * self.monthly_interest_rate
        ).quantize(Decimal("0.01"))
        if interest == 0:
            return self.balance
        return super().deposit(interest)

    def get_account_info(self) -> dict[str, str | Decimal]:
        account_info = super().get_account_info()
        account_info.update({
            "min_balance": self.min_balance,
            "monthly_interest_rate": self.monthly_interest_rate,
        })
        return account_info

    def __str__(self) -> str:
        parent_str = super().__str__()
        return f"{parent_str}\nМинимальный остаток: {self.min_balance}\nМесячная процентная ставка: {self.monthly_interest_rate}"
