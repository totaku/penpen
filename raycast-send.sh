#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Публикация в телеграм каналы
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🎮
# @raycast.argument1 { "type": "text", "placeholder": "Канал или чат", "optional": false }
# @raycast.argument2 { "type": "dropdown", "placeholder": "Операция", "optional": true, "data": [{"title": "Отправить", "value": "send"}, {"title": "Reply to", "value": "reply"}, {"title": "Редактировать", "value": "edit"}, {"title": "Удалить", "value": "delete"}, {"title": "Закрепить", "value": "pin"}, {"title": "Открепить", "value": "unpin"}] }
# @raycast.argument3 { "type": "text", "placeholder": "YouTube URL или ссылка на сообщение", "optional": true }

PROJECT_DIR="/Users/totaku/Work/3lf/main/penpen"
LOG_FILE="$PROJECT_DIR/logs/raycast.log"

mkdir -p "$PROJECT_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Запуск ==="
log "Аргументы: '$1' '$2' '$3'"

TARGET="$1"
OPERATION="${2:-send}"
URL_OR_LINK="$3"

# Определяем тип третьего аргумента
YOUTUBE_URL=""
MESSAGE_REF=""

if [[ -n "$URL_OR_LINK" && "$URL_OR_LINK" != "null" && "$URL_OR_LINK" != "undefined" ]]; then
    if [[ "$URL_OR_LINK" == *"youtube.com"* || "$URL_OR_LINK" == *"youtu.be"* ]]; then
        YOUTUBE_URL="$URL_OR_LINK"
        log "YouTube URL: $YOUTUBE_URL"
    elif [[ "$URL_OR_LINK" == *"t.me"* || "$URL_OR_LINK" =~ ^[0-9]+$ ]]; then
        MESSAGE_REF="$URL_OR_LINK"
        log "Ссылка на сообщение: $MESSAGE_REF"
    fi
fi

# Формируем команду
CMD=(uv run --project "$PROJECT_DIR" bot send --to "$TARGET")

case "$OPERATION" in
    "send")
        log "Режим: отправка"
        if [[ -n "$YOUTUBE_URL" ]]; then
            CMD+=(--video "$YOUTUBE_URL")
        fi
        ;;
    "reply")
        log "Режим: ответ"
        if [[ -z "$MESSAGE_REF" ]]; then
            echo "Ошибка: для Reply to укажи ссылку на сообщение в поле 3"
            exit 1
        fi
        CMD+=(--reply-to "$MESSAGE_REF")
        if [[ -n "$YOUTUBE_URL" ]]; then
            CMD+=(--video "$YOUTUBE_URL")
        fi
        ;;
    "edit")
        log "Режим: редактирование"
        if [[ -z "$MESSAGE_REF" ]]; then
            echo "Ошибка: для Редактировать укажи ссылку на сообщение в поле 3"
            exit 1
        fi
        CMD+=(--edit "$MESSAGE_REF")
        ;;
    "delete")
        log "Режим: удаление"
        if [[ -z "$MESSAGE_REF" ]]; then
            echo "Ошибка: для Удалить укажи ссылку на сообщение в поле 3"
            exit 1
        fi
        CMD+=(--delete "$MESSAGE_REF")
        ;;
    "pin")
        log "Режим: закрепить"
        if [[ -z "$MESSAGE_REF" ]]; then
            echo "Ошибка: для Закрепить укажи ссылку на сообщение в поле 3"
            exit 1
        fi
        CMD+=(--pin "$MESSAGE_REF")
        ;;
    "unpin")
        log "Режим: открепить"
        if [[ -z "$MESSAGE_REF" ]]; then
            echo "Ошибка: для Открепить укажи ссылку на сообщение в поле 3"
            exit 1
        fi
        CMD+=(--unpin "$MESSAGE_REF")
        ;;
    *)
        echo "Ошибка: неизвестная операция '$OPERATION'"
        exit 1
        ;;
esac

log "Команда: ${CMD[*]}"

cd "$PROJECT_DIR"
"${CMD[@]}"
RESULT=$?

if [[ $RESULT -eq 0 ]]; then
    log "Успешно (код: $RESULT)"
    case "$OPERATION" in
        "send")  echo "✅ Отправлено в $TARGET" ;;
        "reply") echo "✅ Ответ отправлен в $TARGET" ;;
        "edit")  echo "✅ Сообщение отредактировано в $TARGET" ;;
        "delete") echo "✅ Сообщение удалено в $TARGET" ;;
        "pin")   echo "✅ Сообщение закреплено в $TARGET" ;;
        "unpin") echo "✅ Сообщение откреплено в $TARGET" ;;
    esac
else
    log "Ошибка (код: $RESULT)"
    echo "❌ Ошибка при '$OPERATION' в $TARGET (код: $RESULT)"
    echo "Лог: $LOG_FILE"
fi

log "=== Завершение ==="
