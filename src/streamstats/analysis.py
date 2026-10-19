import logging
from pathlib import Path

from .errors import FormatError
from .models import LEVELS
from .parsers import parse_csv, parse_jsonl

logger = logging.getLogger(__name__)


# Задаёт сортировку по числу ошибок, затем по названию.
def error_sort_key(item):
    source, count = item
    return -count, source


# Считает общую статистику входных файлов.
def analyze(paths, file_format, skip_invalid=False):
    if file_format == "csv":
        parser = parse_csv
    elif file_format == "jsonl":
        parser = parse_jsonl
    else:
        raise FormatError(f"Неподдерживаемый формат: {file_format}")

    total = 0
    skipped = 0
    levels = {}
    for level in LEVELS:
        levels[level] = 0
    sources = {}
    errors_by_source = {}
    first = None
    last = None

    for file_number, path in enumerate(paths, start=1):
        with Path(path).open(encoding="utf-8", newline="") as file:
            for line_number, event, error in parser(file):
                if error is not None:
                    message = f"Файл {file_number} ({path}), строка {line_number}: {error}"
                    if not skip_invalid:
                        raise type(error)(message) from error
                    logger.warning(message)
                    skipped += 1
                    continue

                total += 1
                level = event["level"]
                source = event["source"]
                timestamp = event["timestamp"]
                levels[level] += 1
                if source not in sources:
                    sources[source] = 0
                sources[source] += 1

                if level in ("ERROR", "CRITICAL"):
                    if source not in errors_by_source:
                        errors_by_source[source] = 0
                    errors_by_source[source] += 1
                if first is None or timestamp < first:
                    first = timestamp
                if last is None or timestamp > last:
                    last = timestamp

    top = sorted(errors_by_source.items(), key=error_sort_key)[:5]
    top_sources = []
    for source, count in top:
        top_sources.append({"source": source, "count": count})

    first_timestamp = None
    last_timestamp = None
    if first is not None:
        first_timestamp = first.isoformat()
    if last is not None:
        last_timestamp = last.isoformat()

    return {
        "total_events": total,
        "by_level": levels,
        "by_source": sources,
        "top_5_error_sources": top_sources,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "skipped_lines": skipped,
    }
