from decimal import Decimal

from bank_account import BankAccount

from exceptions import InvalidOperationError, InsufficientFundsError


class PremiumAccount(BankAccount):
    def __init__(
            self,
            first_name: str,
            last_name: str,
            balance: Decimal,
            overdraft_limit: Decimal,
            withdrawal_limit: Decimal,
            transaction_fee: Decimal,
            **kwargs,
    ) -> None:
        super().__init__(
            first_name=first_name,
            last_name=last_name,
            balance=balance,
            **kwargs,
        )
        self.validate_decimal_amount(transaction_fee)
        self._transaction_fee = transaction_fee
        self.validate_decimal_amount(overdraft_limit)
        self._overdraft_limit = overdraft_limit
        self.validate_decimal_amount(withdrawal_limit)
        if withdrawal_limit == 0:
            raise ValueError(
                "Лимит одной транзакции должен быть положительным."
            )
        self._withdrawal_limit = withdrawal_limit

    @property
    def overdraft_limit(self) -> Decimal:
        return self._overdraft_limit

    @property
    def withdrawal_limit(self) -> Decimal:
        return self._withdrawal_limit

    @property
    def transaction_fee(self) -> Decimal:
        return self._transaction_fee

    def withdraw(self, amount: Decimal) -> Decimal:
        self.validate_status()
        self.validate_operation_amount(amount)
        if amount > self.withdrawal_limit:
            raise InvalidOperationError("Сумма снятия превышает лимит")
        withdrawal_amount = amount + self.transaction_fee
        if self.balance - withdrawal_amount < -self.overdraft_limit:
            raise InsufficientFundsError(
                "Недостаточно средств с учётом овердрафта."
            )
        self._balance -= withdrawal_amount
        return self.balance

    def get_account_info(self) -> dict[str, str | Decimal]:
        account_info = super().get_account_info()
        account_info.update({
            "overdraft_limit": self.overdraft_limit,
            "withdrawal_limit": self.withdrawal_limit,
            "transaction_fee": self.transaction_fee,
        })
        return account_info

    def __str__(self) -> str:
        parent_str = super().__str__()
        return (
            f"{parent_str}\nЛимит овердрафта: {self.overdraft_limit}\nЛимит одной транзакции: {self.withdrawal_limit}"
            f"\nКомиссия: {self.transaction_fee}")
