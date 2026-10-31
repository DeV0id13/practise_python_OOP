class BankingError(Exception):
    """Базовая ошибка банковской системы."""


class AccountFrozenError(BankingError):
    """Счёт заморожен."""


class AccountClosedError(BankingError):
    """Счёт закрыт."""


class InvalidOperationError(BankingError):
    """Недопустимая операция."""


class InsufficientFundsError(BankingError):
    """Недостаточно средств."""
