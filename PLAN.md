# PLAN.md — Дальнейшее развитие penpen

## Статус

Текущая реализация:
- Отправка текста, фото, медиагруппы, видео
- Поддержка нескольких получателей (`--to toto test`)
- Retry-логика на aiogram 3
- Скачивание YouTube-видео через yt-dlp

---

## Приоритет 1: Pin / Edit / Reply через флаги CLI

### Новые флаги

```bash
# Закрепить сообщение по ID или ссылке на пост
uv run bot send --to toto --pin 194
uv run bot send --to toto --pin https://t.me/c/2780029395/194

# Отредактировать сообщение по ID или ссылке (или последнее, если не указан)
uv run bot send --to toto --edit 123
uv run bot send --to toto --edit https://t.me/c/2780029395/194
uv run bot send --to toto --edit          # использует last_message_id

# Ответить на сообщение по ID или ссылке (или на последнее)
uv run bot send --to toto --reply-to 456
uv run bot send --to toto --reply-to https://t.me/c/2780029395/194
uv run bot send --to toto --reply-to      # использует last_message_id
```

### Парсинг ссылки на пост

Ссылка вида `https://t.me/c/2780029395/194` содержит message_id = `194`.
Функция `parse_message_ref(value: str) -> int` в `bot/message_store.py`:
- Если `value` — число → вернуть как int
- Если `value` — ссылка `https://t.me/c/<chat_id>/<msg_id>` → вернуть `<msg_id>` как int
- Иначе → ошибка

### Хранение last_message_id

- Файл `.last_message_id.<target>` в корне проекта (gitignored)
- Создаётся/обновляется после каждой успешной отправки
- Один файл на таргет: `.last_message_id.toto`, `.last_message_id.test`
- При `--edit` / `--reply-to` / `--pin` без аргумента — читается из файла

### Новые методы в TelegramClient

```python
async def pin_message(chat_id: str, message_id: int) -> dict
async def edit_message(chat_id: str, message_id: int, text: str, parse_mode: str) -> dict
async def reply_to_message(chat_id: str, message_id: int, ...) -> dict  # обёртка над send_*, передаёт reply_parameters
```

### Изменения в cli.py

- Добавить аргументы: `--pin`, `--edit [ID]`, `--reply-to [ID]`
- После отправки записывать message_id в `.last_message_id.<target>`
- Читать last_message_id при необходимости

### Изменения в config.py / структуре

- Новый модуль `bot/message_store.py`:
  - `save_last_id(target: str, message_id: int) -> None`
  - `load_last_id(target: str) -> int | None`

### Новые тесты

- `tests/test_message_store.py` — сохранение/чтение ID
- `tests/test_telegram_client.py` — тесты для `pin_message`, `edit_message`

---

## Приоритет 2: Прочее (будущее)

- `--forward <chat_id> <message_id>` — пересылка сообщения
- `--delete <message_id>` — удаление сообщения
- Поддержка кнопок (inline keyboard) через JSON-файл
- Шаблоны сообщений (Jinja2) для переменных подстановок
- Интеграция с CI/CD (GitHub Actions example)
