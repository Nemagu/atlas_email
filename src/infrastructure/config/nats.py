from pydantic import BaseModel


class EmailSenderConsumerStreamSettings(BaseModel):
    """Настройки consumer-а для stream-а отправки писем."""

    stream_name: str = "email"
    main_subject_name: str = "email"
    send_subject_name: str = "send"

    @property
    def send_subject(self) -> str:
        return f"{self.stream_name}.{self.main_subject_name}.{self.send_subject_name}"


class NatsSettings(BaseModel):
    """Настройки подключения к NATS."""

    host: str = "localhost"
    port: int = 4222
    connect_name: str = "app-worker"
    reconnect_time_wait: int = 5
    connect_timeout: int = 5
    ping_interval: int = 120
    max_outstanding_pings: int = 3
    healthcheck_file: str = "/tmp/nats_worker_healthbeat"
    loop_sleep_duration: int = 2

    @property
    def url(self) -> str:
        return f"nats://{self.host}:{self.port}"
