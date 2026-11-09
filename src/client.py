import uuid
from datetime import date
import hashlib
import secrets
import hmac
from enums import ClientStatus


class Client:
    MAX_LOGIN_ATTEMPTS = 3

    def __init__(
            self,
            first_name: str,
            last_name: str,
            date_of_birth: date,
            email: str,
            phone: str,
            password: str,
            client_id: uuid.UUID | None = None,
    ) -> None:
        if client_id is None:
            self._client_id = uuid.uuid4()
        elif not isinstance(client_id, uuid.UUID):
            raise ValueError("Client ID must be a valid UUID.")
        else:
            self._client_id = client_id
        if not (
                isinstance(first_name, str) and first_name.strip()
        ) or not (
                isinstance(last_name, str) and last_name.strip()
        ):
            raise ValueError(
                "First name and last name must be non-empty strings."
            )
        if not isinstance(date_of_birth, date):
            raise TypeError("Incorrect data format")
        today = date.today()
        age = today.year - date_of_birth.year
        if (today.month, today.day) < (
                date_of_birth.month,
                date_of_birth.day,
        ):
            age -= 1
        if age < 18:
            raise ValueError(
                "Клиент должен быть совершеннолетним."
            )
        self._date_of_birth = date_of_birth
        if not isinstance(email, str):
            raise TypeError("Email must be a string.")
        email = email.strip()
        if email.count("@") != 1:
            raise ValueError("Некорректный email.")
        local, domain = email.split("@")
        domain_parts = domain.rsplit(".", 1)
        if (
                not local
                or len(domain_parts) != 2
                or not all(domain_parts)
        ):
            raise ValueError("Некорректный email.")
        if not isinstance(phone, str):
            raise TypeError("Phone must be a string.")
        phone = phone.strip()
        digits = phone.removeprefix("+")
        if (
                not digits.isascii()
                or not digits.isdigit()
                or not 10 <= len(digits) <= 15
        ):
            raise ValueError("Некорректный номер телефона.")
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self._phone = phone
        self._email = email
        self._client_status = ClientStatus.ACTIVE
        self._account_ids: list[uuid.UUID] = []

        if not isinstance(password, str):
            raise TypeError("Password must be a string.")

        if len(password) < 12:
            raise ValueError(
                "Пароль должен содержать минимум 12 символов."
            )
        self._password_salt = secrets.token_bytes(16)
        self._password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self._password_salt,
            600_000,
        )
        self._failed_login_attempts = 0

    def verify_password(self, password: str) -> bool:
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self._password_salt,
            600_000,
        )
        return hmac.compare_digest(
            self._password_hash,
            password_hash,
        )

    def authenticate(self, password: str) -> bool:
        if self.status == ClientStatus.BLOCKED:
            raise ValueError("Клиент заблокирован.")
        if not self.verify_password(password):
            self._failed_login_attempts += 1
            if self._failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                self._client_status = ClientStatus.BLOCKED
            return False
        self._failed_login_attempts = 0
        return True

    @property
    def client_id(self) -> uuid.UUID:
        return self._client_id

    @property
    def account_ids(self) -> tuple[uuid.UUID, ...]:
        return tuple(self._account_ids)

    @property
    def status(self) -> ClientStatus:
        return self._client_status

    def add_account(self, account_id: uuid.UUID) -> None:
        if not isinstance(account_id, uuid.UUID):
            raise TypeError("Incorrect account_id")
        if account_id not in self._account_ids:
            self._account_ids.append(account_id)
        else:
            raise ValueError(
                "Account with this UUID already exists."
            )

    def remove_account(self, account_id: uuid.UUID) -> None:
        if not isinstance(account_id, uuid.UUID):
            raise TypeError("Incorrect account_id")
        if account_id not in self._account_ids:
            raise ValueError(
                "Account with this UUID does not exist."
            )
        self._account_ids.remove(account_id)

    def get_client_info(self) -> dict[str, object]:
        return {
            "client_id": str(self.client_id),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self._date_of_birth.isoformat(),
            "email": self._email,
            "phone": self._phone,
            "status": self.status.value,
            "account_ids": [
                str(account_id)
                for account_id in self.account_ids
            ],
        }

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} | "
            f"{self.first_name} {self.last_name} | "
            f"****{str(self.client_id)[-4:]} | "
            f"{self.status.value} | "
            f"Accounts: {len(self.account_ids)}"
        )
