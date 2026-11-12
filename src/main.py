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

from datetime import date
import uuid

from client import Client


client = Client(
    first_name="Ivan",
    last_name="Petrov",
    date_of_birth=date(2000, 5, 15),
    email="ivan@example.com",
    phone="+79991234567",
    password="12345678923456"
)

assert len(client.account_ids) == 0
assert client.status.value == "active"

account_id = uuid.uuid4()

client.add_account(account_id)
assert account_id in client.account_ids

info = client.get_client_info()
assert info["account_ids"] == [str(account_id)]

# Изменение возвращённого списка не влияет на клиента
info["account_ids"].clear()
assert account_id in client.account_ids

client.remove_account(account_id)
assert len(client.account_ids) == 0

print(client)
print("Client: основные проверки пройдены!")

from datetime import date

from client import Client

client = Client(
    first_name="Ivan",
    last_name="Petrov",
    date_of_birth=date(2000, 5, 15),
    email="ivan@example.com",
    phone="+79991234567",
    password="MySecurePassword123",
)

assert client.verify_password("MySecurePassword123") is True
assert client.verify_password("WrongPassword123") is False
assert client._failed_login_attempts == 0

print("Проверка пароля работает корректно!")


from datetime import date

from client import Client
from enums import ClientStatus

client = Client(
    first_name="Ivan",
    last_name="Petrov",
    date_of_birth=date(2000, 5, 15),
    email="ivan@example.com",
    phone="+79991234567",
    password="MySecurePassword123",
)

# Первая неправильная попытка
assert client.authenticate("wrong1") is False
assert client._failed_login_attempts == 1
assert client.status == ClientStatus.ACTIVE

# Вторая неправильная попытка
assert client.authenticate("wrong2") is False
assert client._failed_login_attempts == 2

# Успешный вход сбрасывает счётчик
assert client.authenticate("MySecurePassword123") is True
assert client._failed_login_attempts == 0

# Три неправильных пароля подряд
for _ in range(3):
    assert client.authenticate("wrong") is False

# Клиент заблокирован
assert client.status == ClientStatus.BLOCKED
assert client._failed_login_attempts == 3

# Даже правильный пароль больше не работает
try:
    client.authenticate("MySecurePassword123")
except ValueError:
    pass
else:
    raise AssertionError("Expected blocked client error")

print("Все проверки авторизации пройдены!")


from datetime import date

from client import Client
from enums import ClientStatus


client = Client(
    first_name="Ivan",
    last_name="Petrov",
    date_of_birth=date(2000, 5, 15),
    email="ivan@example.com",
    phone="+79991234567",
    password="MySecurePassword123",
)

# Две неудачные попытки
assert client.authenticate("wrong1") is False
assert client.authenticate("wrong2") is False

assert client.status == ClientStatus.ACTIVE

# Успешный вход сбрасывает счётчик
assert client.authenticate("MySecurePassword123") is True
assert client._failed_login_attempts == 0

# Три неудачные попытки подряд
for _ in range(3):
    assert client.authenticate("wrong") is False

assert client.status == ClientStatus.BLOCKED
assert client._failed_login_attempts == 3

# Заблокированный клиент не может войти
try:
    client.authenticate("MySecurePassword123")
except ValueError:
    pass
else:
    raise AssertionError("Blocked client authenticated")

print("Client authentication: tests passed!")


from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from bank import Bank
from bank_account import BankAccount
from client import Client
from transaction import Transaction
from transaction_processor import TransactionProcessor
from enums import (
    AccountCurrency,
    TransactionType,
    TransactionStatus,
)


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
    balance=Decimal("1000.00"),
    currency=AccountCurrency.USD,
)

moscow = ZoneInfo("Europe/Moscow")

# Подменяем время на 12:00, чтобы тест
# не зависел от реального времени суток.
with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 11, 12, 0, tzinfo=moscow
    )

    bank.open_account(client.client_id, account)

    processor = TransactionProcessor(bank)

    # Успешное пополнение
    deposit_tx = Transaction(
        transaction_type=TransactionType.DEPOSIT,
        amount=Decimal("500.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        recipient_account_id=account.account_id,
    )

    processor.process(deposit_tx)

    assert deposit_tx.status == TransactionStatus.COMPLETED
    assert deposit_tx.attempts == 1
    assert deposit_tx.fee == Decimal("0.00")
    assert account.balance == Decimal("1500.00")

    # Недостаточно средств
    withdraw_tx = Transaction(
        transaction_type=TransactionType.WITHDRAWAL,
        amount=Decimal("2000.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        sender_account_id=account.account_id,
    )

    processor.process(withdraw_tx)

    assert withdraw_tx.status == TransactionStatus.FAILED
    assert withdraw_tx.attempts == 1
    assert withdraw_tx.failure_reason is not None
    assert account.balance == Decimal("1500.00")

print("TransactionProcessor: tests passed!")



# Создаём два счёта
sender = BankAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("1000.00"),
    currency=AccountCurrency.USD,
)

recipient = BankAccount(
    first_name="Ivan",
    last_name="Petrov",
    balance=Decimal("500.00"),
    currency=AccountCurrency.USD,
)

# Подменяем время для всех банковских операций
with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 11, 12, 0, tzinfo=moscow
    )

    # Регистрируем счета в банке
    bank.open_account(client.client_id, sender)
    bank.open_account(client.client_id, recipient)

    # Тест 1: успешный перевод
    transfer_tx = Transaction(
        transaction_type=TransactionType.INTERNAL_TRANSFER,
        amount=Decimal("300.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        sender_account_id=sender.account_id,
        recipient_account_id=recipient.account_id,
    )

    processor.process(transfer_tx)

    assert transfer_tx.status == TransactionStatus.COMPLETED
    assert transfer_tx.attempts == 1
    assert sender.balance == Decimal("700.00")
    assert recipient.balance == Decimal("800.00")

    print("Successful transfer: passed!")

    # Тест 2: откат при ошибке
    sender_balance_before = sender.balance
    recipient_balance_before = recipient.balance

    failed_tx = Transaction(
        transaction_type=TransactionType.INTERNAL_TRANSFER,
        amount=Decimal("100.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        sender_account_id=sender.account_id,
        recipient_account_id=recipient.account_id,
    )

    with patch.object(
        recipient,
        "deposit",
        side_effect=InvalidOperationError("Deposit failed"),
    ):
        processor.process(failed_tx)

    assert failed_tx.status == TransactionStatus.FAILED
    assert failed_tx.failure_reason == "Deposit failed"

    assert sender.balance == sender_balance_before
    assert recipient.balance == recipient_balance_before

    print("Transfer rollback: passed!")

external_tx = Transaction(
    transaction_type=TransactionType.EXTERNAL_TRANSFER,
    amount=Decimal("125.50"),
    currency=AccountCurrency.USD,
    client_id=client.client_id,
    sender_account_id=sender.account_id,
    recipient_account_id=recipient.account_id,
)

assert processor._calculate_fee(
    external_tx
) == Decimal("1.26")

assert processor._calculate_fee(
    transfer_tx
) == Decimal("0.00")

print("Transaction fees: tests passed!")

from external_account import ExternalAccount
from external_bank_gateway import ExternalBankGateway
from transaction_queue import TransactionQueue

gateway = ExternalBankGateway()

external_recipient = ExternalAccount(
    currency=AccountCurrency.EUR,
    balance=Decimal("500.00"),
)
gateway.register_account(external_recipient)

processor = TransactionProcessor(bank, gateway)
queue = TransactionQueue()

# 5 пополнений
for _ in range(5):
    queue.add_transaction(Transaction(
        transaction_type=TransactionType.DEPOSIT,
        amount=Decimal("1.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        recipient_account_id=account.account_id,
    ))

# 2 снятия
for _ in range(2):
    queue.add_transaction(Transaction(
        transaction_type=TransactionType.WITHDRAWAL,
        amount=Decimal("2.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        sender_account_id=account.account_id,
    ))

# 2 внутренних перевода
for _ in range(2):
    queue.add_transaction(Transaction(
        transaction_type=TransactionType.INTERNAL_TRANSFER,
        amount=Decimal("10.00"),
        currency=AccountCurrency.USD,
        client_id=client.client_id,
        sender_account_id=sender.account_id,
        recipient_account_id=recipient.account_id,
    ))

# 1 внешний перевод с USD в EUR
external_transfer_tx = Transaction(
    transaction_type=TransactionType.EXTERNAL_TRANSFER,
    amount=Decimal("100.00"),
    currency=AccountCurrency.USD,
    client_id=client.client_id,
    sender_account_id=sender.account_id,
    recipient_account_id=external_recipient.account_id,
)
queue.add_transaction(external_transfer_tx)

# Выполняем операции в разрешённое время
with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 11, 12, 0, tzinfo=moscow
    )
    processor.process_queue(queue)

assert len(queue) == 10
assert queue.get_next_transaction() is None

assert all(
    tx.status == TransactionStatus.COMPLETED
    for tx in queue._transactions
)

assert account.balance == Decimal("1501.00")
assert sender.balance == Decimal("579.00")
assert recipient.balance == Decimal("820.00")
assert external_recipient.balance == Decimal("592.00")
assert external_transfer_tx.fee == Decimal("1.00")

print("Day 4: 10 transactions passed!")

failed_tx = Transaction(
    transaction_type=TransactionType.WITHDRAWAL,
    amount=Decimal("99999.00"),
    currency=AccountCurrency.USD,
    client_id=client.client_id,
    sender_account_id=sender.account_id,
)

with patch("bank.datetime") as mock_datetime:
    mock_datetime.now.return_value = datetime(
        2026, 11, 11, 12, 0, tzinfo=moscow
    )

    processor.process(failed_tx)
    assert failed_tx.status == TransactionStatus.FAILED
    assert len(processor.error_log) == 1

    processor.retry(failed_tx)
    assert failed_tx.status == TransactionStatus.PENDING

    processor.process(failed_tx)
    assert failed_tx.attempts == 2
    assert failed_tx.status == TransactionStatus.FAILED

print("Day 4: retry and error logging passed!")


# Проверки замечаний

from uuid import uuid4

test_processor = TransactionProcessor(bank)

# 1. Пополнение USD-счёта в EUR
wrong_currency_deposit = Transaction(
    transaction_type=TransactionType.DEPOSIT,
    amount=Decimal("100.00"),
    currency=AccountCurrency.EUR,
    client_id=client.client_id,
    recipient_account_id=account.account_id,
)

balance_before = account.balance
test_processor.process(wrong_currency_deposit)

assert wrong_currency_deposit.status == TransactionStatus.FAILED
assert account.balance == balance_before
assert wrong_currency_deposit.failure_reason is not None

# 2. Снятие EUR с USD-счёта
wrong_currency_withdraw = Transaction(
    transaction_type=TransactionType.WITHDRAWAL,
    amount=Decimal("100.00"),
    currency=AccountCurrency.EUR,
    client_id=client.client_id,
    sender_account_id=account.account_id,
)

test_processor.process(wrong_currency_withdraw)

assert wrong_currency_withdraw.status == TransactionStatus.FAILED
assert account.balance == balance_before

# 3. Неизвестный клиент
unknown_client_tx = Transaction(
    transaction_type=TransactionType.DEPOSIT,
    amount=Decimal("100.00"),
    currency=AccountCurrency.USD,
    client_id=uuid4(),
    recipient_account_id=account.account_id,
)

test_processor.process(unknown_client_tx)

assert unknown_client_tx.status == TransactionStatus.FAILED
assert unknown_client_tx.failure_reason is not None
assert unknown_client_tx.attempts == 1
assert account.balance == balance_before

# Все три ошибки записаны
assert len(test_processor.error_log) == 3

print("reviews: all tests passed!")
