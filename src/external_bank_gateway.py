import uuid
from decimal import Decimal
from external_account import ExternalAccount
from exceptions import InvalidOperationError


class ExternalBankGateway:
    def __init__(self) -> None:
        self._accounts: dict[uuid.UUID, ExternalAccount] = {}

    def register_account(
            self,
            account: ExternalAccount,
    ) -> None:
        if not isinstance(account, ExternalAccount):
            raise TypeError("account must be an instance of ExternalAccount.")
        if account.account_id in self._accounts:
            raise InvalidOperationError(
                f"Account with UUID {account.account_id} is already registered."
            )
        self._accounts[account.account_id] = account

    def _get_account(
            self,
            account_id: uuid.UUID,
    ) -> ExternalAccount:
        if not isinstance(account_id, uuid.UUID):
            raise TypeError("Account ID must be a UUID.")
        account = self._accounts.get(account_id)
        if account is None:
            raise InvalidOperationError(
                f"Account with UUID {account_id} not found."
            )
        return account

    def deposit(
            self,
            account_id: uuid.UUID,
            amount: Decimal,
    ) -> None:
        account = self._get_account(account_id)
        account.deposit(amount)
