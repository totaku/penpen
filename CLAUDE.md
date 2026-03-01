# CLAUDE.md

Руководство для Claude Code при работе с репозиторием penpen.

## О проекте

**penpen** — CLI-инструмент для отправки сообщений и медиа в Telegram-каналы и чаты.
Построен на `aiogram 3` + `aiohttp`, с поддержкой `uv` и полной типизацией.

## Команды

### Разработка

```bash
# Установка зависимостей
uv sync --dev

# Тесты
uv run pytest
uv run pytest -v                        # подробный вывод
uv run pytest tests/test_config.py      # отдельный файл

# Линтер
uv run ruff check bot/ tests/

# Типы
uv run ty check bot/

# Обновить куки YouTube (запускать при блокировках)
./update-cookies.sh
```

### Использование

```bash
# Отправить текст
uv run bot send --to toto

# Несколько получателей
uv run bot send --to toto test

# С YouTube-видео
uv run bot send --to toto --video "https://youtu.be/VIDEO_ID"

# Проверка без отправки
uv run bot send --to toto --dry-run

# Отладочный вывод
uv run bot send --to toto --debug

# Не удалять медиа после отправки
uv run bot send --to toto --keep-media

# Кастомные пути
uv run bot send --to toto --message path/to/message.md --media-dir path/to/media

# Закрепить последнее отправленное сообщение
uv run bot send --to toto --pin

# Закрепить по ID или ссылке
uv run bot send --to toto --pin 194
uv run bot send --to toto --pin "https://t.me/c/1404339876/194"

# Открепить / удалить
uv run bot send --to toto --unpin 194
uv run bot send --to toto --delete 194

# Отредактировать (текст берётся из message.md)
uv run bot send --to toto --edit 194

# Ответить на сообщение
uv run bot send --to toto --reply-to 194
```

### Конфигурация (.env)

```
BOT_TOKEN=...
CHANNEL_ID_TOTO=-1001404339876   # → target "toto"
CHANNEL_ID_TEST=-1002780029395   # → target "test"
CHAT_CAT=-1001280437635          # → target "cat"
ADMIN_CHAT_ID=12345678
LOG_LEVEL=INFO
```

- `CHANNEL_ID_*` → каналы, ключ строчными буквами без префикса
- `CHAT_*` → чаты, аналогично (кроме `ADMIN_CHAT_ID`)
- Channel ID обязан начинаться с `-100`

## Архитектура

```
bot/
├── cli.py               # argparse, оркестрация, main()
├── config.py            # load_config(), Config, resolve_targets()
├── telegram_client.py   # aiogram 3, send_text/photo/media_group/video, pin/edit/delete, retry
├── message_store.py     # save_last_id(), load_last_id(), parse_message_ref()
├── media_scanner.py     # scan(), clear(), MediaPlan, MediaKind
├── markdown_processor.py # read_message(), telegramify-markdown
└── video_downloader.py  # yt-dlp subprocess, is_youtube_url(), download()
```

### Поток данных

```
main()
  → load_config()
  → resolve_targets(["toto"]) → [("toto", "-1001404339876")]
  → [--pin/--unpin/--delete/--edit] → управление сообщениями, выход
  → [--reply-to] → parse_message_ref / load_last_id → reply_to_message_id
  → [--video] video_downloader.download(url, media_dir)
  → media_scanner.scan(media_dir) → MediaPlan
  → markdown_processor.prepare_caption/text()
  → [--dry-run] вывод и выход
  → async with TelegramClient:
      asyncio.gather(*[_send_to_target(...) for each target])
  → все успешно → save_last_id(target, message_id) для каждого таргета
  → все успешно + не --keep-media → media_scanner.clear()
  → exit 0 / exit 1
```

### Диспетчер по типу медиа

| `MediaKind`    | Метод API         | Ограничение caption |
|----------------|-------------------|---------------------|
| `TEXT_ONLY`    | `sendMessage`     | 4096 символов       |
| `SINGLE_PHOTO` | `sendPhoto`       | 1024 символа        |
| `PHOTO_GROUP`  | `sendMediaGroup`  | 1024 символа        |
| `SINGLE_VIDEO` | `sendVideo`       | 1024 символа        |

## Важные детали реализации

### Видео
- Формат yt-dlp: `bestvideo[vcodec^=avc]+bestaudio[ext=m4a]` — принудительно H.264
- `--recode-video mp4` — гарантия совместимости с Mac/iOS/Telegram
- `--postprocessor-args "ffmpeg:-movflags +faststart"` — streaming
- `--remote-components ejs:github` — решение JS-челленджей YouTube (требует `deno`)
- Параметр API: `cover` (не `thumbnail`) — без ограничения 320px

### Обложка видео
- `cover.jpg` или `thumbnail.jpg` в `media/` → передаётся как `cover` в API
- yt-dlp скачивает thumbnail автоматически, скрипт переименовывает его в `cover.jpg`
- Если обложки нет — видео отправляется без неё

### Куки YouTube
- `cookies.txt` в корне проекта (gitignored)
- Создаётся через `./update-cookies.sh` (читает из Firefox)
- Если `cookies.txt` отсутствует или не читается — автоматически используется `--cookies-from-browser chrome`
- При невалидных/устаревших куках автоматически fallback на `--cookies-from-browser chrome`
- Обновлять раз в месяц или при ошибках авторизации

### Управление сообщениями (pin/edit/reply)
- `--pin/--unpin/--delete/--edit REF` — не отправляют медиа, только управляют существующим сообщением
- `REF` — число (`194`), ссылка (`https://t.me/c/<chat_id>/<msg_id>`), или пусто (= last)
- После каждой успешной отправки `message_id` сохраняется в `.last_message_id.<target>` в текущей директории
- `--reply-to` работает вместе с отправкой — передаёт `reply_parameters` в API

### Retry
- 3 попытки с экспоненциальным backoff (1s, 2s, 4s)
- Только на: `NetworkError`, `TimeoutException`, `OSError`
- `TelegramError` (ответ API) — не повторяется

### Зависимости системы
- `ffprobe` — получение размеров и длительности видео
- `deno` — решение JS-челленджей yt-dlp (есть в PATH)
- `ffmpeg` — перекодировка видео через yt-dlp

## Структура файлов

```
penpen/
├── .env                 # токены и ID (gitignored)
├── message.md           # текст для отправки (gitignored)
├── cookies.txt          # YouTube куки (gitignored)
├── media/               # медиафайлы для отправки (gitignored)
│   └── .gitkeep
├── update-cookies.sh    # экспорт куки из Firefox
├── pyproject.toml
├── uv.lock
├── bot/
└── tests/
```
