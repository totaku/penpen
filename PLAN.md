# PLAN.md — Дальнейшее развитие penpen

## Текущее состояние

Реализовано:
- Отправка текста, фото, медиагруппы, видео
- Поддержка нескольких получателей (`--to toto test`)
- Retry-логика на aiogram 3
- Скачивание YouTube-видео через yt-dlp
- Управление сообщениями: `--pin`, `--unpin`, `--delete`, `--edit`, `--reply-to`
- Парсинг REF: число, ссылка `t.me/c/...`, или пусто (= last)
- Трекинг `message_id`: сохраняется в `.last_message_id.<target>` после каждой отправки
- `--edit` автоматически переключается между `editMessageText` и `editMessageCaption`

---

## Приоритет 1: Будущее

- `--forward <chat_id> <message_id>` — пересылка сообщения
- Поддержка кнопок (inline keyboard) через JSON-файл
- Шаблоны сообщений (Jinja2) для переменных подстановок
- Интеграция с CI/CD (GitHub Actions example)
