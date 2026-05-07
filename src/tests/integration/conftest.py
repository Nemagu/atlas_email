import socket
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import suppress
from email.message import Message
from pathlib import Path

import pytest
from aiosmtpd.controller import Controller

PROJECT_NAME = "transactions_email"


def find_free_port() -> int:
    """Возвращает свободный TCP-порт, выделенный ОС."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_tcp(host: str, port: int, timeout: float = 30.0) -> None:
    """Блокирует до появления TCP-соединения или бросает TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"Сервис {host}:{port} не стал доступен за {timeout}s")


@pytest.fixture(scope="session")
def session_tmp_dir() -> Path:
    """Изолированная папка для временных файлов сессии тестов."""
    path = Path("/tmp") / PROJECT_NAME / str(uuid.uuid4())
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(scope="session")
def nats_endpoint(session_tmp_dir: Path) -> Iterator[tuple[str, int]]:
    """Поднимает NATS через docker compose и возвращает (host, port)."""
    port = find_free_port()
    project = f"test_{uuid.uuid4().hex[:8]}"
    compose_file = session_tmp_dir / f"{uuid.uuid4().hex[:8]}-compose.yml"
    compose_file.write_text(
        f"""services:
  nats:
    image: nats:2-alpine
    ports:
      - "{port}:4222"
"""
    )
    subprocess.run(
        ["docker", "compose", "-p", project, "-f", str(compose_file), "up", "-d"],
        check=True,
    )
    try:
        wait_for_tcp("127.0.0.1", port, timeout=30.0)
        yield "127.0.0.1", port
    finally:
        with suppress(Exception):
            subprocess.run(
                [
                    "docker", "compose",
                    "-p", project,
                    "-f", str(compose_file),
                    "down", "-v",
                ],
                check=False,
            )


class CapturingHandler:
    """aiosmtpd handler, накапливающий принятые сообщения для проверки."""

    def __init__(self) -> None:
        self.messages: list[Message] = []

    async def handle_DATA(self, server, session, envelope) -> str:
        from email import message_from_bytes

        self.messages.append(message_from_bytes(envelope.content))
        return "250 Message accepted"


@pytest.fixture
async def smtp_server() -> AsyncIterator[tuple[str, int, CapturingHandler]]:
    """Поднимает локальный SMTP через aiosmtpd."""
    handler = CapturingHandler()
    port = find_free_port()
    controller = Controller(handler, hostname="127.0.0.1", port=port)
    controller.start()
    try:
        yield "127.0.0.1", port, handler
    finally:
        controller.stop()
