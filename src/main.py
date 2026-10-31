from decimal import Decimal

from account import BankAccount
from enums import AccountStatus, AccountCurrency
from exceptions import AccountFrozenError

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
