#!/usr/bin/env bash
# Экспортирует куки YouTube из Chrome в cookies.txt (формат Netscape/yt-dlp)
# Запускай периодически или когда yt-dlp начинает требовать авторизацию.
# Chrome должен быть запущен перед выполнением скрипта.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKIES_FILE="$SCRIPT_DIR/cookies.txt"

# Ищем yt-dlp: сначала в venv проекта, потом в PATH
YT_DLP="$SCRIPT_DIR/.venv/bin/yt-dlp"
if [[ ! -x "$YT_DLP" ]]; then
  YT_DLP="$(which yt-dlp 2>/dev/null || echo "")"
fi
if [[ -z "$YT_DLP" ]]; then
  echo "Ошибка: yt-dlp не найден. Запусти: uv sync"
  exit 1
fi

echo "Экспортируем куки из Chrome..."

# --print id — просто печатает ID видео, ничего не скачивает
# Этого достаточно чтобы yt-dlp записал cookies.txt
"$YT_DLP" \
  --cookies-from-browser firefox \
  --cookies "$COOKIES_FILE" \
  --print id \
  --no-playlist \
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>&1 | grep -v "^\[" || true

if [[ -f "$COOKIES_FILE" ]]; then
  COUNT=$(grep -c "youtube\|google" "$COOKIES_FILE" 2>/dev/null || echo "?")
  echo "Готово: $COOKIES_FILE (youtube/google записей: $COUNT)"
else
  echo "Ошибка: файл куки не создан."
  exit 1
fi
