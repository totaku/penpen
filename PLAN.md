# PLAN.md — Дальнейшее развитие penpen

## Текущее состояние (февраль 2026)

Реализовано:
- Отправка текста, фото, медиагруппы, видео в каналы и чаты
- Несколько получателей (`--to toto test`), параллельная отправка
- Retry-логика (3 попытки, exponential backoff)
- Скачивание YouTube-видео (yt-dlp, H.264 MP4, cover.jpg)
- Управление: `--pin`, `--unpin`, `--delete`, `--edit`, `--reply-to`, `--forward`
- Парсинг REF: число, `t.me/c/...`, `last`
- Трекинг `message_id` в `.last_message_id.<target>`
- Уведомления админу: ошибки + overflow (в code-блоке)
- Overflow: если сообщение слишком длинное — в канал не отправляется, целиком уведомляет админа
- Raycast-интеграция (`raycast-send.sh`)

---

## Приоритет 1: Overflow — улучшение качества

**Проблема:** `telegramify_markdown` раздувает текст экранированием (`\.`, `\#` и др.).
Overflow отправляется в MarkdownV2-экранированном виде, который читать неудобно.

**Решение:** Отправлять overflow из исходного `raw`-текста (до конвертации),
без `parse_mode` — просто plain text. Читать легче, форматирование внутри code-блока
всё равно не рендерится.

Конкретно: хранить в исключении `raw` (исходный markdown) вместо / вместе с `converted`,
считать boundary по `raw`, отправлять `raw[limit:]` как plain text.

---

## Приоритет 2: Inline-кнопки (`--buttons`)

Поддержка inline keyboard через JSON-файл рядом с `message.md`:

```json
[
  [{"text": "Читать", "url": "https://example.com"}],
  [{"text": "Поделиться", "callback_data": "share"}]
]
```

```bash
uv run bot send --to toto --buttons buttons.json
```

Нужно: `InlineKeyboardMarkup` в aiogram, новый параметр CLI, чтение JSON.

---

## Приоритет 3: `--poll` — создание опроса

```bash
uv run bot send --to toto --poll poll.json
```

`poll.json`:
```json
{
  "question": "Как вам?",
  "options": ["Отлично", "Нормально", "Плохо"],
  "is_anonymous": true
}
```

Использует `bot.send_poll()` вместо `send_message`.

---

## Приоритет 4: Шаблоны (Jinja2)

Подстановка переменных в `message.md`:

```bash
uv run bot send --to toto --var date=2026-02-25 --var title="Релиз v2"
```

`message.md`:
```
# {{ title }}
Дата: {{ date }}
```

Минимально: `jinja2.Template(raw).render(**vars)` перед `to_telegram_markdown`.

---

## Приоритет 5: `--list-targets` — просмотр доступных таргетов

```bash
uv run bot send --list-targets
# channels: toto, test
# chats: cat
```

Мелкая UX-фича, полезна при работе с новым `.env`.

---

## Не делать / низкий приоритет

- CI/CD интеграция — не нужна для CLI-инструмента
- Webhook/polling режим — выходит за рамки концепции CLI
- База данных вместо `.last_message_id.*` — излишне для одного пользователя
