from dataclasses import dataclass

from application.ports.email_sender import EmailMessage, EmailSender


@dataclass(slots=True, frozen=True)
class SendEmailCommand:
    recipient: str
    subject: str
    text_body: str
    html_body: str


class SendEmailUseCase:
    """Отправляет письмо получателю."""

    def __init__(self, email_sender: EmailSender) -> None:
        self._email_sender = email_sender

    async def execute(self, command: SendEmailCommand) -> None:
        """Преобразует команду в `EmailMessage` и делегирует отправку `EmailSender`."""
        message = EmailMessage(
            recipient=command.recipient,
            subject=command.subject,
            text_body=command.text_body,
            html_body=command.html_body,
        )
        await self._email_sender.send(message)
