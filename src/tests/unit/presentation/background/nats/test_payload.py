import pytest
from pydantic import ValidationError

from presentation.background.nats.payload import EmailSendPayload


def test_payload_parses_full_object() -> None:
    raw = b'{"recipient":"a@b.c","subject":"s","text_body":"t","html_body":"<p/>"}'
    payload = EmailSendPayload.model_validate_json(raw)
    assert payload.recipient == "a@b.c"
    assert payload.subject == "s"
    assert payload.text_body == "t"
    assert payload.html_body == "<p/>"


@pytest.mark.parametrize(
    "missing_field",
    ["recipient", "subject", "text_body", "html_body"],
    ids=["recipient", "subject", "text_body", "html_body"],
)
def test_payload_requires_all_fields(missing_field: str) -> None:
    fields = {
        "recipient": "a@b.c",
        "subject": "s",
        "text_body": "t",
        "html_body": "<p/>",
    }
    fields.pop(missing_field)
    with pytest.raises(ValidationError):
        EmailSendPayload.model_validate(fields)
