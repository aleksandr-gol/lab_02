from datetime import UTC, datetime

from .errors import EventError, TimeError

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
FIELDS = ("timestamp", "level", "source", "message")


# Проверяет поля события и переводит время в UTC.
def validate_event(row):
    if not isinstance(row, dict):
        raise EventError("Событие должно быть объектом")

    for field in FIELDS:
        if field not in row:
            raise EventError(f"Нет поля {field}")
        if not isinstance(row[field], str):
            raise EventError(f"Поле {field} должно быть строкой")

    if row["level"] not in LEVELS:
        raise EventError("Неизвестный уровень события")
    if row["source"].strip() == "":
        raise EventError("Источник не должен быть пустым")

    try:
        timestamp = datetime.fromisoformat(row["timestamp"])
        timestamp = timestamp.astimezone(UTC)
    except (ValueError, OverflowError) as error:
        raise TimeError("Неверная временная метка ISO 8601") from error

    return {
        "timestamp": timestamp,
        "level": row["level"],
        "source": row["source"],
        "message": row["message"],
    }
