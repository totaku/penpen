# penpen

CLI-инструмент для отправки сообщений и медиа в Telegram-каналы и чаты.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` / `ffprobe`
- `deno` (только для скачивания YouTube-видео)

## Установка

```bash
uv sync
```

## Настройка

Создай `.env` в корне проекта:

```env
BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Каналы (ключ = CHANNEL_ID_ + имя в верхнем регистре)
CHANNEL_ID_MYCHANNEL=-100xxxxxxxxxx
CHANNEL_ID_TEST=-100xxxxxxxxxx

# Чаты (ключ = CHAT_ + имя в верхнем регистре)
CHAT_MYCHAT=-100xxxxxxxxxx

# Опционально
ADMIN_CHAT_ID=xxxxxxxxxx   # куда слать уведомления об ошибках
LOG_LEVEL=INFO
```

После этого можно обращаться к каналу/чату по короткому имени — `--to mychannel`, `--to test` и т.д.

## Как отправить сообщение

Текст — в файл `message.md` (поддерживается Markdown). Медиафайлы — в папку `media/`.

```bash
# Отправить текст
uv run bot send --to test

# Нескольким получателям сразу
uv run bot send --to test mychannel

# Проверить без отправки (покажет текст и параметры)
uv run bot send --to test --dry-run
```

## Медиа

Положи файлы в `media/` перед отправкой — бот сам разберётся что делать:

| Содержимое `media/`  | Что отправится              |
|----------------------|-----------------------------|
| пусто                | только текст                |
| 1 картинка           | фото + подпись              |
| 2–10 картинок        | галерея + подпись           |
| видео                | видео + подпись             |
| видео + `cover.jpg`  | видео с обложкой + подпись  |

Лимит подписи к медиа — 1024 символа. Текстовые сообщения без медиа — до 4096.

```bash
# Оставить медиафайлы после отправки (по умолчанию удаляются)
uv run bot send --to test --keep-media
```

## YouTube

```bash
# Сначала обновить куки (один раз или при ошибках авторизации)
./update-cookies.sh

# Отправить с видео
uv run bot send --to test --video "https://youtu.be/VIDEO_ID"
```

Видео скачивается в H.264 MP4, thumbnail сохраняется как `cover.jpg` и передаётся как обложка.

## Управление сообщениями

После каждой успешной отправки `message_id` сохраняется автоматически.
Флаги без аргумента используют последнее отправленное сообщение.

```bash
# Закрепить последнее сообщение
uv run bot send --to test --pin

# Закрепить по ID или ссылке
uv run bot send --to test --pin 194
uv run bot send --to test --pin "https://t.me/c/1404339876/194"

# Открепить
uv run bot send --to test --unpin 194

# Удалить
uv run bot send --to test --delete 194

# Отредактировать (текст берётся из message.md)
uv run bot send --to test --edit 194

# Ответить на сообщение (отправляет новый пост как ответ)
uv run bot send --to test --reply-to 194

# Переслать сообщение из другого канала
uv run bot send --to test --forward "https://t.me/c/1234567890/42"
```

## Шаблоны

Для повторяющихся постов с одинаковой структурой (например, PS Plus каждый месяц)
удобно использовать шаблоны: структура хранится в `templates/NAME.md` (Jinja2),
переменные — в `data.yml`.

```bash
uv run bot send --to test --template ps_plus --data data.yml

# Вместе с медиа — картинку просто кладёшь в media/ как обычно
uv run bot send --to test --template ps_plus --data data.yml
```

Пример `data.yml`:

```yaml
date: "3 марта"
url: "https://blog.playstation.com/..."
tier: "Essential"
games:
  - "PGA Tour 2K25 | PS5"
  - "Monster Hunter Rise | PS5, PS4"
  - "Slime Rancher 2 | PS5"
```

Новый шаблон — просто новый `.md` файл в `templates/`, без изменений кода.

## Дополнительные опции

```bash
# Указать другой файл с текстом (по умолчанию message.md)
uv run bot send --to test --message path/to/post.md

# Указать другую папку с медиа (по умолчанию media/)
uv run bot send --to test --media-dir path/to/media

# Подробный вывод для отладки
uv run bot send --to test --debug
```

## Разработка

```bash
uv sync --dev
uv run pytest
uv run ruff check bot/ tests/
uv run ty check bot/
```
