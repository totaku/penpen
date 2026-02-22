# penpen

CLI-инструмент для отправки сообщений и медиа в Telegram-каналы и чаты.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` / `ffprobe`
- `deno` (для скачивания YouTube-видео)

## Установка

```bash
uv sync
```

## Настройка

Создай `.env` в корне проекта:

```env
BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Каналы (имя = CHANNEL_ID_ + имя в верхнем регистре)
CHANNEL_ID_MYCHANNEL=-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CHANNEL_ID_TEST=-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Чаты (имя = CHAT_ + имя в верхнем регистре)
CHAT_MYCHAT=-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Опционально
ADMIN_CHAT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LOG_LEVEL=INFO
```

## Использование

Текст сообщения — в файле `message.md` (Markdown). Медиафайлы — в папке `media/`.

```bash
# Отправить текст
uv run bot send --to test

# Нескольким получателям сразу
uv run bot send --to test test

# С YouTube-видео
uv run bot send --to test --video "https://youtu.be/VIDEO_ID"

# Проверить без отправки
uv run bot send --to test --dry-run --debug

# Не удалять медиа после отправки
uv run bot send --to test --keep-media

# Закрепить последнее отправленное сообщение
uv run bot send --to test --pin

# Закрепить по ID или ссылке
uv run bot send --to test --pin 194
uv run bot send --to test --pin "https://t.me/c/1404339876/194"

# Открепить / удалить
uv run bot send --to test --unpin 194
uv run bot send --to test --delete 194

# Отредактировать (текст берётся из message.md)
uv run bot send --to test --edit 194

# Ответить на сообщение
uv run bot send --to test --reply-to 194
```

После каждой успешной отправки `message_id` сохраняется в `.last_message_id.<target>`.
Флаги `--pin`, `--unpin`, `--delete`, `--edit`, `--reply-to` без аргумента используют это значение автоматически.

## Медиа

Положи файлы в папку `media/` перед отправкой:

| Содержимое `media/`  | Что отправится              |
|----------------------|-----------------------------|
| пусто                | только текст                |
| 1 картинка           | фото + подпись              |
| 2–10 картинок        | галерея + подпись           |
| видео                | видео + подпись             |
| видео + `cover.jpg`  | видео с обложкой + подпись  |

**Лимит подписи к медиа:** 1024 символа. Текстовые сообщения без медиа — до 4096.

## YouTube

```bash
# Сначала обновить куки (один раз или при блокировках)
./update-cookies.sh

# Затем отправить с видео
uv run bot send --to test --video "https://youtu.be/VIDEO_ID"
```

Видео скачивается в формате H.264 MP4 для совместимости с Mac/iOS/Telegram.
Thumbnail автоматически сохраняется как `cover.jpg`.

## Разработка

```bash
uv sync --dev
uv run pytest
uv run ruff check bot/ tests/
uv run ty check bot/
```
