from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from application.ports.email_sender import EmailMessage, EmailSender
from infrastructure.config.smtp import SmtpSettings


class SmtpEmailSender(EmailSender):
    """Отправка писем через SMTP с помощью aiosmtplib."""

    def __init__(self, settings: SmtpSettings) -> None:
        self._settings = settings

    async def send(self, message: EmailMessage) -> None:
        mime = MIMEMultipart("alternative")
        mime["From"] = self._settings.sender
        mime["To"] = message.recipient
        mime["Subject"] = message.subject
        mime.attach(MIMEText(message.text_body, "plain"))
        mime.attach(MIMEText(message.html_body, "html"))

        kwargs: dict[str, object] = {
            "hostname": self._settings.host,
            "port": self._settings.port,
            "use_tls": self._settings.use_tls,
            "timeout": self._settings.timeout,
        }
        if self._settings.username:
            kwargs["username"] = self._settings.username
            kwargs["password"] = self._settings.password
        await aiosmtplib.send(mime, **kwargs)
