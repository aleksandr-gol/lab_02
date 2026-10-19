# Лабораторная 2

Программа читает CSV или JSONL и считает статистику событий.
Сделана обязательная часть задания, без дополнительных заданий.
Нужен Python 3.11 или новее.

## Установка и запуск

Открыть терминал в папке lab_02:
```powershell
python -m pip install -e ".[dev]"
python -m streamstats analyze events.jsonl --format jsonl --output report.json
python -m streamstats analyze events.csv --format csv --output report.json
```
Можно указать несколько входных файлов одного формата через пробел.
Без `--output` отчёт выводится в терминал.
С `--skip-invalid` неверные записи пропускаются с предупреждением.
Для отчёта нужно указывать отдельный файл: существующий файл перезаписывается.

## Файлы программы

- `errors.py` — классы ошибок
- `models.py` — проверка события и преобразование времени
- `parsers.py` — чтение CSV и JSONL
- `analysis.py` — подсчёт статистики
- `report.py` — сохранение JSON
- `__main__.py` — запуск из терминала

## Проверка

```powershell
python -m pytest
ruff check .
python -m streamstats --help
```
