import json
from pathlib import Path


# Сохраняет отчёт в JSON-файл.
def save_report(report, path):
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False)
