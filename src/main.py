from decimal import Decimal

from bank_account import BankAccount
from savings_account import SavingsAccount
from enums import AccountStatus, AccountCurrency
from exceptions import AccountFrozenError, BankingError

active_account = BankAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("1000.00"),
    account_status=AccountStatus.ACTIVE,
    currency=AccountCurrency.USD,
)

frozen_account = BankAccount(
    first_name="Alex",
    last_name="Smith",
    balance=Decimal("500.00"),
    account_status=AccountStatus.FROZEN,
)

active_account.deposit(Decimal("250.00"))
active_account.withdraw(Decimal("100.00"))

print(active_account.balance)
# 1150.00

try:
    frozen_account.deposit(Decimal("50.00"))
except AccountFrozenError as exc:
    print(exc)
    # Account is frozen.

print(active_account)
# BankAccount | Ivan Petrov | ****4625 |
# active | 1150.00 USD
# (4625 — пример случайно сформированного номера)


account = SavingsAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("1000.00"),
    min_balance=Decimal("200.00"),
    monthly_interest_rate=Decimal("0.01"),
)
print(account)
account.withdraw(Decimal("500.00"))
print(account.balance)
# 500.00
try:
    account.withdraw(Decimal("400.00"))
except BankingError as exc:
    print(exc)
    print(exc.__class__)
# InvalidOperationError
# Минимальный остаток не может быть нарушен.

account.apply_monthly_interest()
print(account.balance)
# 505.00


from decimal import Decimal

from exceptions import InvalidOperationError

# Минимальный остаток должен сохраняться
account = SavingsAccount(
    "Ivan",
    "Petrov",
    Decimal("1000"),
    Decimal("200"),
    Decimal("0.01"),
)

assert account.withdraw(Decimal("800")) == Decimal("200")

try:
    account.withdraw(Decimal("1"))
except InvalidOperationError:
    pass
else:
    raise AssertionError("Expected InvalidOperationError")

assert account.balance == Decimal("200")

# Начисление процентов
assert account.apply_monthly_interest() == Decimal("202.00")

# Информация о счёте
info = account.get_account_info()
assert info["min_balance"] == Decimal("200")
assert info["monthly_interest_rate"] == Decimal("0.01")

from decimal import Decimal

from premium_account import PremiumAccount
from exceptions import (
    InvalidOperationError,
    InsufficientFundsError,
)

account = PremiumAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("100"),
    overdraft_limit=Decimal("500"),
    withdrawal_limit=Decimal("600"),
    transaction_fee=Decimal("5"),
)

# Обычное снятие
assert account.withdraw(Decimal("50")) == Decimal("45")

# Снятие с использованием овердрафта
assert account.withdraw(Decimal("300")) == Decimal("-260")

# Превышение лимита овердрафта
try:
    account.withdraw(Decimal("300"))
except InsufficientFundsError:
    pass
else:
    raise AssertionError("Expected InsufficientFundsError")

# Баланс не изменился после неудачного снятия
assert account.balance == Decimal("-260")

# Погашение задолженности пополнением
assert account.deposit(Decimal("300")) == Decimal("40")

# Превышение лимита одной операции
try:
    account.withdraw(Decimal("601"))
except InvalidOperationError:
    pass
else:
    raise AssertionError("Expected InvalidOperationError")

assert account.balance == Decimal("40")

# Проверка информации о счёте
info = account.get_account_info()

assert info["overdraft_limit"] == Decimal("500")
assert info["withdrawal_limit"] == Decimal("600")
assert info["transaction_fee"] == Decimal("5")

print(account)
print("PremiumAccount: все проверки пройдены!")

from decimal import Decimal

from investment_account import InvestmentAccount

account = InvestmentAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("10000.00"),
)

account.invest("stocks", Decimal("3000.00"))
account.invest("bonds", Decimal("2000.00"))
account.invest("etf", Decimal("1000.00"))

growth_rates = {
    "stocks": Decimal("0.10"),
    "bonds": Decimal("0.04"),
    "etf": Decimal("0.07"),
}

assert account.balance == Decimal("4000.00")

assert account.project_yearly_growth(
    growth_rates
) == Decimal("450.00")

# Проверяем отрицательную доходность
negative_rates = {
    "stocks": Decimal("-0.05"),
    "bonds": Decimal("0.04"),
    "etf": Decimal("0.07"),
}

assert account.project_yearly_growth(
    negative_rates
) == Decimal("0.00")

# Прогноз не должен изменять состояние счёта
assert account.balance == Decimal("4000.00")
assert account.portfolio["stocks"] == Decimal("3000.00")

# Проверяем защиту внутреннего словаря
portfolio = account.portfolio
portfolio["stocks"] = Decimal("999999")

assert account.portfolio["stocks"] == Decimal("3000.00")

print(account)
print("InvestmentAccount: проверки пройдены!")
