import logging

import uvloop

from infrastructure.config import NatsConsumerWorkerSettings
from presentation.background.nats.email_consumer import EmailNatsConsumerWorker


def main() -> None:
    """Точка входа: bootstrap uvloop и запуск NATS-консьюмера."""
    settings = NatsConsumerWorkerSettings()
    logging.basicConfig(level=settings.logging.level.value.upper())
    uvloop.run(EmailNatsConsumerWorker(settings).run())


if __name__ == "__main__":
    main()
