import asyncio
from logging import getLogger

from nats import connect
from nats.aio.client import Client
from nats.errors import (
    ConnectionClosedError,
    ConnectionDrainingError,
    ConnectionReconnectingError,
    StaleConnectionError,
)
from nats.js import JetStreamContext

from infrastructure.config import NatsSettings
from presentation.background.base import BackgroundBaseWorker

logger = getLogger(__name__)
NATS_CONNECTION_ERRORS = (
    ConnectionClosedError,
    ConnectionDrainingError,
    ConnectionReconnectingError,
    StaleConnectionError,
)


class NatsBaseWorker(BackgroundBaseWorker):
    """Базовый NATS-воркер: управление подключением и реконнектом."""

    def __init__(self, nats_settings: NatsSettings) -> None:
        super().__init__(nats_settings.healthcheck_file)
        self._nats_settings = nats_settings
        self._nc: Client | None = None
        self._js: JetStreamContext | None = None
        self._nats_lock = asyncio.Lock()

    async def setup(self) -> None:
        """Устанавливает подключение к NATS и вызывает hook после коннекта."""
        await self._connect_nats()

    async def complete(self) -> None:
        """Закрывает NATS-соединение, подавляя ошибки на shutdown."""
        if self._nc:
            try:
                await asyncio.wait_for(self._nc.close(), timeout=5.0)
            except Exception:
                pass

    async def _events_after_connected(self) -> None:
        return None

    async def _connect_nats(self) -> None:
        async with self._nats_lock:
            if self._nc is not None and self._nc.is_connected:
                return
            logger.info("connecting to nats")
            while not self._shutdown_event.is_set():
                self._update_heartbeat()
                try:
                    self._nc = await asyncio.wait_for(
                        connect(
                            self._nats_settings.url,
                            name=self._nats_settings.connect_name,
                            connect_timeout=self._nats_settings.connect_timeout,
                            reconnect_time_wait=self._nats_settings.reconnect_time_wait,
                            max_reconnect_attempts=0,
                            ping_interval=self._nats_settings.ping_interval,
                            max_outstanding_pings=self._nats_settings.max_outstanding_pings,
                        ),
                        timeout=self._nats_settings.connect_timeout,
                    )
                    self._js = self._nc.jetstream()
                    await self._events_after_connected()
                    logger.info("nats connected")
                    return
                except BaseException as e:
                    logger.warning("nats connection failed: %s", e)
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self._nats_settings.reconnect_time_wait,
                    )
                except asyncio.TimeoutError:
                    pass
