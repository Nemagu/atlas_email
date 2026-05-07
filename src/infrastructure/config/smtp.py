from os import path
from typing import Self

from pydantic import BaseModel, model_validator


class SmtpSettings(BaseModel):
    """Настройки подключения к SMTP-серверу."""

    host: str = "localhost"
    port: int = 587
    username: str = ""
    password_file: str = "/run/secrets/smtp_password"
    sender: str = ""
    use_tls: bool = True
    timeout: int = 10

    @model_validator(mode="after")
    def validate_password_file(self) -> Self:
        if not path.isfile(self.password_file):
            raise ValueError(f"Password file not found: {self.password_file}")
        return self

    @property
    def password(self) -> str:
        with open(self.password_file, encoding="utf-8") as f:
            return f.read().strip()
