from os import getenv

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from infrastructure.config.logging import LoggingSettings
from infrastructure.config.nats import EmailSenderConsumerStreamSettings, NatsSettings
from infrastructure.config.smtp import SmtpSettings


class AppBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=getenv("CONFIG_FILE"),
        yaml_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(
                settings_cls=settings_cls,
                yaml_file=getenv("CONFIG_FILE"),
                yaml_file_encoding="utf-8",
            ),
        )


class NatsConsumerWorkerSettings(AppBaseSettings):
    """Конфиг NATS-консьюмера, отправляющего письма."""

    email: EmailSenderConsumerStreamSettings = Field(
        default_factory=EmailSenderConsumerStreamSettings
    )
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    nats: NatsSettings = Field(default_factory=NatsSettings)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
