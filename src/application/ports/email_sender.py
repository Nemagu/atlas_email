from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class EmailMessage:
    """Сообщение электронной почты для отправки."""

    recipient: str
    subject: str
    text_body: str
    html_body: str


class EmailSender(ABC):
    """Интерфейс отправки электронных писем."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...
