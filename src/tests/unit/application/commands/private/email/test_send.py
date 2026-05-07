import pytest

from application.commands.private.email import SendEmailCommand, SendEmailUseCase
from application.ports.email_sender import EmailMessage, EmailSender


class _FakeEmailSender(EmailSender):
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


@pytest.fixture
def email_sender() -> _FakeEmailSender:
    return _FakeEmailSender()


@pytest.fixture
def use_case(email_sender: _FakeEmailSender) -> SendEmailUseCase:
    return SendEmailUseCase(email_sender)


@pytest.fixture
def command_factory():
    def make(**overrides: str) -> SendEmailCommand:
        defaults: dict[str, str] = {
            "recipient": "user@example.com",
            "subject": "Test subject",
            "text_body": "Plain text body",
            "html_body": "<p>HTML body</p>",
        }
        defaults.update(overrides)
        return SendEmailCommand(**defaults)  # type: ignore[arg-type]

    return make


async def test_execute_returns_none(
    use_case: SendEmailUseCase, command_factory
) -> None:
    result = await use_case.execute(command_factory())
    assert result is None


async def test_execute_passes_full_message_to_sender(
    use_case: SendEmailUseCase,
    email_sender: _FakeEmailSender,
    command_factory,
) -> None:
    command = command_factory()
    await use_case.execute(command)
    assert email_sender.sent == [
        EmailMessage(
            recipient=command.recipient,
            subject=command.subject,
            text_body=command.text_body,
            html_body=command.html_body,
        )
    ]


@pytest.mark.parametrize(
    "field,value",
    [
        ("recipient", "alice@example.com"),
        ("subject", "Welcome to the service"),
        ("text_body", "Hello world"),
        ("html_body", "<b>Hello</b>"),
    ],
    ids=["recipient", "subject", "text_body", "html_body"],
)
async def test_execute_propagates_each_field(
    use_case: SendEmailUseCase,
    email_sender: _FakeEmailSender,
    command_factory,
    field: str,
    value: str,
) -> None:
    await use_case.execute(command_factory(**{field: value}))
    assert getattr(email_sender.sent[0], field) == value
