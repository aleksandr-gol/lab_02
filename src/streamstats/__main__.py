import argparse
import json
import logging
import sys

from .analysis import analyze
from .errors import ConfigError, StreamStatsError
from .report import save_report


class ArgumentParser(argparse.ArgumentParser):
    # Сообщает об ошибке в аргументах запуска.
    def error(self, message):
        raise ConfigError(message)


# Получает аргументы и запускает анализ файлов.
def main():
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    parser = ArgumentParser(description="Потоковый анализатор событий")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("analyze", help="Посчитать статистику файлов")
    command.add_argument("inputs", nargs="+", help="Входные файлы")
    command.add_argument("--format", required=True, help="csv или jsonl")
    command.add_argument("--output", help="Путь к JSON-отчёту; иначе вывод в консоль")
    command.add_argument("--skip-invalid", action="store_true", help="Пропускать ошибки")

    try:
        args = parser.parse_args()
        report = analyze(args.inputs, args.format, args.skip_invalid)
        if args.output:
            save_report(report, args.output)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
    except (StreamStatsError, OSError, UnicodeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
