#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Публикация в телеграм каналы
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🎮
# @raycast.argument1 { "type": "text", "placeholder": "Канал или чат", "optional": false }
# @raycast.argument2 { "type": "dropdown", "placeholder": "Операция", "optional": true, "data": [{"title": "Отправить", "value": "send"}, {"title": "Reply to", "value": "reply"}, {"title": "Редактировать", "value": "edit"}, {"title": "Удалить", "value": "delete"}, {"title": "Закрепить", "value": "pin"}, {"title": "Открепить", "value": "unpin"}, {"title": "Репост", "value": "forward"}] }
# @raycast.argument3 { "type": "text", "placeholder": "YouTube URL или ссылка на сообщение", "optional": true }

# Путь к директории проекта и скрипту
PROJECT_DIR="/Users/totaku/Work/3lf/main/marvin"
TG_SCRIPT="$PROJECT_DIR/tgsend"
LOG_FILE="$PROJECT_DIR/logs/raycast-tg.log"

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Логируем запуск и аргументы
log "=== Запуск скрипта ==="
log "Аргумент 1 (канал/чат): '$1'"
log "Аргумент 2 (Операция): '$2'"
log "Аргумент 3 (URL/ссылка): '$3'"

# Первый аргумент: канал или чат
TARGET=$1

# Проверяем формат первого аргумента
if [[ $TARGET == chat* ]]; then
    # Это чат
    TARGET_TYPE="--chats $TARGET"
    log "Тип цели: чат ($TARGET)"
elif [[ $TARGET == channel* ]]; then
    # Это канал
    TARGET_TYPE="--channels $TARGET"
    log "Тип цели: канал ($TARGET)"
else
    # По умолчанию считаем, что это канал
    TARGET_TYPE="--channels $TARGET"
    log "Тип цели: канал по умолчанию ($TARGET)"
fi

# Второй аргумент: операция (dropdown)
OPERATION=${2:-send}
log "Операция: $OPERATION"

# Третий аргумент: универсальное поле (YouTube URL или ссылка на сообщение)
# Определяем автоматически по содержимому
URL_OR_LINK="$3"
YOUTUBE_PARAM=""
MESSAGE_LINK=""

if [[ -n "$URL_OR_LINK" && "$URL_OR_LINK" != "null" && "$URL_OR_LINK" != "undefined" ]]; then
    log "Аргумент 3 содержит: $URL_OR_LINK"

    # Проверяем, это YouTube URL или ссылка на сообщение
    if [[ "$URL_OR_LINK" == *"youtube.com"* || "$URL_OR_LINK" == *"youtu.be"* ]]; then
        # Это YouTube URL
        YOUTUBE_PARAM="--youtube \"$URL_OR_LINK\""
        log "Определено как YouTube URL: $URL_OR_LINK"
    elif [[ "$URL_OR_LINK" == *"t.me"* ]]; then
        # Это ссылка на сообщение Telegram
        MESSAGE_LINK="$URL_OR_LINK"
        log "Определено как ссылка на сообщение: $MESSAGE_LINK"
    else
        # Неизвестный формат - попробуем как ссылку на сообщение
        MESSAGE_LINK="$URL_OR_LINK"
        log "Неизвестный формат, используем как ссылку: $MESSAGE_LINK"
    fi
fi

# Формируем параметры операции
OPERATION_PARAM=""
case "$OPERATION" in
    "send")
        # Обычная отправка - без дополнительных параметров
        log "Режим: обычная отправка"
        ;;
    "reply")
        # Reply to message
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--reply-to \"$MESSAGE_LINK\""
            log "Режим: ответ на сообщение $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Reply to' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    "edit")
        # Редактирование сообщения
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--edit \"$MESSAGE_LINK\""
            log "Режим: редактирование сообщения $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Редактировать' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    "delete")
        # Удаление сообщения
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--delete \"$MESSAGE_LINK\""
            log "Режим: удаление сообщения $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Удалить' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    "pin")
        # Закрепление сообщения
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--pin \"$MESSAGE_LINK\""
            log "Режим: закрепление сообщения $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Закрепить' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    "unpin")
        # Открепление сообщения
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--unpin \"$MESSAGE_LINK\""
            log "Режим: открепление сообщения $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Открепить' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    "forward")
        # Пересылка сообщения
        if [[ -n "$MESSAGE_LINK" && "$MESSAGE_LINK" != "null" && "$MESSAGE_LINK" != "undefined" ]]; then
            OPERATION_PARAM="--forward \"$MESSAGE_LINK\""
            log "Режим: пересылка сообщения $MESSAGE_LINK"
        else
            ERROR_MSG="Ошибка: для операции 'Репост' необходимо указать ссылку на сообщение в поле 3"
            log "$ERROR_MSG"
            echo "$ERROR_MSG"
            exit 1
        fi
        ;;
    *)
        ERROR_MSG="Ошибка: неизвестная операция '$OPERATION'"
        log "$ERROR_MSG"
        echo "$ERROR_MSG"
        exit 1
        ;;
esac

# Проверяем наличие файла message.md
MESSAGE_FILE="$PROJECT_DIR/message.md"
if [[ ! -f "$MESSAGE_FILE" ]]; then
    ERROR_MSG="Ошибка: Файл $MESSAGE_FILE не найден!"
    log "$ERROR_MSG"
    echo "$ERROR_MSG"
    exit 1
fi
log "Файл сообщения найден: $MESSAGE_FILE"

# Переходим в директорию проекта перед запуском скрипта
cd "$PROJECT_DIR"
log "Текущая директория: $(pwd)"

# Формируем полную команду
FULL_COMMAND="$TG_SCRIPT $TARGET_TYPE"

# Для операций send и reply добавляем message-file
if [[ "$OPERATION" == "send" || "$OPERATION" == "reply" ]]; then
    FULL_COMMAND="$FULL_COMMAND --message-file \"$MESSAGE_FILE\""
fi

# Для операции edit также нужен message-file (с новым текстом)
if [[ "$OPERATION" == "edit" ]]; then
    FULL_COMMAND="$FULL_COMMAND --message-file \"$MESSAGE_FILE\""
fi

# Добавляем YouTube параметр если есть (только для send и reply)
if [[ -n "$YOUTUBE_PARAM" && ("$OPERATION" == "send" || "$OPERATION" == "reply") ]]; then
    FULL_COMMAND="$FULL_COMMAND $YOUTUBE_PARAM"
fi

# Добавляем параметр операции (--reply-to, --edit, --delete, --pin, --unpin, --forward)
if [[ -n "$OPERATION_PARAM" ]]; then
    FULL_COMMAND="$FULL_COMMAND $OPERATION_PARAM"
fi

log "Выполняемая команда: $FULL_COMMAND"

# Определяем описание операции для сообщений
case "$OPERATION" in
    "send")
        OP_TEXT="Отправка сообщения"
        OP_SUCCESS="✅ Сообщение успешно отправлено"
        OP_ERROR="❌ Ошибка при отправке сообщения"
        ;;
    "reply")
        OP_TEXT="Отправка ответа"
        OP_SUCCESS="✅ Ответ успешно отправлен"
        OP_ERROR="❌ Ошибка при отправке ответа"
        ;;
    "edit")
        OP_TEXT="Редактирование сообщения"
        OP_SUCCESS="✅ Сообщение успешно отредактировано"
        OP_ERROR="❌ Ошибка при редактировании сообщения"
        ;;
    "delete")
        OP_TEXT="Удаление сообщения"
        OP_SUCCESS="✅ Сообщение успешно удалено"
        OP_ERROR="❌ Ошибка при удалении сообщения"
        ;;
    "pin")
        OP_TEXT="Закрепление сообщения"
        OP_SUCCESS="✅ Сообщение успешно закреплено"
        OP_ERROR="❌ Ошибка при закреплении сообщения"
        ;;
    "unpin")
        OP_TEXT="Открепление сообщения"
        OP_SUCCESS="✅ Сообщение успешно откреплено"
        OP_ERROR="❌ Ошибка при откреплении сообщения"
        ;;
    "forward")
        OP_TEXT="Пересылка сообщения"
        OP_SUCCESS="✅ Сообщение успешно переслано"
        OP_ERROR="❌ Ошибка при пересылке сообщения"
        ;;
esac

# Запускаем скрипт с собранными параметрами
echo "$OP_TEXT в $TARGET..."
echo "Команда: $FULL_COMMAND"
echo ""

# Используем eval для правильной обработки параметров с пробелами и специальными символами
eval "$FULL_COMMAND"
RESULT=$?

# Проверяем результат выполнения
if [ $RESULT -eq 0 ]; then
    log "Команда выполнена успешно (код: $RESULT)"
    echo ""
    echo "$OP_SUCCESS в $TARGET"
else
    log "Ошибка выполнения команды (код: $RESULT)"
    echo ""
    echo "$OP_ERROR в $TARGET (код: $RESULT)"
    echo "Подробности смотрите в логе: $LOG_FILE"
fi

log "=== Завершение скрипта ==="
echo ""
