
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from bank import Bank
from bank_account import BankAccount
from client import Client
from enums import AccountCurrency
from exceptions import InvalidOperationError


bank = Bank("Test Bank")

client = Client(
    first_name="Ivan",
    last_name="Petrov",
    date_of_birth=date(2000, 5, 15),
    email="ivan@example.com",
    phone="+79991234567",
    password="MySecurePassword123",
)

bank.add_client(client)

assert bank.authenticate_client(
    client.client_id,
    "MySecurePassword123",
)

account = BankAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("100.00"),
)

moscow = ZoneInfo("Europe/Moscow")

# Проверяем операции днём
with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 9, 12, 0, tzinfo=moscow
    )

    account_id = bank.open_account(
        client.client_id, account
    )

    assert bank.deposit(
        client.client_id,
        account_id,
        Decimal("25.00"),
    ) == Decimal("125.00")

# Проверяем ночное ограничение
with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 9, 2, 0, tzinfo=moscow
    )

    try:
        bank.withdraw(
            client.client_id,
            account_id,
            Decimal("10.00"),
        )
    except InvalidOperationError:
        pass
    else:
        raise AssertionError(
            "Ночная операция должна быть запрещена"
        )

# После ошибки баланс не изменился
assert account.balance == Decimal("125.00")

# Проверяем журнал безопасности
assert bank.security_events[-1]["action"] == "withdraw"

# Проверяем поиск
assert account in bank.search_accounts(
    client.client_id,
    currency=AccountCurrency.USD,
)

# Проверяем аналитику
assert bank.get_total_balance() == {
    "USD": Decimal("125.00"),
}

ranking = bank.get_clients_ranking(
    AccountCurrency.USD
)

assert ranking[0] == (client, Decimal("125.00"))

print("Bank Day 3: основные проверки пройдены!")
