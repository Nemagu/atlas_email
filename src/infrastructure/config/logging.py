from enum import StrEnum

from pydantic import BaseModel


class LoggingLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LoggingSettings(BaseModel):
    """Настройки логирования."""

    level: LoggingLevel = LoggingLevel.INFO
