from email.message import Message
from pathlib import Path
from typing import Any

import aiosmtplib
import pytest

from application.ports.email_sender import EmailMessage
from infrastructure.config.smtp import SmtpSettings
from infrastructure.email.aiosmtplib.email_sender import SmtpEmailSender


@pytest.fixture
def password_file(tmp_path: Path) -> Path:
    file = tmp_path / "smtp_password"
    file.write_text("secret\n")
    return file


@pytest.fixture
def settings(password_file: Path) -> SmtpSettings:
    return SmtpSettings(
        host="smtp.example.com",
        port=2525,
        username="bot",
        password_file=str(password_file),
        sender="bot@example.com",
        use_tls=True,
        timeout=7,
    )


@pytest.fixture
def captured_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    async def fake_send(message: Message, **kwargs: Any) -> Any:
        calls.append({"message": message, **kwargs})
        return None

    monkeypatch.setattr(aiosmtplib, "send", fake_send)
    return calls


@pytest.fixture
def message() -> EmailMessage:
    return EmailMessage(
        recipient="user@example.com",
        subject="Hi there",
        text_body="plain content",
        html_body="<p>html content</p>",
    )


async def test_send_calls_aiosmtplib_with_settings(
    settings: SmtpSettings,
    captured_calls: list[dict[str, Any]],
    message: EmailMessage,
) -> None:
    await SmtpEmailSender(settings).send(message)
    assert len(captured_calls) == 1
    call = captured_calls[0]
    assert call["hostname"] == "smtp.example.com"
    assert call["port"] == 2525
    assert call["username"] == "bot"
    assert call["password"] == "secret"
    assert call["use_tls"] is True
    assert call["timeout"] == 7


async def test_send_builds_mime_headers(
    settings: SmtpSettings,
    captured_calls: list[dict[str, Any]],
    message: EmailMessage,
) -> None:
    await SmtpEmailSender(settings).send(message)
    mime = captured_calls[0]["message"]
    assert mime["From"] == "bot@example.com"
    assert mime["To"] == "user@example.com"
    assert mime["Subject"] == "Hi there"


async def test_send_attaches_text_and_html_parts(
    settings: SmtpSettings,
    captured_calls: list[dict[str, Any]],
    message: EmailMessage,
) -> None:
    await SmtpEmailSender(settings).send(message)
    mime = captured_calls[0]["message"]
    parts = mime.get_payload()
    assert len(parts) == 2
    assert parts[0].get_content_type() == "text/plain"
    assert parts[1].get_content_type() == "text/html"
    assert "plain content" in parts[0].get_payload()
    assert "html content" in parts[1].get_payload()
