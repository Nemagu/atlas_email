# transactions_email

Сервис-консьюмер NATS, отправляющий электронные письма через SMTP. Получает сообщения о необходимости отправки письма из subject `email.email.send`, формирует MIME-сообщение с текстовой и HTML-версиями и отдаёт SMTP-серверу.

## Быстрый старт

```bash
uv sync
CONFIG_FILE=configs/example.yaml uv run python src/main.py
```

## Конфигурация

Все настройки читаются из YAML-файла, путь к которому задаётся в переменной окружения `CONFIG_FILE`. Пример — `configs/example.yaml`.

Ключевые блоки:

| Блок | Назначение |
|---|---|
| `nats` | подключение к NATS (host, port, connect_name, healthcheck_file) |
| `email` | имена subject-а: `<stream_name>.<main_subject_name>.<send_subject_name>` |
| `smtp` | подключение к SMTP-серверу (host, port, username, sender, use_tls, timeout) |
| `logging` | уровень логирования (`debug`, `info`, `warning`, `error`, `critical`) |

Пароль SMTP задаётся файлом по пути `smtp.password_file` — содержимое файла используется при подключении. Если `username` пустой, аутентификация не выполняется.

## Команды разработки

```bash
uv run ruff check                       # линт
uv run pytest src/tests/                # все тесты
uv run pytest src/tests/unit/           # юниты (быстрые)
uv run pytest src/tests/integration/    # интеграционные (требуют docker)
uv run pytest --cov=src                 # с покрытием
```

Интеграционные тесты автоматически поднимают NATS через `docker compose` (с уникальным проектом и портом) и in-process SMTP-сервер `aiosmtpd`. Временные файлы создаются в `/tmp/transactions_email/` и не удаляются после прогона — для отладки.

## Структура

```
src/
├── application/            # use case + порт EmailSender
├── infrastructure/
│   ├── config/             # pydantic-settings: yaml-only
│   └── email/aiosmtplib/   # адаптер SMTP через aiosmtplib
├── presentation/
│   └── background/nats/    # NATS-консьюмер + lifecycle воркера
├── tests/
│   ├── unit/               # юниты
│   └── integration/        # end-to-end через NATS+SMTP
└── main.py                 # entrypoint с uvloop
```

Архитектура — гексагональная: `application/` определяет порт и use case, `infrastructure/` — реализацию SMTP-адаптера, `presentation/` — точку входа (NATS-консьюмер).

## Контракт сообщения

Subject: `email.email.send` (настраивается через `email.*` блок конфига).

Payload — JSON:

```json
{
  "recipient": "user@example.com",
  "subject": "Subject of the email",
  "text_body": "Plain text fallback",
  "html_body": "<html><body>...</body></html>"
}
```

Доставка at-most-once: используется plain NATS `subscribe`, без JetStream. На ошибках валидации/SMTP — логирование, без повторной доставки.
