from exceptions import BankingError
from enums import TransactionStatus
from decimal import Decimal, ROUND_HALF_UP
from bank import Bank
from transaction import Transaction
from enums import TransactionType, AccountCurrency
from exceptions import InvalidOperationError
from external_bank_gateway import ExternalBankGateway
from datetime import datetime, timezone
from transaction_queue import TransactionQueue


class TransactionProcessor:
    FX_PER_USD = {
        AccountCurrency.USD: Decimal("1"),
        AccountCurrency.EUR: Decimal("0.92"),
        AccountCurrency.RUB: Decimal("90"),
        AccountCurrency.KZT: Decimal("500"),
        AccountCurrency.CNY: Decimal("7.2"),
    }

    MAX_ATTEMPTS = 3

    def __init__(
            self,
            bank: Bank,
            external_gateway: ExternalBankGateway | None = None,
    ) -> None:
        if not isinstance(bank, Bank):
            raise TypeError("bank must be an instance of Bank.")
        if external_gateway is not None and not isinstance(external_gateway, ExternalBankGateway):
            raise TypeError("external_gateway must be an instance of ExternalBankGateway or None.")
        self._external_gateway = external_gateway
        self._bank = bank
        self._error_log: list[dict[str, object]] = []

    @property
    def error_log(self) -> tuple[dict[str, object], ...]:
        return tuple(entry.copy() for entry in self._error_log)

    def _execute(
            self,
            transaction: Transaction,
            fee: Decimal = Decimal("0.00"),
    ) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Expected Transaction instance.")
        if transaction.transaction_type == TransactionType.DEPOSIT:
            account = self._bank._get_client_account(
                client_id=transaction.client_id,
                account_id=transaction.recipient_account_id,
            )

            if account.currency != transaction.currency:
                raise InvalidOperationError(
                    "Transaction currency does not match account currency."
                )

            self._bank.deposit(
                client_id=transaction.client_id,
                account_id=transaction.recipient_account_id,
                amount=transaction.amount,
            )

        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            account = self._bank._get_client_account(
                client_id=transaction.client_id,
                account_id=transaction.sender_account_id,
            )

            if account.currency != transaction.currency:
                raise InvalidOperationError(
                    "Transaction currency does not match account currency."
                )

            self._bank.withdraw(
                client_id=transaction.client_id,
                account_id=transaction.sender_account_id,
                amount=transaction.amount,
            )
        elif transaction.transaction_type == TransactionType.INTERNAL_TRANSFER:
            self._bank.transfer(
                client_id=transaction.client_id,
                sender_account_id=transaction.sender_account_id,
                recipient_account_id=transaction.recipient_account_id,
                amount=transaction.amount,
                currency=transaction.currency,
            )
        elif transaction.transaction_type == TransactionType.EXTERNAL_TRANSFER:
            target_currency = self._validate_external_transfer(
                transaction
            )
            converted_amount = self._convert_amount(
                transaction.amount,
                transaction.currency,
                target_currency,
            )
            assert self._external_gateway is not None
            self._bank.external_transfer(
                client_id=transaction.client_id,
                sender_account_id=transaction.sender_account_id,
                recipient_account_id=transaction.recipient_account_id,
                amount=transaction.amount,
                fee=fee,
                gateway=self._external_gateway,
                recipient_amount=converted_amount,
            )
        else:
            raise InvalidOperationError(
                f"Transaction type {transaction.transaction_type} is not supported."
            )

    def _calculate_fee(
            self,
            transaction: Transaction,
    ) -> Decimal:
        if transaction.transaction_type == TransactionType.EXTERNAL_TRANSFER:
            return (transaction.amount * Decimal("0.01")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        return Decimal("0.00")

    def _convert_amount(
            self,
            amount: Decimal,
            source: AccountCurrency,
            target: AccountCurrency,
    ) -> Decimal:
        return (
                amount
                / self.FX_PER_USD[source]
                * self.FX_PER_USD[target]
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def process(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Expected Transaction instance.")

        if transaction.status != TransactionStatus.PENDING:
            raise InvalidOperationError(
                "Transaction is not pending."
            )

        if (
                transaction.execute_after is not None
                and transaction.execute_after > datetime.now(timezone.utc)
        ):
            raise InvalidOperationError(
                "Transaction is scheduled for later."
            )

        transaction.start_processing()

        try:
            fee = self._calculate_fee(transaction)
            self._execute(transaction, fee)
            transaction.complete(fee)

        except BankingError as exc:
            reason = str(exc) or type(exc).__name__
            transaction.fail(reason)

            self._error_log.append({
                "transaction_id": str(transaction.transaction_id),
                "attempt": transaction.attempts,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
            })

    def _validate_external_transfer(
            self,
            transaction: Transaction,
    ) -> AccountCurrency:
        if self._external_gateway is None:
            raise InvalidOperationError(
                "External gateway is not configured."
            )
        sender = self._bank._get_client_account(
            client_id=transaction.client_id,
            account_id=transaction.sender_account_id,
        )
        sender.validate_status()
        if sender.currency != transaction.currency:
            raise InvalidOperationError(
                "Sender currency mismatch."
            )
        external_account = self._external_gateway._get_account(
            transaction.recipient_account_id
        )
        return external_account.currency

    def retry(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Expected Transaction instance.")

        if transaction.status != TransactionStatus.FAILED:
            raise InvalidOperationError(
                "Only failed transactions can be retried."
            )

        if transaction.attempts >= self.MAX_ATTEMPTS:
            raise InvalidOperationError(
                "Maximum processing attempts exceeded."
            )

        transaction.change_status(TransactionStatus.PENDING)

    def process_queue(self, queue: TransactionQueue) -> None:
        if not isinstance(queue, TransactionQueue):
            raise TypeError("Expected TransactionQueue instance.")

        while True:
            transaction = queue.get_next_transaction()

            if transaction is None:
                break

            self.process(transaction)
