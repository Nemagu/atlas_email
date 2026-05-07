import asyncio
from logging import getLogger

from nats.aio.msg import Msg

from application.commands.private.email import SendEmailCommand, SendEmailUseCase
from infrastructure.config import NatsConsumerWorkerSettings
from infrastructure.email.aiosmtplib.email_sender import SmtpEmailSender
from presentation.background.nats.base import NatsBaseWorker
from presentation.background.nats.payload import EmailSendPayload

logger = getLogger(__name__)


class EmailNatsConsumerWorker(NatsBaseWorker):
    """NATS-консьюмер: получает сообщения и отправляет письма."""

    def __init__(self, settings: NatsConsumerWorkerSettings) -> None:
        super().__init__(settings.nats)
        self._email_settings = settings.email
        self._use_case = SendEmailUseCase(SmtpEmailSender(settings.smtp))

    async def _events_after_connected(self) -> None:
        await self._nc.subscribe(  # pyright: ignore[reportOptionalMemberAccess]
            self._email_settings.send_subject,
            cb=self._on_message,
        )

    def _create_tasks(self) -> None:
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))

    async def _heartbeat_loop(self) -> None:
        while not self._shutdown_event.is_set():
            self._update_heartbeat()
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._nats_settings.loop_sleep_duration,
                )
            except asyncio.TimeoutError:
                pass

    async def _on_message(self, msg: Msg) -> None:
        try:
            payload = EmailSendPayload.model_validate_json(msg.data)
            await self._use_case.execute(
                SendEmailCommand(
                    recipient=payload.recipient,
                    subject=payload.subject,
                    text_body=payload.text_body,
                    html_body=payload.html_body,
                )
            )
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.error("message processing error: %s", e)
