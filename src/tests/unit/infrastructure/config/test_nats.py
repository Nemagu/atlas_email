import pytest

from infrastructure.config.nats import EmailSenderConsumerStreamSettings, NatsSettings


@pytest.mark.parametrize(
    "stream,main,send,expected",
    [
        ("email", "email", "send", "email.email.send"),
        ("foo", "bar", "baz", "foo.bar.baz"),
    ],
    ids=["defaults", "custom"],
)
def test_send_subject_composition(
    stream: str, main: str, send: str, expected: str
) -> None:
    settings = EmailSenderConsumerStreamSettings(
        stream_name=stream,
        main_subject_name=main,
        send_subject_name=send,
    )
    assert settings.send_subject == expected


@pytest.mark.parametrize(
    "host,port,expected",
    [
        ("localhost", 4222, "nats://localhost:4222"),
        ("nats.example.com", 4444, "nats://nats.example.com:4444"),
    ],
    ids=["default", "custom"],
)
def test_nats_url_composition(host: str, port: int, expected: str) -> None:
    settings = NatsSettings(host=host, port=port)
    assert settings.url == expected
