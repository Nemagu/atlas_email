import asyncio
import json
import uuid
from pathlib import Path

import nats
import pytest

from infrastructure.config import NatsConsumerWorkerSettings
from presentation.background.nats.email_consumer import EmailNatsConsumerWorker
from src.tests.integration.conftest import CapturingHandler


@pytest.fixture
def config_file(
    session_tmp_dir: Path,
    nats_endpoint: tuple[str, int],
    smtp_server: tuple[str, int, CapturingHandler],
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    nats_host, nats_port = nats_endpoint
    smtp_host, smtp_port, _ = smtp_server

    password_file = session_tmp_dir / f"smtp_password_{uuid.uuid4().hex[:6]}"
    password_file.write_text("test")

    config = session_tmp_dir / f"config_{uuid.uuid4().hex[:6]}.yaml"
    config.write_text(
        f"""nats:
  host: {nats_host}
  port: {nats_port}
  loop_sleep_duration: 1
smtp:
  host: {smtp_host}
  port: {smtp_port}
  username: ""
  password_file: {password_file}
  sender: bot@example.com
  use_tls: false
  timeout: 5
"""
    )
    monkeypatch.setenv("CONFIG_FILE", str(config))
    return config


async def test_email_published_to_nats_is_delivered_via_smtp(
    config_file: Path,
    nats_endpoint: tuple[str, int],
    smtp_server: tuple[str, int, CapturingHandler],
) -> None:
    settings = NatsConsumerWorkerSettings()
    worker = EmailNatsConsumerWorker(settings)
    worker_task = asyncio.create_task(worker.run())

    await asyncio.sleep(1.5)

    nats_host, nats_port = nats_endpoint
    nc = await nats.connect(f"nats://{nats_host}:{nats_port}")
    payload = json.dumps(
        {
            "recipient": "user@example.com",
            "subject": "Hello",
            "text_body": "plain content",
            "html_body": "<p>html content</p>",
        }
    ).encode("utf-8")
    await nc.publish(settings.email.send_subject, payload)
    await nc.flush()
    await nc.close()

    _, _, handler = smtp_server
    for _ in range(30):
        if handler.messages:
            break
        await asyncio.sleep(0.2)

    worker._shutdown_event.set()
    await worker_task

    assert len(handler.messages) == 1
    msg = handler.messages[0]
    assert msg["From"] == "bot@example.com"
    assert msg["To"] == "user@example.com"
    assert msg["Subject"] == "Hello"
    body = msg.as_string()
    assert "plain content" in body
    assert "html content" in body
