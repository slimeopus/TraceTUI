"""Клиентский интерфейс для запуска TraceTUI."""

import argparse
import sys
from pathlib import Path

from .app import TraceTUIApp


def main():
    """Точка входа из CLI."""
    parser = argparse.ArgumentParser(
        description="TraceTUI — Interactive TUI debugger for logs"
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Log files to open",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["auto", "loguru", "logging", "simple"],
        default="auto",
        help="Log format (default: auto-detect)",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Filter by minimum log level",
    )

    args = parser.parse_args()

    # Фильтруем несуществующие файлы
    valid_paths = []
    for file_path in args.files:
        if file_path.exists():
            valid_paths.append(file_path)
        else:
            print(f"File not found: {file_path}", file=sys.stderr)

    app = TraceTUIApp(
        file_paths=valid_paths if valid_paths else None,
        format_type=args.format,
        log_level=args.log_level,
    )

    app.run()


if __name__ == "__main__":
    main()
