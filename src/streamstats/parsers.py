import csv
import json

from .errors import EventError, StreamStatsError
from .models import FIELDS, validate_event


# Читает JSONL и выдаёт номер строки, событие или ошибку.
def parse_jsonl(file):
    for number, line in enumerate(file, start=1):
        try:
            row = json.loads(line)
            event = validate_event(row)
        except json.JSONDecodeError:
            yield number, None, EventError("Неверный JSON")
        except StreamStatsError as error:
            yield number, None, error
        else:
            yield number, event, None


# Читает CSV и выдаёт номер строки, событие или ошибку.
def parse_csv(file):
    reader = csv.DictReader(file, strict=True)
    try:
        header = reader.fieldnames
    except csv.Error as error:
        yield 1, None, EventError(f"Неверный заголовок CSV: {error}")
        return

    if header is None:
        return
    for field in FIELDS:
        if field not in header:
            yield 1, None, EventError(f"В заголовке нет поля {field}")
            return

    while True:
        number = reader.reader.line_num + 1
        try:
            row = next(reader)
        except StopIteration:
            return
        except csv.Error as error:
            yield number, None, EventError(f"Неверный CSV: {error}")
            continue

        try:
            if None in row or None in row.values():
                raise EventError("Число полей не совпадает с заголовком")
            event = validate_event(row)
        except StreamStatsError as error:
            yield number, None, error
        else:
            yield number, event, None
