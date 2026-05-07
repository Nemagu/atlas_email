from pathlib import Path

import pytest

from infrastructure.config.smtp import SmtpSettings


@pytest.fixture
def password_file(tmp_path: Path) -> Path:
    file = tmp_path / "smtp_password"
    file.write_text("topsecret\n")
    return file


def test_default_values(password_file: Path) -> None:
    settings = SmtpSettings(password_file=str(password_file))
    assert settings.host == "localhost"
    assert settings.port == 587
    assert settings.use_tls is True
    assert settings.timeout == 10


def test_password_property_reads_and_strips_file(password_file: Path) -> None:
    settings = SmtpSettings(password_file=str(password_file))
    assert settings.password == "topsecret"


def test_validator_raises_on_missing_password_file() -> None:
    with pytest.raises(ValueError, match="Password file not found"):
        SmtpSettings(password_file="/nonexistent/path/file")
