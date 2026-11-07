from decimal import Decimal

from bank_account import BankAccount
from exceptions import InvalidOperationError, InsufficientFundsError


class InvestmentAccount(BankAccount):
    ALLOWED_ASSETS = ("stocks", "bonds", "etf")

    def __init__(
            self,
            first_name: str,
            last_name: str,
            balance: Decimal,
            **kwargs,
    ) -> None:
        super().__init__(
            first_name=first_name,
            last_name=last_name,
            balance=balance,
            **kwargs,
        )
        self._investments = {
            asset: Decimal("0.00")
            for asset in self.ALLOWED_ASSETS
        }

    @property
    def portfolio(self) -> dict[str, Decimal]:
        return self._investments.copy()

    def invest(
            self,
            asset_type: str,
            amount: Decimal,
    ) -> None:
        self.validate_status()
        if asset_type not in self.ALLOWED_ASSETS:
            raise InvalidOperationError(
                "Недопустимый тип актива."
            )
        self.validate_operation_amount(amount)
        if amount > self.balance:
            raise InsufficientFundsError("Недостаточно свободных средств")
        super().withdraw(amount)
        self._investments[asset_type] += amount

    def withdraw(self, amount: Decimal) -> Decimal:
        return super().withdraw(amount)

    def project_yearly_growth(
            self,
            growth_rates: dict[str, Decimal],
    ) -> Decimal:
        if not isinstance(growth_rates, dict):
            raise TypeError(
                "Ставки доходности должны быть словарём."
            )
        if growth_rates.keys() != set(self.ALLOWED_ASSETS):
            raise InvalidOperationError(
                "Неверный набор типов активов."
            )
        for rate in growth_rates.values():
            if not isinstance(rate, Decimal) or not rate.is_finite():
                raise ValueError("Некорректная ставка доходности.")
        total_growth = Decimal("0.00")
        for asset_type, amount in self.portfolio.items():
            rate = growth_rates[asset_type]
            total_growth += rate * amount
        return total_growth.quantize(Decimal("0.01"))

    def get_account_info(self) -> dict[str, object]:
        account_info = super().get_account_info()
        account_info.update({
            "investments": self.portfolio,
        })
        return account_info

    def __str__(self) -> str:
        parent_str = super().__str__()
        investments_str = "\n".join(
            f"{asset}: {amount:.2f} {self.currency.value}"
            for asset, amount in self.portfolio.items()
        )
        return f"{parent_str}\nИнвестиции:\n{investments_str}"
