import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from streamstats.analysis import analyze
from streamstats.errors import EventError
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import save_report


# Создаёт строку JSONL для тестов.
def event(level="INFO", source="server"):
    row = {
        "timestamp": "2026-10-07T12:00:00+03:00",
        "level": level,
        "source": source,
        "message": "start",
    }
    return json.dumps(row, ensure_ascii=False) + "\n"


# Проверяет чтение JSONL.
def test_jsonl():
    rows = list(parse_jsonl(StringIO(event())))
    number, row, error = rows[0]
    assert number == 1
    assert error is None
    assert row["source"] == "server"
    assert row["timestamp"].isoformat() == "2026-10-07T09:00:00+00:00"


# Проверяет CSV с запятой внутри сообщения.
def test_csv():
    text = 'timestamp,level,source,message\n2026-10-07T12:00:00Z,INFO,api,"hello, world"\n'
    rows = list(parse_csv(StringIO(text)))
    number, row, error = rows[0]
    assert number == 2
    assert error is None
    assert row["message"] == "hello, world"


# Проверяет пустой файл в обоих форматах.
def test_empty(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("", encoding="utf-8")
    for file_format in ("csv", "jsonl"):
        report = analyze([path], file_format)
        assert report["total_events"] == 0
        assert report["first_timestamp"] is None
        assert report["last_timestamp"] is None


# Проверяет остановку на ошибке и пропуск записи.
def test_bad_row(tmp_path, caplog):
    path = tmp_path / "events.txt"
    for file_format in ("csv", "jsonl"):
        if file_format == "jsonl":
            text = event() + "broken\n" + event()
            number = 2
        else:
            good = "2026-10-07T12:00:00Z,INFO,api,ok\n"
            text = "timestamp,level,source,message\n" + good + "broken\n" + good
            number = 3
        path.write_text(text, encoding="utf-8")
        with pytest.raises(EventError, match=f"строка {number}"):
            analyze([path], file_format)
        caplog.clear()
        report = analyze([path], file_format, skip_invalid=True)
        assert report["total_events"] == 2
        assert report["skipped_lines"] == 1
        assert "WARNING" in caplog.text
        assert str(path) in caplog.text


# Проверяет общую статистику двух файлов.
def test_files(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text(event("ERROR", "db"), encoding="utf-8")
    b.write_text(event("CRITICAL", "db") + event(), encoding="utf-8")
    report = analyze([a, b], "jsonl")
    assert report["total_events"] == 3
    assert report["by_level"] == {
        "DEBUG": 0, "INFO": 1, "WARNING": 0, "ERROR": 1, "CRITICAL": 1,
    }
    assert report["by_source"] == {"db": 2, "server": 1}
    assert report["top_5_error_sources"] == [{"source": "db", "count": 2}]


# Проверяет кириллицу во входном файле и отчёте.
def test_unicode(tmp_path):
    path = tmp_path / "события.jsonl"
    path.write_text(event(source="сервер"), encoding="utf-8")
    report = analyze([path], "jsonl")
    assert report["by_source"] == {"сервер": 1}
    output = tmp_path / "отчёт.json"
    save_report(report, output)
    assert "сервер" in output.read_text(encoding="utf-8")


# Запускает CLI во временной папке.
def test_cli(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(event(), encoding="utf-8")
    output = tmp_path / "report.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    command = [sys.executable, "-m", "streamstats", "analyze", str(path),
               "--format", "jsonl", "--output", str(output)]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["total_events"] == 1

    path.write_text("broken\n", encoding="utf-8")
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert result.returncode == 2
    assert "строка 1" in result.stderr
