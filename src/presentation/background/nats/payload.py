from pydantic import BaseModel


class EmailSendPayload(BaseModel):
    """Схема входящего сообщения на отправку письма."""

    recipient: str
    subject: str
    text_body: str
    html_body: str
