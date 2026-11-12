import uuid
from decimal import Decimal, InvalidOperation
from premium_account import PremiumAccount
from external_bank_gateway import ExternalBankGateway
from client import Client
from bank_account import BankAccount
from exceptions import InvalidOperationError
from investment_account import InvestmentAccount
from enums import ClientStatus, AccountStatus, AccountCurrency
from datetime import datetime
from zoneinfo import ZoneInfo
from savings_account import SavingsAccount


class Bank:
    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Некорректное название банка.")

        self.name = name.strip()

        self._clients: dict[uuid.UUID, Client] = {}
        self._accounts: dict[uuid.UUID, BankAccount] = {}
        self._authenticated_clients: set[uuid.UUID] = set()
        self._security_events: list[dict[str, object]] = []

    def add_client(self, client: Client) -> None:
        if not isinstance(client, Client):
            raise TypeError("Expected Client instance.")
        if client.client_id in self._clients:
            raise ValueError(
                "Client with this UUID already exists."
            )
        if client.account_ids:
            raise InvalidOperationError(
                "Cannot register client with existing accounts."
            )
        self._clients[client.client_id] = client

    def get_client(self, client_id: uuid.UUID) -> Client:
        if not isinstance(client_id, uuid.UUID):
            raise TypeError("Incorrect client_id")
        client = self._clients.get(client_id)
        if client is None:
            raise InvalidOperationError(
                "Client with this UUID does not exist."
            )
        return client

    def open_account(
            self,
            client_id: uuid.UUID,
            account: BankAccount,
    ) -> uuid.UUID:
        self._check_authentication(client_id)
        self._check_working_hours(client_id, "open_account")
        client = self.get_client(client_id)
        if not isinstance(account, BankAccount):
            raise TypeError("account must be an instance of BankAccount or its subclass.")
        if account.account_id in self._accounts:
            raise ValueError("Account with this UUID already exists.")
        if account.first_name != client.first_name or account.last_name != client.last_name:
            raise ValueError("Account owner name and surname must match the client's data.")
        if account.account_status != AccountStatus.ACTIVE:
            raise InvalidOperationError(
                "Открываемый счёт должен быть активным."
            )
        client.add_account(account.account_id)
        self._accounts[account.account_id] = account
        return account.account_id

    def _get_client_account(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
    ) -> BankAccount:
        self._check_authentication(client_id)
        client = self.get_client(client_id)
        if not isinstance(account_id, uuid.UUID):
            raise TypeError("Incorrect account_id")
        account = self._accounts.get(account_id)
        if account is None or account_id not in client.account_ids:
            self._flag_suspicious_action(
                client_id,
                "account_access",
                "Попытка доступа к чужому или неизвестному счёту.",
            )
            raise InvalidOperationError(
                "Account does not exist for this client."
            )
        return account

    def freeze_account(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
    ) -> None:
        account = self._get_client_account(
            client_id, account_id
        )
        self._check_working_hours(client_id, "freeze_account")
        account.freeze()

    def unfreeze_account(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
    ) -> None:
        account = self._get_client_account(
            client_id, account_id
        )
        self._check_working_hours(client_id, "unfreeze_account")
        account.unfreeze()

    def close_account(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
    ) -> None:
        account = self._get_client_account(
            client_id, account_id
        )
        self._check_working_hours(client_id, "close_account")
        if isinstance(account, InvestmentAccount):
            if any(account.portfolio.values()):
                raise InvalidOperationError(
                    "Cannot close account with investments."
                )
        account.close()
        client = self.get_client(client_id)
        client.remove_account(account_id)
        del self._accounts[account_id]

    def authenticate_client(
            self,
            client_id: uuid.UUID,
            password: str,
    ) -> bool:
        client = self.get_client(client_id)
        if client.status == ClientStatus.BLOCKED:
            self._authenticated_clients.discard(client_id)
            self._flag_suspicious_action(
                client_id,
                "login",
                "Попытка входа заблокированного клиента.",
            )
            raise InvalidOperationError("Client is blocked.")
        result = client.authenticate(password)
        if result:
            self._authenticated_clients.add(client_id)
        else:
            self._authenticated_clients.discard(client_id)
            self._flag_suspicious_action(
                client_id,
                "login",
                "Неверный пароль.",
            )

            if client.status == ClientStatus.BLOCKED:
                self._flag_suspicious_action(
                    client_id,
                    "login",
                    "Клиент заблокирован после трёх попыток.",
                )
        return result

    def _check_authentication(
            self,
            client_id: uuid.UUID,
    ) -> None:
        client = self.get_client(client_id)
        if client.status != ClientStatus.ACTIVE:
            self._authenticated_clients.discard(client_id)
            raise InvalidOperationError(
                "Client is not active."
            )
        if client_id not in self._authenticated_clients:
            raise InvalidOperationError(
                "Client is not authenticated."
            )

    def _check_working_hours(
            self,
            client_id: uuid.UUID,
            action: str,
    ) -> None:
        current = datetime.now(ZoneInfo("Europe/Moscow"))
        if 0 <= current.hour < 5:
            self._flag_suspicious_action(
                client_id,
                action,
                "Попытка операции в запрещённое время.",
            )
            raise InvalidOperationError(
                "Операции запрещены с 00:00 до 05:00."
            )

    def _flag_suspicious_action(
            self,
            client_id: uuid.UUID,
            action: str,
            reason: str,
    ) -> None:
        current = datetime.now(ZoneInfo("Europe/Moscow"))
        event = {
            "client_id": str(client_id),
            "action": action,
            "reason": reason,
            "timestamp": current.isoformat(),
        }
        self._security_events.append(event)

    @property
    def security_events(self) -> tuple[dict[str, object], ...]:
        return tuple(
            event.copy()
            for event in self._security_events
        )

    def search_accounts(
            self,
            client_id: uuid.UUID,
            currency: AccountCurrency | None = None,
            status: AccountStatus | None = None,
            account_type: type[BankAccount] | None = None,
    ) -> tuple[BankAccount, ...]:
        self._check_authentication(client_id)
        if currency is not None and not isinstance(
                currency, AccountCurrency
        ):
            raise TypeError(
                "currency must be an instance of AccountCurrency."
            )
        if status is not None and not isinstance(
                status, AccountStatus
        ):
            raise TypeError(
                "status must be an instance of AccountStatus."
            )
        if account_type is not None:
            if (
                    not isinstance(account_type, type)
                    or not issubclass(account_type, BankAccount)
            ):
                raise TypeError(
                    "account_type must be a BankAccount subclass."
                )
        client = self.get_client(client_id)
        accounts = [
            self._accounts[account_id]
            for account_id in client.account_ids
        ]
        if currency is not None:
            accounts = [
                account for account in accounts
                if account.currency == currency
            ]
        if status is not None:
            accounts = [
                account for account in accounts
                if account.account_status == status
            ]
        if account_type is not None:
            accounts = [
                account for account in accounts
                if isinstance(account, account_type)
            ]
        return tuple(accounts)

    @staticmethod
    def _get_account_total_value(
            account: BankAccount,
    ) -> Decimal:
        total = account.balance
        if isinstance(account, InvestmentAccount):
            total += sum(
                account.portfolio.values(),
                Decimal("0.00"),
            )
        return total

    def get_total_balance(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}

        for account in self._accounts.values():
            currency = account.currency.value
            account_total = self._get_account_total_value(account)
            if currency not in totals:
                totals[currency] = Decimal("0.00")
            totals[currency] += account_total

        return totals

    def get_clients_ranking(
            self,
            currency: AccountCurrency,
    ) -> list[tuple[Client, Decimal]]:
        if not isinstance(currency, AccountCurrency):
            raise TypeError(
                "currency must be an instance of AccountCurrency."
            )
        ranking = []
        for client in self._clients.values():
            total = Decimal("0.00")

            for account_id in client.account_ids:
                account = self._accounts[account_id]

                if account.currency == currency:
                    total += self._get_account_total_value(account)

            ranking.append((client, total))
        ranking.sort(
            key=lambda item: item[1],
            reverse=True,
        )
        return ranking

    def deposit(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
            amount: Decimal,
    ) -> Decimal:
        account = self._get_client_account(client_id, account_id)
        self._check_working_hours(client_id, "deposit")
        return account.deposit(amount)

    def withdraw(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
            amount: Decimal,
    ) -> Decimal:
        account = self._get_client_account(client_id, account_id)
        self._check_working_hours(client_id, "withdraw")
        return account.withdraw(amount)

    def invest(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
            asset_type: str,
            amount: Decimal,
    ) -> None:
        account = self._get_client_account(client_id, account_id)
        self._check_working_hours(client_id, "invest")

        if not isinstance(account, InvestmentAccount):
            raise InvalidOperationError(
                "Этот счёт не поддерживает инвестиции."
            )

        account.invest(asset_type, amount)

    def apply_monthly_interest(
            self,
            client_id: uuid.UUID,
            account_id: uuid.UUID,
    ) -> Decimal:
        account = self._get_client_account(client_id, account_id)
        self._check_working_hours(
            client_id, "apply_monthly_interest"
        )

        if not isinstance(account, SavingsAccount):
            raise InvalidOperationError(
                "Это не накопительный счёт."
            )

        return account.apply_monthly_interest()

    def transfer(
            self,
            client_id: uuid.UUID,
            sender_account_id: uuid.UUID,
            recipient_account_id: uuid.UUID,
            amount: Decimal,
            currency: AccountCurrency,
    ) -> None:
        sender = self._get_client_account(
            client_id, sender_account_id
        )
        self._check_working_hours(client_id, "transfer")
        if not isinstance(recipient_account_id, uuid.UUID):
            raise TypeError("Invalid recipient account ID.")
        if sender_account_id == recipient_account_id:
            raise InvalidOperationError(
                "Cannot transfer to the same account."
            )
        recipient = self._accounts.get(recipient_account_id)
        if recipient is None:
            raise InvalidOperationError(
                "Recipient account does not exist."
            )
        if not isinstance(currency, AccountCurrency):
            raise TypeError("Invalid currency.")
        sender.validate_status()
        recipient.validate_status()
        sender.validate_operation_amount(amount)
        if sender.currency != currency or recipient.currency != currency:
            raise InvalidOperationError(
                "Account currencies must match."
            )
        if sender.balance < 0 and not isinstance(sender, PremiumAccount):
            raise InvalidOperationError(
                "Transfers from negative balances are prohibited."
            )
        sender_balance = sender.balance
        recipient_balance = recipient.balance
        try:
            sender.withdraw(amount)
            recipient.deposit(amount)
        except Exception:
            sender._balance = sender_balance
            recipient._balance = recipient_balance
            raise

    def external_transfer(
            self,
            client_id: uuid.UUID,
            sender_account_id: uuid.UUID,
            recipient_account_id: uuid.UUID,
            amount: Decimal,
            fee: Decimal,
            gateway: ExternalBankGateway,
            recipient_amount: Decimal | None = None,
    ) -> None:
        sender = self._get_client_account(
            client_id,
            sender_account_id,
        )
        self._check_working_hours(
            client_id,
            "external_transfer",
        )
        if not isinstance(gateway, ExternalBankGateway):
            raise TypeError(
                "gateway must be an ExternalBankGateway."
            )
        recipient = gateway._get_account(
            recipient_account_id
        )
        sender.validate_status()
        if recipient_amount is None:
            if sender.currency != recipient.currency:
                raise InvalidOperationError(
                    "Currency conversion is required."
                )
            recipient_amount = amount

        sender.validate_operation_amount(recipient_amount)
        sender.validate_operation_amount(amount)
        if not isinstance(fee, Decimal):
            raise TypeError("Fee must be a Decimal.")
        if not fee.is_finite() or fee < 0:
            raise ValueError(
                "Fee must be a non-negative finite Decimal."
            )
        try:
            if fee != fee.quantize(Decimal("0.01")):
                raise ValueError(
                    "Fee must have no more than 2 decimal places."
                )
        except InvalidOperation as exc:
            raise ValueError(
                "Invalid fee precision."
            ) from exc
        total = amount + fee
        sender.validate_operation_amount(total)
        sender_balance = sender.balance
        recipient_balance = recipient.balance
        try:
            sender.withdraw(total)
            gateway.deposit(
                account_id=recipient_account_id,
                amount=recipient_amount,
            )
        except Exception:
            sender._balance = sender_balance
            recipient._balance = recipient_balance
            raise
